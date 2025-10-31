"""
Symptom Model Service

Provides AI functionality for analyzing patient symptoms:
- Loads pretrained PyTorch model
- Converts symptom text to embeddings
- Returns top-K probable conditions
"""

import torch
import torch.nn.functional as F
from typing import List, Dict
import numpy as np

from app.utils.preprocess import preprocess_pipeline
from app.utils.logger import log_info, log_debug, log_error, log_exceptions
from app.config import settings

# --------------------------
# SymptomModelService Class
# --------------------------
class SymptomModelService:
    def __init__(self, model_path: str = None, device: str = None, top_k: int = None):
        self.model_path = model_path or settings.symptom_model_path
        self.device = device or settings.device
        self.top_k = top_k or settings.symptom_top_k

        self.model = None
        self._load_model()

    @log_exceptions
    def _load_model(self):
        """Load pretrained PyTorch symptom model"""
        try:
            self.model = torch.load(self.model_path, map_location=self.device)
            self.model.eval()
            log_info("Symptom model loaded successfully", model_path=str(self.model_path), device=self.device)
        except Exception as e:
            log_error("Failed to load symptom model", exc=e)
            raise RuntimeError(f"Could not load symptom model from {self.model_path}") from e

    @log_exceptions
    def predict(self, symptom_text: str, embedding_model: object = None) -> List[Dict]:
        """
        Predict probable conditions from symptom text.

        Args:
            symptom_text (str): Raw patient symptom description
            embedding_model (object, optional): Pretrained embedding model for vectorization

        Returns:
            List[Dict]: Top-K predicted conditions with probabilities
        """
        # Preprocess symptom text to vector
        vector = preprocess_pipeline(symptom_text, embedding_model=embedding_model)

        # Convert to torch tensor
        input_tensor = torch.tensor(vector, dtype=torch.float32).unsqueeze(0).to(self.device)
        log_debug("Input tensor created", shape=input_tensor.shape)

        # Model inference
        with torch.no_grad():
            logits = self.model(input_tensor)
            probabilities = F.softmax(logits, dim=1).cpu().numpy()[0]

        # Map to class labels
        class_labels = getattr(self.model, "classes", [f"condition_{i}" for i in range(len(probabilities))])
        predictions = [{"disease": label, "probability": float(prob)} for label, prob in zip(class_labels, probabilities)]

        # Sort top-K
        predictions_sorted = sorted(predictions, key=lambda x: x["probability"], reverse=True)[:self.top_k]
        log_info("Symptom prediction completed", predictions=predictions_sorted)
        return predictions_sorted
# --------------------------
# Extended SymptomModelService Features
# --------------------------

    @log_exceptions
    def predict_batch(self, symptom_texts: List[str], embedding_model: object = None, personalization_weights: dict = None) -> List[List[Dict]]:
        """
        Predict probable conditions for a batch of symptom texts.

        Args:
            symptom_texts (List[str]): List of raw symptom descriptions
            embedding_model (object, optional): Pretrained embedding model
            personalization_weights (dict, optional): Patient-specific weighting adjustments

        Returns:
            List[List[Dict]]: List of top-K predictions for each input
        """
        batch_predictions = []
        for text in symptom_texts:
            preds = self.predict(text, embedding_model=embedding_model)

            # Apply personalization weights if provided
            if personalization_weights:
                for pred in preds:
                    weight = personalization_weights.get(pred["disease"], 1.0)
                    pred["probability"] *= weight

                # Re-sort after weighting
                preds = sorted(preds, key=lambda x: x["probability"], reverse=True)[:self.top_k]

            batch_predictions.append(preds)
            log_debug("Batch prediction processed for input", text=text, predictions=preds)
        log_info("Batch symptom predictions completed", batch_size=len(symptom_texts))
        return batch_predictions

    @log_exceptions
    def update_model(self, new_model_path: str):
        """
        Update the service to use a new pretrained model.

        Args:
            new_model_path (str): Path to new PyTorch model
        """
        self.model_path = new_model_path
        self._load_model()
        log_info("Symptom model updated to new path", new_model_path=new_model_path)

# --------------------------
# Factory function
# --------------------------
def get_symptom_service(model_path: str = None, device: str = None, top_k: int = None) -> SymptomModelService:
    """
    Returns a ready-to-use SymptomModelService instance.
    """
    return SymptomModelService(model_path=model_path, device=device, top_k=top_k)
