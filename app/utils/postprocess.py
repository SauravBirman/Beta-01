import numpy as np
from typing import Dict, Any, List, Union, Optional
from datetime import datetime

from app.utils.logger import get_logger
from app.services.fusion_layer import FusionLayer, fuse_patient_modalities
  # moved actual fusion logic here

logger = get_logger(__name__)


class ScoreNormalizer:
    """
    Utility to normalize various model scores into a comparable range [0, 1].
    Used for UI presentation or ranking confidence, not for fusion itself.
    """

    def __init__(self, method: str = "minmax"):
        self.method = method

    def normalize(self, scores: Union[List[float], np.ndarray]) -> np.ndarray:
        scores = np.array(scores, dtype=float)

        try:
            if self.method == "minmax":
                min_val, max_val = np.min(scores), np.max(scores)
                if max_val == min_val:
                    return np.zeros_like(scores)
                return (scores - min_val) / (max_val - min_val)

            elif self.method == "softmax":
                exp_scores = np.exp(scores - np.max(scores))
                return exp_scores / exp_scores.sum()

            else:
                logger.warning("Unknown normalization method '%s'. Returning unchanged scores.", self.method)
                return scores

        except Exception as e:
            logger.error("Score normalization failed: %s", str(e))
            return np.zeros_like(scores)


class ReportFormatter:
    """
    Converts AI outputs into readable summaries for both patients and clinicians.
    """

    def format_symptom_analysis(self, analysis: Dict[str, Any]) -> str:
        detected = ", ".join(analysis.get("symptoms_detected", []))
        possible = ", ".join(analysis.get("possible_conditions", []))
        summary = f"Detected symptoms: {detected or 'None'}. Possible causes: {possible or 'Unknown'}."
        return summary.strip()

    def format_risk_summary(self, risk_scores: Dict[str, float]) -> str:
        formatted_lines = [
            f"- {disease.capitalize()}: {round(score * 100, 2)}% risk"
            for disease, score in sorted(risk_scores.items(), key=lambda x: x[1], reverse=True)
        ]
        return "\n".join(formatted_lines) if formatted_lines else "No disease risk detected."

    def format_lifestyle_recommendations(self, recs: Dict[str, List[str]]) -> str:
        output = ["Recommended Lifestyle Adjustments:"]
        for category, tips in recs.items():
            output.append(f"\n{category.capitalize()}:")
            for tip in tips:
                output.append(f"  • {tip}")
        return "\n".join(output) if recs else "No recommendations available."


class DashboardBuilder:
    """
    Builds structured dashboards for frontend consumption.
    Integrates personalization and multimodal context metadata.
    """

    def __init__(self):
        self.formatter = ReportFormatter()
        self.aggregator = FusionLayer()

    def build_patient_dashboard(
        self,
        patient_id: str,
        risks: Dict[str, float],
        recommendations: Dict[str, List[str]],
        summary_text: str,
        personalization_meta: Optional[Dict[str, Any]] = None,
        fusion_sources: Optional[Dict[str, float]] = None,
        blockchain_ref: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create unified JSON output for patient portal.
        """
        try:
            overall_status = self._compute_health_status(risks)
            timestamp = datetime.utcnow().isoformat() + "Z"

            dashboard = {
                "patient_id": patient_id,
                "timestamp": timestamp,
                "overall_health_status": overall_status,
                "disease_risk_summary": self.formatter.format_risk_summary(risks),
                "ai_summary": summary_text,
                "personalized_recommendations": recommendations,
                "fusion_sources": fusion_sources or {},
                "personalization_metadata": personalization_meta or {},
                "blockchain_reference": blockchain_ref,
            }

            logger.info("✅ Patient dashboard generated successfully for %s", patient_id)
            return dashboard

        except Exception as e:
            logger.error("Failed to build patient dashboard: %s", str(e))
            return {"error": str(e)}

    def build_doctor_dashboard(
        self,
        patient_name: str,
        risks: Dict[str, float],
        ai_notes: str,
        alerts: Optional[List[str]] = None,
        lab_summary: Optional[str] = None,
        image_summary: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Doctor view: includes deeper diagnostic insight across modalities.
        """
        try:
            doctor_view = {
                "patient_name": patient_name,
                "generated_at": datetime.utcnow().isoformat() + "Z",
                "aggregated_risks": risks,
                "ai_summary_notes": ai_notes,
                "modality_summaries": {
                    "lab": lab_summary,
                    "image": image_summary,
                },
                "alerts": alerts or self._generate_alerts(risks),
            }

            logger.info("👨‍⚕️ Doctor dashboard created for %s", patient_name)
            return doctor_view

        except Exception as e:
            logger.error("Error while building doctor dashboard for %s: %s", patient_name, str(e))
            return {"error": str(e)}

    def _compute_health_status(self, risks: Dict[str, float]) -> str:
        avg_risk = np.mean(list(risks.values())) if risks else 0.0
        if avg_risk < 0.3:
            return "Healthy"
        elif avg_risk < 0.6:
            return "Moderate Risk"
        else:
            return "High Risk"

    def _generate_alerts(self, risks: Dict[str, float]) -> List[str]:
        return [f"⚠️ High risk of {disease}" for disease, score in risks.items() if score > 0.7]
