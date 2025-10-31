"""
Route: /personalization
Handles patient-specific personalization and model adaptation.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import logging

from app.services.personalization_engine import PersonalizationEngine

router = APIRouter(
    prefix="/personalization",
    tags=["Personalization"]
)

logger = logging.getLogger("ai_module")

# Request schema
class PersonalizationRequest(BaseModel):
    patient_id: str = Field(..., description="Unique patient identifier")
    preferences: Optional[Dict[str, Any]] = Field(
        default=None, description="Optional personalization parameters"
    )


# Response schema
class PersonalizationResponse(BaseModel):
    patient_id: str
    status: str
    message: str = "Personalization updated successfully"


# Initialize personalization engine
personalization_engine = PersonalizationEngine()


@router.post("/", response_model=PersonalizationResponse)
async def personalize_patient(request: PersonalizationRequest):
    """
    Personalize AI models for a specific patient.

    Steps:
        1. Load patient history and current models.
        2. Apply preferences and fine-tune if necessary.
        3. Save updated patient-specific model weights.
    """
    try:
        logger.debug(f"Received personalization request for patient_id={request.patient_id}")

        # Step 1 & 2: Update personalization
        updated = personalization_engine.update_personalization(
            patient_id=request.patient_id,
            preferences=request.preferences
        )
        logger.debug(f"Personalization update result: {updated}")

        return PersonalizationResponse(
            patient_id=request.patient_id,
            status="success"
        )

    except Exception as e:
        logger.exception("Error occurred during patient personalization")
        raise HTTPException(status_code=500, detail=str(e))
