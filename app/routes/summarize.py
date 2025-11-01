from fastapi import APIRouter, HTTPException, UploadFile, Form
from pydantic import BaseModel
from typing import Optional, Dict, Any
import asyncio
import traceback
from datetime import datetime

from app.services.summary_model import SummaryService
from app.utils.logger import get_logger
from app.utils.postprocess import ReportFormatter

logger = get_logger(__name__)
router = APIRouter()

# Initialize services
summary_service = SummaryService()
formatter = ReportFormatter()


# ----------- Request and Response Models -----------

class ReportSummaryRequest(BaseModel):
    patient_id: str
    report_text: str
    report_type: Optional[str] = "general"
    language: Optional[str] = "en"


class ReportSummaryResponse(BaseModel):
    patient_id: str
    generated_at: str
    structured_summary: Dict[str, Any]
    summary_text: str
    ai_confidence: float


# ----------- Route Implementation -----------

@router.post("/summarize-report", response_model=ReportSummaryResponse)
async def summarize_report(request: ReportSummaryRequest):
    """
    Summarize a medical report or prescription using BioBERT-like transformer model.
    Includes structured summary info (keywords, readability, length, etc.)
    """

    try:
        logger.info(f"[Summarization] Processing report for patient_id={request.patient_id}")

        # Step 1: Run the summarization asynchronously
        loop = asyncio.get_event_loop()
        summary_data = await loop.run_in_executor(
            None,
            lambda: summary_service.summarize(
                text=request.report_text,
                report_type=request.report_type,
                language=request.language
            ),
        )

        # Step 2: Postprocess and build structured result
        structured_summary = {
            "report_type": request.report_type,
            "keywords": summary_data.get("keywords", []),
            "readability_score": summary_data.get("readability_score", 0.0),
            "summary_length": len(summary_data.get("summary_text", "").split()),
            "language": request.language,
            "model_version": summary_data.get("model_version"),
        }

        # Step 3: Format text summary for readability
        formatted_summary = formatter.format_symptom_analysis({
            "symptoms_detected": summary_data.get("keywords", []),
            "possible_conditions": summary_data.get("predicted_conditions", []),
        })

        # Step 4: Construct response payload
        response = ReportSummaryResponse(
            patient_id=request.patient_id,
            generated_at=datetime.utcnow().isoformat() + "Z",
            structured_summary=structured_summary,
            summary_text=formatted_summary or summary_data.get("summary_text", ""),
            ai_confidence=float(summary_data.get("confidence", 0.9)),
        )

        logger.info(f"[Summarization] Completed for patient_id={request.patient_id}")
        return response

    except Exception as e:
        error_trace = traceback.format_exc()
        logger.error(f"[SummarizationError] Failed for patient_id={request.patient_id}: {str(e)}")
        logger.debug(error_trace)
        raise HTTPException(status_code=500, detail="Internal error during report summarization.")


# ----------- Example Testing Endpoint -----------

@router.get("/summarize-report/test")
async def test_summary():
    """
    Simple test endpoint for verifying summarization module.
    """
    sample_report = """
    Patient exhibits mild cough and fatigue for 5 days. 
    Lab results show slightly elevated WBC count.
    No chest pain or shortness of breath observed.
    """
    test_request = ReportSummaryRequest(patient_id="test123", report_text=sample_report)
    result = await summarize_report(test_request)
    return result.dict()
