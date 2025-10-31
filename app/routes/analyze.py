"""
FastAPI route for analyzing patient symptoms
Endpoint: /analyze-symptoms
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import List, Optional

from app.services.symptom_model import get_symptom_service
from app.services.personalization_engine import get_personalization_engine
from app.utils.postprocess import format_symptom_output
from app.utils.logger import log_info, log_error, log_exceptions

router = APIRouter()

# --------------------------
# Request schema
# --------------------------
class SymptomRequest(BaseModel):
    patient_id: str
    symptom_text: str
    top_k: Optional[int] = None

# --------------------------
# Response schema
# --------------------------
class SymptomResponse(BaseModel):
    predictions: List[dict]

# --------------------------
# Route: /analyze-symptoms
# --------------------------
@router.post("/analyze-symptoms", response_model=SymptomResponse)
@log_exceptions
async def analyze_symptoms(request: SymptomRequest):
    """
    Analyze patient symptoms and return top-K probable conditions
    """
    try:
        # Initialize services
        symptom_service = get_symptom_service(top_k=request.top_k)
        personalization_engine = get_personalization_engine(patient_id=request.patient_id)

        # Predict symptoms
        predictions = symptom_service.predict(request.symptom_text)

        # Apply personalization weights
        predictions_adjusted = personalization_engine.apply_weights(predictions)

        # Postprocess and format
        predictions_formatted = format_symptom_output(predictions_adjusted, top_k=request.top_k)

        # Log the event
        personalization_engine.log_history(event_type="symptom_prediction", predictions=predictions_formatted)

        log_info("Symptom analysis completed", patient_id=request.patient_id)
        return {"predictions": predictions_formatted}

    except Exception as e:
        log_error("Error in /analyze-symptoms route", exc=e)
        raise HTTPException(status_code=500, detail=str(e))
