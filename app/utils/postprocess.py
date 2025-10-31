"""
Postprocessing utilities for AI Health Assistant

Includes:
- Formatting symptom predictions
- Formatting disease risk predictions
- Formatting report summaries
- Integration with personalization adjustments
- Logging and error handling
"""

from typing import List, Dict, Optional
import numpy as np
from app.utils.logger import log_debug, log_info, log_error, log_exceptions
from app.config import settings

# --------------------------
# Format symptom analysis output
# --------------------------
@log_exceptions
def format_symptom_output(predictions: List[Dict], top_k: Optional[int] = None, personalization_weights: Optional[Dict] = None) -> List[Dict]:
    """
    Format symptom model predictions.

    Args:
        predictions (List[Dict]): Raw predictions from symptom model, e.g., [{"disease": "flu", "probability": 0.85}]
        top_k (Optional[int]): Number of top predictions to keep
        personalization_weights (Optional[Dict]): Patient-specific weighting adjustments

    Returns:
        List[Dict]: Formatted predictions sorted by probability
    """
    if not predictions:
        return []

    # Apply personalization adjustments
    if personalization_weights:
        for pred in predictions:
            weight = personalization_weights.get(pred["disease"], 1.0)
            pred["probability"] *= weight
            log_debug("Applied personalization weight", disease=pred["disease"], original=pred["probability"]/weight, weight=weight, adjusted=pred["probability"])

    # Sort predictions
    predictions_sorted = sorted(predictions, key=lambda x: x["probability"], reverse=True)

    # Keep top-k if specified
    if top_k:
        predictions_sorted = predictions_sorted[:top_k]

    # Round probabilities
    for pred in predictions_sorted:
        pred["probability"] = round(pred["probability"], 4)

    log_info("Symptom predictions formatted", predictions=predictions_sorted)
    return predictions_sorted


# --------------------------
# Format disease risk output
# --------------------------
@log_exceptions
def format_disease_output(risks: List[Dict], top_k: Optional[int] = None, personalization_weights: Optional[Dict] = None) -> List[Dict]:
    """
    Format disease risk predictions.

    Args:
        risks (List[Dict]): Raw risk predictions from disease model
        top_k (Optional[int]): Number of top risks to return
        personalization_weights (Optional[Dict]): Patient-specific weighting adjustments

    Returns:
        List[Dict]: Formatted risks sorted by probability
    """
    if not risks:
        return []

    # Apply personalization adjustments
    if personalization_weights:
        for risk in risks:
            weight = personalization_weights.get(risk["disease"], 1.0)
            risk["probability"] *= weight
            log_debug("Applied personalization weight to risk", disease=risk["disease"], adjusted=risk["probability"])

    # Sort and top-k
    risks_sorted = sorted(risks, key=lambda x: x["probability"], reverse=True)
    if top_k:
        risks_sorted = risks_sorted[:top_k]

    # Round probabilities
    for risk in risks_sorted:
        risk["probability"] = round(risk["probability"], 4)

    log_info("Disease risk predictions formatted", risks=risks_sorted)
    return risks_sorted
# --------------------------
# Format report summaries
# --------------------------
@log_exceptions
def format_summary_output(summary: str, max_length: Optional[int] = None) -> str:
    """
    Format and clean model-generated summaries.

    Args:
        summary (str): Raw summary text
        max_length (Optional[int]): Maximum length of summary (in characters)

    Returns:
        str: Cleaned and optionally truncated summary
    """
    if not summary:
        return ""

    # Remove extra spaces and newlines
    formatted = " ".join(summary.split())

    # Truncate if max_length is specified
    if max_length and len(formatted) > max_length:
        formatted = formatted[:max_length].rstrip()
        log_debug("Summary truncated to max_length", max_length=max_length, summary=formatted)

    log_info("Summary formatted", summary=formatted)
    return formatted


# --------------------------
# Full pipeline for predictions
# --------------------------
@log_exceptions
def postprocess_pipeline(
    predictions: List[Dict],
    summary: Optional[str] = None,
    top_k: Optional[int] = None,
    personalization_weights: Optional[Dict] = None
) -> Dict:
    """
    Full postprocessing pipeline:
    - Format symptom/disease predictions
    - Format summary
    - Apply personalization weights

    Args:
        predictions (List[Dict]): Raw symptom or risk predictions
        summary (Optional[str]): Raw report summary
        top_k (Optional[int]): Top-K selection for predictions
        personalization_weights (Optional[Dict]): Patient-specific adjustments

    Returns:
        Dict: {
            "predictions": formatted predictions,
            "summary": formatted summary
        }
    """
    formatted_predictions = format_symptom_output(
        predictions, top_k=top_k, personalization_weights=personalization_weights
    )

    formatted_summary = None
    if summary:
        formatted_summary = format_summary_output(summary, max_length=settings.summary_max_tokens)

    log_info("Postprocessing pipeline completed", predictions=formatted_predictions, summary=formatted_summary)
    return {
        "predictions": formatted_predictions,
        "summary": formatted_summary
    }
