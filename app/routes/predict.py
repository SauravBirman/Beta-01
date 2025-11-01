# app/routes/predict.py
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field, model_validator
from typing import Dict, Any, Optional, List
import hashlib
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from app.utils.logger import get_logger
from app.config import settings, DEFAULT_WEIGHTS, MAX_WORKERS, INFERENCE_TIMEOUT_SEC
from app.utils.preprocess import DataPreprocessor
from app.services.disease_model import get_default_disease_model
from app.services.symptom_model import get_default_symptom_model
from app.services.summary_model import get_default_summary_model
from app.services.recommender import Recommender
from app.services.personalization_engine import PersonalizationEngine
from app.services.image_model import get_default_image_model
from app.services.fusion_layer import FusionLayer
from app.utils.postprocess import DashboardBuilder

logger = get_logger(__name__)
router = APIRouter(prefix="/predict", tags=["predict"])

# Threadpool for CPU-bound model calls
_executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)


# --------- Request/Response Schemas ----------
class LabItem(BaseModel):
    name: str
    value: float
    ref_low: Optional[float] = None
    ref_high: Optional[float] = None


class LabPayload(BaseModel):
    patient_id: str
    timestamp: Optional[datetime] = None
    labs: List[LabItem]


class VitalsPoint(BaseModel):
    ts: Optional[datetime]
    hr: Optional[float]
    bp_sys: Optional[float]
    bp_dia: Optional[float]


class VitalsPayload(BaseModel):
    patient_id: str
    vitals: List[VitalsPoint]


class PredictRequest(BaseModel):
    patient_id: str = Field(..., description="Unique patient identifier")
    lab_payload: Optional[LabPayload] = None
    vitals_payload: Optional[VitalsPayload] = None
    note_text: Optional[str] = None
    image_uri: Optional[str] = None
    request_id: Optional[str] = None

    @model_validator(mode="after")
    def ensure_some_input(self):
        if not (self.lab_payload or self.vitals_payload or self.note_text or self.image_uri):
            raise ValueError(
                "At least one of lab_payload, vitals_payload, note_text, or image_uri must be provided"
            )
        return self


class PredictResponse(BaseModel):
    patient_id: str
    inference_id: str
    inference_time: datetime
    risk_scores: Dict[str, float]
    summary: Optional[str]
    preventive_suggestions: List[str]
    explanations: Dict[str, Any]
    dashboard_patient: Dict[str, Any]


# --------- Singletons / clients -------------
_preprocessor = DataPreprocessor()
_disease_model = get_default_disease_model()
_symptom_model = get_default_symptom_model()
_summary_model = get_default_summary_model()
_personalization = PersonalizationEngine()
_image_model = get_default_image_model()
_fusion_layer = FusionLayer(personalization_engine=_personalization)
_recommender = Recommender(personalization_engine=_personalization)
_dashboard_builder = DashboardBuilder()


# --------- Helper utilities -----------------
def _compute_inference_hash(payload: Dict[str, Any]) -> str:
    """Compute SHA256 hash of inference payload for audit logging / blockchain."""
    raw = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _normalize_labs_into_dataframe(lab_payload: LabPayload):
    """Convert LabPayload into DataFrame for preprocessing."""
    import pandas as pd
    if not lab_payload or not lab_payload.labs:
        return None
    row = {item.name: item.value for item in lab_payload.labs}
    return pd.DataFrame([row])


def _vitals_to_frame(vitals_payload: VitalsPayload):
    import pandas as pd
    if not vitals_payload or not vitals_payload.vitals:
        return None
    records = [
        {"ts": v.ts.isoformat() if v.ts else None, "hr": v.hr, "bp_sys": v.bp_sys, "bp_dia": v.bp_dia}
        for v in vitals_payload.vitals
    ]
    return pd.DataFrame(records)


async def _run_in_executor(fn, *args, timeout_sec: int = INFERENCE_TIMEOUT_SEC, **kwargs):
    loop = asyncio.get_event_loop()
    fut = loop.run_in_executor(_executor, lambda: fn(*args, **kwargs))
    try:
        return await asyncio.wait_for(fut, timeout=timeout_sec)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Model inference timed out")
    except Exception as exc:
        logger.exception("Error running function in executor: %s", exc)
        raise HTTPException(status_code=500, detail="Internal inference error")


