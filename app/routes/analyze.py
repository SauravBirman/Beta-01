# app/routes/analyze.py
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import json
import hashlib

from app.utils.logger import get_logger
from app.config import settings, MAX_WORKERS, INFERENCE_TIMEOUT_SEC
from app.utils.preprocess import DataPreprocessor
from app.services.symptom_model import get_default_symptom_model
from app.utils.postprocess import ReportFormatter, DashboardBuilder

logger = get_logger(__name__)
router = APIRouter(prefix="/analyze", tags=["symptom-analysis"])

# Threadpool shared with predict router to keep behavior consistent
_executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)
_preprocessor = DataPreprocessor()
_symptom_model = get_default_symptom_model()
_formatter = ReportFormatter()
_dashboard_builder = DashboardBuilder()


# ---- Request / Response models ----
class AnalyzeRequest(BaseModel):
    patient_id: str = Field(..., description="Unique patient identifier")
    report_text: Optional[str] = Field(None, description="Free-text clinical note or symptom description")
    request_id: Optional[str] = Field(None, description="Optional client request id for tracing")


class EntityOut(BaseModel):
    entity: str
    label: str


class AnalyzeResponse(BaseModel):
    patient_id: str
    request_id: Optional[str]
    timestamp: datetime
    extracted_entities: List[EntityOut]
    probable_conditions: Dict[str, float]
    summary: Optional[str]
    explanation: Dict[str, Any]


# ---- Helpers ----
def _compute_hash(obj: Dict[str, Any]) -> str:
    raw = json.dumps(obj, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


async def _run_in_executor(fn, *args, timeout_sec: int = INFERENCE_TIMEOUT_SEC, **kwargs):
    loop = asyncio.get_event_loop()
    fut = loop.run_in_executor(_executor, lambda: fn(*args, **kwargs))
    try:
        return await asyncio.wait_for(fut, timeout=timeout_sec)
    except asyncio.TimeoutError:
        logger.error("Executor task timed out")
        raise HTTPException(status_code=504, detail="Symptom analysis timed out")
    except Exception as exc:
        logger.exception("Executor task failed: %s", exc)
        raise HTTPException(status_code=500, detail="Internal symptom analysis error")


# ---- Route Implementations ----
@router.post("/symptoms", response_model=AnalyzeResponse)
async def analyze_symptoms(req: AnalyzeRequest, background_tasks: BackgroundTasks):
    """
    Extract symptoms/entities from clinical text and provide coarse probable conditions.
    Also returns a short extractive summary of the input text.
    """
    if not req.report_text or not req.report_text.strip():
        raise HTTPException(status_code=400, detail="report_text is required")

    logger.info("Analyze request received: patient=%s request_id=%s", req.patient_id, req.request_id)

    # Preprocess text (lightweight)
    try:
        processed = await _run_in_executor(_preprocessor.text_processor.clean_text, req.report_text)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Text preprocessing failed: %s", exc)
        raise HTTPException(status_code=500, detail="Preprocessing failed")

    # Run NER / extraction and summary in parallel
    try:
        ner_task = _run_in_executor(_symptom_model.extract_entities, req.report_text)
        condition_task = None  # we'll call predict_conditions_from_entities after ner
        summary_task = _run_in_executor(lambda t: _formatter.format_symptom_analysis({"symptoms_detected": [], "possible_conditions": []}), req.report_text)
        # run ner first then map to conditions
        ents = await ner_task
        # Map to probable conditions using model helper
        conds = await _run_in_executor(_symptom_model.predict_conditions_from_symptoms, ents)
        # Create a small summary (prefer summary_model if available via summarizer service)
        # For speed, create a short sentence summarizing top entities
        if ents:
            entities_list = [e.get("entity") for e in ents]
            summary_text = "Detected: " + ", ".join(entities_list) + "."
        else:
            summary_text = "No clear symptom entities detected."
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Symptom model failed: %s", exc)
        raise HTTPException(status_code=500, detail="Symptom extraction failed")

    # Prepare explanation & audit hash
    explanation = {
        "entities": ents,
        "condition_probs": conds
    }

    inference_payload = {
        "patient_id": req.patient_id,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "report_text_hash": _compute_hash({"text": req.report_text}),
        "explanation": explanation
    }
    inference_hash = _compute_hash(inference_payload)

    # Background logging (local audit file). Replace with blockchain adapter later.
    def _bg_log():
        try:
            audit_path = settings.DATA_DIR / "analyze_audit.jsonl"
            with open(audit_path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps({"inference_hash": inference_hash, "payload": inference_payload}) + "\n")
            logger.info("Analyze audit written for patient=%s hash=%s", req.patient_id, inference_hash)
        except Exception as exc:
            logger.exception("Failed to write analyze audit: %s", exc)

    background_tasks.add_task(_bg_log)

    # Build response
    resp = AnalyzeResponse(
        patient_id=req.patient_id,
        request_id=req.request_id,
        timestamp=datetime.utcnow(),
        extracted_entities=[EntityOut(**e) for e in ents],
        probable_conditions=conds,
        summary=summary_text,
        explanation=explanation
    )

    logger.info("Analyze completed: patient=%s request_id=%s hash=%s", req.patient_id, req.request_id, inference_hash)
    return resp
