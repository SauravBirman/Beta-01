"""
FastAPI route for predicting disease risk
Endpoint: /predict-risk
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict

from app.services.disease_model import get_disease_service
from app.services.personalization_engine import get_personalization_engine
from app.services.recommender import get_recommender_service
from app.utils.postprocess import format_disease_output
from app.utils.logger import log_info, log_error, log_exceptions

router = APIRouter()

# --------------------------
# Request schema
# --------------------------
class PredictRequest(BaseModel):
    patient_id: str
    symptom_text: str
    top_k: Optional[int] = None
    include_recommendations: Optional[bool] = False

# --------------------------
# Response schema
# --------------------------
class PredictResponse(BaseModel):
    predictions: List[Dict]
    recommendations: Optional[List[Dict]] = None

# --------------------------
# Route: /predict-risk
# --------------------------
@router.post("/predict-risk", response_model=PredictResponse)
@log_exceptions
async def predict_risk(request: PredictRequest):
    """
    Predict disease risk and optionally provide preventive recommendations
    """
    try:
        # Initialize services
        disease_service = get_disease_service(top_k=request.top_k)
        personalization_engine = get_personalization_engine(patient_id=request.patient_id)
        recommender_service = get_recommender_service() if request.include_recommendations else None

        # Predict disease risk
        predictions = disease_service.predict(request.symptom_text)

        # Apply personalization
        predictions_adjusted = personalization_engine.apply_weights(predictions)

        # Postprocess predictions
        predictions_formatted = format_disease_output(predictions_adjusted, top_k=request.top_k)

        # Optionally generate recommendations
        recommendations_formatted = None
        if request.include_recommendations and recommender_service:
            recommendations_formatted = recommender_service.recommend(predictions_adjusted)

        # Log history
        personalization_engine.log_history(
            event_type="disease_prediction",
            predictions=predictions_formatted,
            notes="Recommendations included" if recommendations_formatted else None
        )

        log_info("Disease prediction completed", patient_id=request.patient_id)
        return {
            "predictions": predictions_formatted,
            "recommendations": recommendations_formatted
        }

    except Exception as e:
        log_error("Error in /predict-risk route", exc=e)
        raise HTTPException(status_code=500, detail=str(e))
