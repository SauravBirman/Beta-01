from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio
import traceback

from app.services.disease_model import DiseaseModel
from app.services.recommender import Recommender

from app.services.personalization_engine import PersonalizationEngine
from app.utils.logger import get_logger
from app.utils.postprocess import DashboardBuilder

logger = get_logger(__name__)
router = APIRouter()

# Initialize all backend services
from app.services.disease_model import DiseaseModel

risk_predictor = DiseaseModel()

recommender = Recommender()
personalizer = PersonalizationEngine()
dashboard_builder = DashboardBuilder()


# ------------- Request & Response Models -------------

class RiskPredictionRequest(BaseModel):
    patient_id: str
    demographics: Optional[Dict[str, Any]] = None
    symptoms: Optional[str] = None
    lab_results: Optional[Dict[str, float]] = None
    lifestyle: Optional[Dict[str, Any]] = None
    vitals: Optional[Dict[str, float]] = None
    medical_history: Optional[List[str]] = None
    include_recommendations: bool = True


class RiskPredictionResponse(BaseModel):
    patient_id: str
    generated_at: str
    overall_health_status: str
    disease_risk_summary: Dict[str, float]
    personalized_recommendations: Optional[Dict[str, List[str]]]
    model_version: str


# ------------- Main Predictive Route -------------

@router.post("/predict-risk", response_model=RiskPredictionResponse)
async def predict_risk(request: RiskPredictionRequest):
    """
    Predict potential disease risks (e.g., diabetes, hypertension)
    and generate personalized preventive recommendations.
    """

    try:
        logger.info(f"[Prediction] Processing patient_id={request.patient_id}")

        # Step 1: Async inference to improve responsiveness
        loop = asyncio.get_event_loop()
        raw_risks = await loop.run_in_executor(
            None,
            lambda: risk_predictor.predict(
                symptoms=request.symptoms,
                lab_data=request.lab_results,
                lifestyle=request.lifestyle,
                vitals=request.vitals,
                history=request.medical_history,
            ),
        )

        if not raw_risks:
            raise ValueError("Empty risk prediction returned from model.")

        # Step 2: Apply personalization engine
        personalized_risks = personalizer.apply_personalization(
            patient_id=request.patient_id,
            base_risks=raw_risks,
            lifestyle_data=request.lifestyle,
            vitals=request.vitals,
        )

        # Step 3: Generate preventive recommendations (optional)
        recommendations = None
        if request.include_recommendations:
            recommendations = recommender.generate(
                risks=personalized_risks,
                lifestyle=request.lifestyle,
                demographics=request.demographics,
            )

        # Step 4: Build dashboard output
        dashboard = dashboard_builder.build_patient_dashboard(
            risks=personalized_risks,
            recommendations=recommendations or {},
            summary_text="AI-based risk prediction and preventive guidance.",
            patient_id=request.patient_id,
        )

        response = RiskPredictionResponse(
            patient_id=request.patient_id,
            generated_at=dashboard["timestamp"],
            overall_health_status=dashboard["overall_health_status"],
            disease_risk_summary=personalized_risks,
            personalized_recommendations=recommendations,
            model_version=risk_predictor.model_version,
        )

        logger.info(f"[Prediction] Completed successfully for {request.patient_id}")
        return response

    except Exception as e:
        logger.error(f"[PredictionError] {str(e)} for patient_id={request.patient_id}")
        logger.debug(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Internal error during risk prediction.")


# ------------- Diagnostic Test Endpoint -------------

@router.get("/predict-risk/test")
async def test_predict():
    """
    Simple mock test for the prediction pipeline.
    """
    mock_request = RiskPredictionRequest(
        patient_id="demo123",
        symptoms="fatigue, frequent urination, increased thirst",
        lab_results={"glucose": 180, "cholesterol": 220},
        lifestyle={"smoking": "no", "diet": "high sugar"},
        vitals={"bmi": 28, "bp_sys": 140},
    )

    result = await predict_risk(mock_request)
    return result.dict()
