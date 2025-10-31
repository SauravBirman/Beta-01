"""
FastAPI route for summarizing medical reports
Endpoint: /summarize-report
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.services.summary_model import get_summary_service
from app.utils.postprocess import format_summary_output
from app.utils.logger import log_info, log_error, log_exceptions

router = APIRouter()

# --------------------------
# Request schema
# --------------------------
class ReportRequest(BaseModel):
    report_text: str
    max_tokens: Optional[int] = None

# --------------------------
# Response schema
# --------------------------
class ReportResponse(BaseModel):
    summary: str

# --------------------------
# Route: /summarize-report
# --------------------------
@router.post("/summarize-report", response_model=ReportResponse)
@log_exceptions
async def summarize_report(request: ReportRequest):
    """
    Generate summary for a given medical report
    """
    try:
        # Initialize summary service
        summary_service = get_summary_service(max_tokens=request.max_tokens)

        # Generate summary
        summary_raw = summary_service.summarize(request.report_text)

        # Postprocess and format summary
        summary_formatted = format_summary_output(summary_raw, max_length=request.max_tokens)

        log_info("Report summarization completed", summary_preview=summary_formatted[:100])
        return {"summary": summary_formatted}

    except Exception as e:
        log_error("Error in /summarize-report route", exc=e)
        raise HTTPException(status_code=500, detail=str(e))
