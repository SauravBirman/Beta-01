"""
Personalization Engine

Handles patient-specific personalization:
- Manages weights.json and history.csv
- Applies personalization adjustments to predictions
- Supports per-patient fine-tuning or weighting
- Logging and exception handling
"""

import json
import csv
import os
from typing import Dict, List, Optional
from datetime import datetime
from app.utils.logger import log_info, log_debug, log_error, log_exceptions
from app.config import settings

# --------------------------
# Personalization Engine Class
# --------------------------
class PersonalizationEngine:
    def __init__(self, patient_id: str, personalized_dir: str = None):
        self.patient_id = patient_id
        self.personalized_dir = personalized_dir or os.path.join(settings.models_personalized_dir, patient_id)
        self.weights_file = os.path.join(self.personalized_dir, "weights.json")
        self.history_file = os.path.join(self.personalized_dir, "history.csv")

        # Ensure directory exists
        os.makedirs(self.personalized_dir, exist_ok=True)

        # Load existing weights or initialize
        self.weights = self._load_weights()

    @log_exceptions
    def _load_weights(self) -> Dict:
        """Load patient-specific weights from JSON"""
        if os.path.exists(self.weights_file):
            with open(self.weights_file, "r") as f:
                weights = json.load(f)
            log_info("Loaded existing patient weights", patient_id=self.patient_id)
        else:
            weights = {}
            log_info("Initialized new patient weights", patient_id=self.patient_id)
        return weights

    @log_exceptions
    def save_weights(self):
        """Save patient-specific weights to JSON"""
        with open(self.weights_file, "w") as f:
            json.dump(self.weights, f, indent=4)
        log_info("Saved patient weights", patient_id=self.patient_id, weights=self.weights)
# --------------------------
# Extended PersonalizationEngine Features
# --------------------------
class PersonalizationEngine(PersonalizationEngine):  # Extending previous class

    @log_exceptions
    def apply_weights(self, predictions: List[Dict]) -> List[Dict]:
        """
        Apply patient-specific weights to a list of predictions.

        Args:
            predictions (List[Dict]): Predictions from AI services

        Returns:
            List[Dict]: Adjusted predictions
        """
        adjusted_preds = []
        for pred in predictions:
            disease = pred.get("disease")
            prob = pred.get("probability", 0)
            weight = self.weights.get(disease, 1.0)
            adjusted_prob = prob * weight
            adjusted_preds.append({
                "disease": disease,
                "probability": round(adjusted_prob, 4)
            })
            log_debug("Applied personalization weight", disease=disease, original=prob, weight=weight, adjusted=adjusted_prob)
        return adjusted_preds

    @log_exceptions
    def log_history(self, event_type: str, predictions: List[Dict], notes: Optional[str] = None):
        """
        Log patient interaction history to CSV.

        Args:
            event_type (str): Type of event (e.g., 'prediction', 'recommendation')
            predictions (List[Dict]): Predictions or recommendations
            notes (str, optional): Additional notes
        """
        file_exists = os.path.exists(self.history_file)
        with open(self.history_file, "a", newline="") as csvfile:
            fieldnames = ["timestamp", "event_type", "predictions", "notes"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            if not file_exists:
                writer.writeheader()

            writer.writerow({
                "timestamp": datetime.utcnow().isoformat(),
                "event_type": event_type,
                "predictions": json.dumps(predictions),
                "notes": notes or ""
            })
        log_info("Logged patient history", patient_id=self.patient_id, event_type=event_type)

    @log_exceptions
    def update_weight(self, disease: str, weight: float):
        """
        Update or set a patient-specific weight for a disease.

        Args:
            disease (str): Disease name
            weight (float): Weight multiplier
        """
        self.weights[disease] = weight
        self.save_weights()
        log_info("Updated patient weight", patient_id=self.patient_id, disease=disease, weight=weight)

# --------------------------
# Factory function
# --------------------------
def get_personalization_engine(patient_id: str) -> PersonalizationEngine:
    """
    Returns a ready-to-use PersonalizationEngine instance for a patient.
    """
    return PersonalizationEngine(patient_id=patient_id)