# --------- Core route logic -----------------
@router.post("/risk", response_model=PredictResponse)
async def predict_risk(request: PredictRequest, background_tasks: BackgroundTasks):
    start_ts = datetime.utcnow()
    logger.info("Received predict request for patient_id=%s request_id=%s", request.patient_id, request.request_id)

    # Preprocess inputs
    lab_df = _normalize_labs_into_dataframe(request.lab_payload) if request.lab_payload else None
    vitals_df = _vitals_to_frame(request.vitals_payload) if request.vitals_payload else None

    preproc_input = {}
    if lab_df is not None:
        preproc_input["lab_results"] = lab_df
    if vitals_df is not None:
        preproc_input["vitals"] = vitals_df
    if request.note_text:
        preproc_input["doctor_notes"] = request.note_text
        preproc_input["symptoms"] = request.note_text

    try:
        processed = await _run_in_executor(_preprocessor.preprocess_patient_data, preproc_input)
    except Exception as exc:
        logger.exception("Preprocessing failed: %s", exc)
        raise HTTPException(status_code=500, detail="Preprocessing error")

    # Prepare tabular features
    tabular_features = {}
    if lab_df is not None:
        tabular_features.update(lab_df.to_dict(orient="records")[0])

    if processed.get("vitals_features") is not None and vitals_df is not None:
        try:
            if "hr" in vitals_df.columns:
                tabular_features["hr_mean"] = float(vitals_df["hr"].dropna().mean())
            if "bp_sys" in vitals_df.columns:
                tabular_features["bp_sys_mean"] = float(vitals_df["bp_sys"].dropna().mean())
        except Exception:
            logger.debug("Vitals aggregation failed")

    # Run models concurrently
    try:
        disease_task = _run_in_executor(_disease_model.predict_proba, tabular_features)
        symptom_task = _run_in_executor(_symptom_model.extract_entities, request.note_text or "")
        summary_task = _run_in_executor(_summary_model.summarize, request.note_text or "")
        disease_probs, symptoms, summary_text = await asyncio.gather(disease_task, symptom_task, summary_task)
    except Exception as exc:
        logger.exception("Model inference error: %s", exc)
        raise HTTPException(status_code=500, detail="Inference error")

    # Personalization
    patient_settings = _personalization.load_patient_settings(request.patient_id)
    weights = _personalization.apply_personalization(DEFAULT_WEIGHTS, request.patient_id)

    try:
        text_condition_probs = _symptom_model.predict_conditions_from_symptoms(symptoms or [])
    except Exception:
        text_condition_probs = {"diabetes": 0.0, "hypertension": 0.0, "cardiac": 0.0}

    # -------- NEW SECTION: Image model + Fusion layer integration --------
    try:
        if request.image_uri:
            image_probs = await _run_in_executor(_image_model.predict_image, request.image_uri)
        else:
            image_probs = {k: 0.0 for k in (disease_probs.keys() if disease_probs else ["diabetes", "hypertension", "cardiac"])}
    except Exception as exc:
        logger.exception("Image model inference failed: %s", exc)
        image_probs = {k: 0.0 for k in (disease_probs.keys() if disease_probs else ["diabetes", "hypertension", "cardiac"])}

    try:
        fused = _fusion_layer.combine_predictions(
            tabular_probs=disease_probs,
            text_probs=text_condition_probs,
            image_probs=image_probs,
            weights=weights
        )
    except Exception as exc:
        logger.exception("Fusion layer failed: %s", exc)
        raise HTTPException(status_code=500, detail="Fusion error")

    # Recommender
    try:
        recommendations_result = _recommender.get_recommendations(
            patient_id=request.patient_id,
            risk_scores=fused,
            symptoms=symptoms,
            profile=patient_settings.get("profile", {})
        )
        suggestions = [r["title"] + ": " + r["text"] for r in recommendations_result.get("recommendations", [])]
    except Exception as exc:
        logger.exception("Recommender failed: %s", exc)
        suggestions = []

    explanations = {
        "tabular": disease_probs,
        "text": text_condition_probs,
        "image": image_probs,
        "weights_used": weights,
        "notes_entities": symptoms,
    }

    dashboard_patient = _dashboard_builder.build_patient_dashboard(
        risks=fused,
        recommendations=recommendations_result.get("recommendations", {}),
        summary_text=summary_text,
        patient_id=request.patient_id
    )

    inference_payload = {
        "patient_id": request.patient_id,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "model_meta": settings.MODEL_METADATA,
        "risk_scores": fused,
        "summary": summary_text,
        "explanations": explanations,
    }
    inference_hash = _compute_inference_hash(inference_payload)

    def _background_log():
        logger.info("Inference logged: patient=%s inference_hash=%s", request.patient_id, inference_hash)
        try:
            audit_path = settings.DATA_DIR / "audit_logs.jsonl"
            with open(audit_path, "a", encoding="utf-8") as f:
                f.write(json.dumps({"inference_hash": inference_hash, "payload": inference_payload}) + "\n")
        except Exception as exc:
            logger.exception("Failed to write audit log: %s", exc)

    background_tasks.add_task(_background_log)

    return {
        "patient_id": request.patient_id,
        "inference_id": inference_hash,
        "inference_time": datetime.utcnow(),
        "risk_scores": fused,
        "summary": summary_text,
        "preventive_suggestions": suggestions,
        "explanations": explanations,
        "dashboard_patient": dashboard_patient,
    }
