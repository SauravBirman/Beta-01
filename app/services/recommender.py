"""
Preventive Care Recommender

Provides personalized preventive care recommendations based on:
- Disease risk predictions
- Patient-specific preferences and history
- Top-K actionable recommendations
- Logging and exception handling
"""

from typing import List, Dict, Optional
from app.utils.logger import log_info, log_debug, log_error, log_exceptions
from app.config import settings

# --------------------------
# Default preventive actions mapping
# --------------------------
DEFAULT_PREVENTIVE_ACTIONS = {
    "hypertension": ["Reduce salt intake", "Regular blood pressure monitoring", "Exercise regularly"],
    "diabetes": ["Monitor blood sugar", "Balanced diet", "Regular physical activity"],
    "flu": ["Annual flu vaccine", "Hand hygiene", "Avoid crowded places"],
    "covid": ["Vaccination booster", "Mask in public", "Social distancing"],
    "obesity": ["Healthy diet", "Regular exercise", "Consult nutritionist"]
    # Add more mappings as needed
}

# --------------------------
# Recommender Service
# --------------------------
class RecommenderService:
    def __init__(self, preventive_actions: Dict[str, List[str]] = None, top_k: int = None):
        self.preventive_actions = preventive_actions or DEFAULT_PREVENTIVE_ACTIONS
        self.top_k = top_k or settings.recommender_top_k

    @log_exceptions
    def recommend(
        self,
        disease_predictions: List[Dict],
        personalization_weights: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Generate preventive care recommendations based on disease predictions.

        Args:
            disease_predictions (List[Dict]): List of disease predictions with probabilities
            personalization_weights (Dict, optional): Patient-specific adjustments for recommendation priority

        Returns:
            List[Dict]: List of top-K recommended actions per disease
        """
        if not disease_predictions:
            return []

        recommendations = []
        for pred in disease_predictions:
            disease = pred.get("disease")
            prob = pred.get("probability", 0)

            # Skip if probability is very low
            if prob < 0.05:
                continue

            # Base recommendations
            actions = self.preventive_actions.get(disease, [])

            # Apply personalization weights
            if personalization_weights:
                weight = personalization_weights.get(disease, 1.0)
                adjusted_prob = prob * weight
            else:
                adjusted_prob = prob

            recommendations.append({
                "disease": disease,
                "probability": round(adjusted_prob, 4),
                "actions": actions[:self.top_k]
            })

            log_debug("Recommendation generated", disease=disease, probability=adjusted_prob, actions=actions[:self.top_k])

        # Sort by adjusted probability descending
        recommendations_sorted = sorted(recommendations, key=lambda x: x["probability"], reverse=True)
        log_info("Recommendations completed", recommendations=recommendations_sorted)
        return recommendations_sorted
# --------------------------
# Extended RecommenderService Features
# --------------------------
class RecommenderService(RecommenderService):  # Extending previous class
    @log_exceptions
    def recommend_batch(
        self,
        batch_predictions: List[List[Dict]],
        personalization_weights_list: Optional[List[Dict]] = None
    ) -> List[List[Dict]]:
        """
        Generate recommendations for a batch of patients.

        Args:
            batch_predictions (List[List[Dict]]): List of disease predictions per patient
            personalization_weights_list (Optional[List[Dict]]): List of patient-specific weights

        Returns:
            List[List[Dict]]: Batch of recommendations
        """
        batch_recommendations = []
        for idx, predictions in enumerate(batch_predictions):
            personalization_weights = None
            if personalization_weights_list:
                personalization_weights = personalization_weights_list[idx]
            recs = self.recommend(predictions, personalization_weights=personalization_weights)
            batch_recommendations.append(recs)
            log_debug("Batch recommendation processed", patient_index=idx, recommendations=recs)
        log_info("Batch preventive recommendations completed", batch_size=len(batch_predictions))
        return batch_recommendations

# --------------------------
# Factory function
# --------------------------
def get_recommender_service(preventive_actions: dict = None, top_k: int = None) -> RecommenderService:
    """
    Returns a ready-to-use RecommenderService instance.
    """
    return RecommenderService(preventive_actions=preventive_actions, top_k=top_k)
