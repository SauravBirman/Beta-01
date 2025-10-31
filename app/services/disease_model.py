"""
Disease Model Service

Provides AI functionality for predicting disease risk:
- Loads pretrained model (scikit-learn or PyTorch)
- Converts symptom vectors into risk probabilities
- Returns top-K probable diseases
- Supports personalization adjustments
- Full logging and exception handling
"""

import pickle
from typing import List, Dict, Optional
import numpy as np
import torch

from app.utils.preprocess import preprocess_pipeline
from app.utils.logger import log_info, log_debug, log_error, log_exceptions
from app.config import settings

# --------------------------
# DiseaseModelService Class
# --------------------------
class DiseaseModelService:
    def __init__(self, model_path: str = None, top_k: int = None, device: str = None):
        self.model_path = model_path or str(settings.disease_model_path)
        self.top_k = top_k or settings.disease_top_k
        self.device = device or settings.device

        self.model = None
        self._load_model()

    @log_exceptions
    def _load_model(self):
        """Load pretrained disease risk model (pickle or PyTorch)"""
        try:
            if self.model_path.endswith(".pkl"):
                with open(self.model_path, "rb") as f:
                    self.model = pickle.load(f)
                log_info("Disease model loaded (pickle)", model_path=self.model_path)
            elif self.model_path.endswith(".pt"):
                self.model = torch.load(self.model_path, map_location=self.device)
                self.model.eval()
                log_info("Disease model loaded (PyTorch)", model_path=self.model_path, device=self.device)
            else:
                raise ValueError("Unsupported model format. Use .pkl or .pt")
        except Exception as e:
            log_error("Failed to load disease model", exc=e)
            raise RuntimeError(f"Could not load disease model from {self.model_path}") from e

    @log_exceptions
    def predict(self, symptom_text: str, embedding_model: Optional[object] = None,
                personalization_weights: Optional[Dict] = None) -> List[Dict]:
        """
        Predict disease risk from patient symptom text.

        Args:
            symptom_text (str): Raw patient symptom description
            embedding_model (object, optional): Pretrained embedding model
            personalization_weights (dict, optional): Patient-specific weighting adjustments

        Returns:
            List[Dict]: Top-K disease predictions with probabilities
        """
        # Preprocess symptom text
        vector = preprocess_pipeline(symptom_text, embedding_model=embedding_model)

        # Convert to appropriate format
        if isinstance(self.model, torch.nn.Module):
            input_tensor = torch.tensor(vector, dtype=torch.float32).unsqueeze(0).to(self.device)
            with torch.no_grad():
                logits = self.model(input_tensor)
                probs = torch.softmax(logits, dim=1).cpu().numpy()[0]
        else:  # scikit-learn model
            probs = self.model.predict_proba([vector])[0]

        # Map class labels
        class_labels = getattr(self.model, "classes_", [f"disease_{i}" for i in range(len(probs))])
        predictions = [{"disease": label, "probability": float(prob)} for label, prob in zip(class_labels, probs)]

        # Apply personalization weights
        if personalization_weights:
            for pred in predictions:
                weight = personalization_weights.get(pred["disease"], 1.0)
                pred["probability"] *= weight

        # Sort and select top-K
        predictions_sorted = sorted(predictions, key=lambda x: x["probability"], reverse=True)[:self.top_k]
        log_info("Disease prediction completed", predictions=predictions_sorted)
        return predictions_sorted
# --------------------------
# Extended DiseaseModelService Features
# --------------------------

    @log_exceptions
    def predict_batch(
        self,
        symptom_texts: List[str],
        embedding_model: Optional[object] = None,
        personalization_weights: Optional[Dict] = None
    ) -> List[List[Dict]]:
        """
        Predict disease risk for a batch of symptom texts.

        Args:
            symptom_texts (List[str]): List of raw symptom descriptions
            embedding_model (object, optional): Pretrained embedding model
            personalization_weights (dict, optional): Patient-specific weighting adjustments

        Returns:
            List[List[Dict]]: List of top-K predictions for each input
        """
        batch_results = []
        for text in symptom_texts:
            preds = self.predict(text, embedding_model=embedding_model, personalization_weights=personalization_weights)
            batch_results.append(preds)
            log_debug("Batch prediction processed for input", text=text, predictions=preds)
        log_info("Batch disease predictions completed", batch_size=len(symptom_texts))
        return batch_results

    @log_exceptions
    def update_model(self, new_model_path: str):
        """
        Update the service to use a new pretrained model.

        Args:
            new_model_path (str): Path to new model
        """
        self.model_path = new_model_path
        self._load_model()
        log_info("Disease model updated", new_model_path=new_model_path)

# --------------------------
# Factory function
# --------------------------
def get_disease_service(model_path: str = None, top_k: int = None, device: str = None) -> DiseaseModelService:
    """
    Returns a ready-to-use DiseaseModelService instance.
    """
    return DiseaseModelService(model_path=model_path, top_k=top_k, device=device)
