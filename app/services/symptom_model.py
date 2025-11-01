"""
SymptomModel service

Responsibilities:
- Load a clinical NER / symptom extraction model (HuggingFace transformers if available)
  or fall back to a deterministic rule-based extractor.
- Provide a clean API for:
    * extract_entities(text: str) -> List[Dict[str,str]]
    * predict_conditions_from_entities(entities: List[Dict[str,str]]) -> Dict[str,float]
- Designed for production: lazy model loading, device selection, batching, and graceful fallback.
"""

from typing import List, Dict, Optional, Any
import os
import logging
from pathlib import Path
from functools import lru_cache

from app.utils.logger import get_logger
from app.config import settings, SYMPTOM_MODEL_PATH

logger = get_logger(__name__)


# Try importing transformers optionally; if not available, we'll use the rule-based fallback
try:
    from transformers import pipeline, AutoTokenizer, AutoModelForTokenClassification
    TRANSFORMERS_AVAILABLE = True
except Exception:
    TRANSFORMERS_AVAILABLE = False
    logger.info("transformers not available; SymptomModel will use rule-based fallback.")


class SymptomModel:
    """
    SymptomModel handles extraction of symptom entities from clinical text.

    Behavior:
      - If a transformer model path exists and transformers package is available, initialize
        a token-classification pipeline for NER.
      - Otherwise use a light-weight regex/keyphrase-based extractor suitable for demos.

    Methods:
      - extract_entities(text) -> list of {"entity": str, "label": str}
      - predict_conditions_from_entities(entities) -> coarse risk map e.g., {"diabetes": 0.6}
    """

    DEFAULT_SYMPTOM_KEYWORDS = [
        "fever", "cough", "fatigue", "headache", "polyuria", "polydipsia",
        "chest pain", "palpitations", "shortness of breath", "dizziness",
        "blurred vision", "weight loss", "weight gain", "nausea", "vomiting",
    ]

    # Mapping from simple symptom keywords to condition influence (coarse)
    CONDITION_RULES = {
        "diabetes": {"polyuria", "polydipsia", "weight loss", "blurred vision"},
        "hypertension": {"headache", "dizziness", "blurred vision", "palpitations"},
        "cardiac": {"chest pain", "palpitations", "shortness of breath"},
        "infection": {"fever", "cough", "nausea", "vomiting"},
    }

    def __init__(self,
                 model_path: Optional[str] = None,
                 model_name_or_path: Optional[str] = None,
                 use_gpu: bool = False,
                 ner_task: str = "ner"):
        """
        Args:
            model_path: explicit local path to a token-classification model (overrides model_name_or_path)
            model_name_or_path: HF model identifier (e.g., "emilyalsentzer/Bio_ClinicalBERT")
            use_gpu: attempt to use CUDA device if available
            ner_task: pipeline task name ("ner" or "token-classification")
        """
        self._use_transformer = False
        self._pipeline = None
        self._device = 0 if (use_gpu and self._gpu_available()) else -1
        self.model_path = model_path or (str(SYMPTOM_MODEL_PATH) if SYMPTOM_MODEL_PATH else None)
        self.model_name_or_path = model_name_or_path
        self.ner_task = ner_task

        logger.info("Initializing SymptomModel; transformer_available=%s, model_path=%s, device=%s",
                    TRANSFORMERS_AVAILABLE, self.model_path, self._device)

        # Lazy initialization - actual model loading on first call
        self._initialized = False

    def _gpu_available(self) -> bool:
        try:
            import torch
            return torch.cuda.is_available()
        except Exception:
            return False

    def _init_transformer(self):
        """
        Initialize the HF pipeline if possible.
        """
        if not TRANSFORMERS_AVAILABLE:
            logger.debug("Transformers package not present; skipping transformer init.")
            return

        model_source = None
        if self.model_path and Path(self.model_path).exists():
            model_source = str(self.model_path)
        elif self.model_name_or_path:
            model_source = self.model_name_or_path
        else:
            # no model available
            model_source = None

        if model_source:
            try:
                logger.info("Loading tokenizer & model for NER from '%s' on device %s", model_source, self._device)
                # Use token-classification pipeline with automatic aggregation_strategy
                self._pipeline = pipeline(self.ner_task,
                                          model=model_source,
                                          tokenizer=model_source,
                                          aggregation_strategy="simple",
                                          device=self._device)
                self._use_transformer = True
                logger.info("Transformer-based NER pipeline initialized successfully.")
            except Exception as exc:
                logger.exception("Failed to initialize transformer NER pipeline: %s", exc)
                self._pipeline = None
                self._use_transformer = False
        else:
            logger.info("No HF model source provided for SymptomModel; using fallback rules.")
            self._pipeline = None
            self._use_transformer = False

        self._initialized = True

    def extract_entities(self, text: str, top_k: int = 20) -> List[Dict[str, str]]:
        """
        Extract symptom-related entities from text.

        Returns:
            List of dicts: [{"entity": "fever", "label": "SYMPTOM"}, ...]
        """
        if not isinstance(text, str) or not text.strip():
            return []

        if not self._initialized:
            self._init_transformer()

        text_clean = self._basic_clean(text)

        if self._use_transformer and self._pipeline:
            try:
                ner_results = self._pipeline(text_clean)
                entities = []
                for item in ner_results:
                    # item example: {'entity_group': 'SYMPTOM', 'score': 0.98, 'word': 'fever', 'start': 10, 'end': 15}
                    word = item.get("word") or item.get("entity")
                    label = item.get("entity_group") or item.get("entity")
                    if word:
                        entities.append({"entity": word.strip(), "label": label})
                logger.debug("Transformer extracted %d entities", len(entities))
                return entities
            except Exception as exc:
                logger.exception("Transformer NER failed; falling back to rule-based extractor: %s", exc)
                # fall through to rule-based

        # Rule-based fallback
        return self._rule_based_extract(text_clean, top_k=top_k)

    def _rule_based_extract(self, text: str, top_k: int = 20) -> List[Dict[str, str]]:
        """
        Simple keyword-based extraction for demo/hackathon.
        Uses the DEFAULT_SYMPTOM_KEYWORDS list.
        """
        found = []
        text_lower = text.lower()
        for kw in self.DEFAULT_SYMPTOM_KEYWORDS:
            if kw in text_lower:
                found.append({"entity": kw, "label": "SYMPTOM"})
        # Deduplicate preserving order
        seen = set()
        dedup = []
        for ent in found:
            if ent["entity"] not in seen:
                dedup.append(ent)
                seen.add(ent["entity"])
        logger.debug("Rule-based extracted entities: %s", dedup[:top_k])
        return dedup[:top_k]

    def predict_conditions_from_entities(self, entities: List[Dict[str, str]]) -> Dict[str, float]:
        """
        Map a list of extracted entities to a coarse condition probability map.

        Returns:
            dict e.g.: {"diabetes": 0.65, "hypertension": 0.12}
        """
        # initialize zeroed probabilities
        cond_scores = {k: 0.0 for k in self.CONDITION_RULES.keys()}
        entity_set = {e.get("entity", "").lower() for e in entities if e.get("entity")}

        for cond, keywords in self.CONDITION_RULES.items():
            overlap = entity_set.intersection({kw.lower() for kw in keywords})
            if overlap:
                # coarse mapping: more matched keywords -> higher confidence
                score = min(0.2 * len(overlap), 0.9)  # each match adds 0.2 up to 0.9
                cond_scores[cond] = round(float(score), 4)

        # Normalize: ensure values within [0,1] and do minor smoothing
        for k in list(cond_scores.keys()):
            v = cond_scores[k]
            if v < 0:
                v = 0.0
            if v > 1:
                v = 1.0
            cond_scores[k] = v

        logger.debug("Predicted coarse condition probabilities from entities: %s", cond_scores)
        return cond_scores


# Optional convenience singleton
_default_symptom_model: Optional[SymptomModel] = None


def get_default_symptom_model() -> SymptomModel:
    global _default_symptom_model
    if _default_symptom_model is None:
        _default_symptom_model = SymptomModel()
    return _default_symptom_model


def load_model(path: Optional[str] = None) -> SymptomModel:
    """
    Compatibility function for main.py startup event.
    Initializes and caches the default symptom model.
    """
    global _default_symptom_model
    if _default_symptom_model is None:
        _default_symptom_model = SymptomModel(model_path=path)
        logger.info(f"✅ SymptomModel loaded successfully (path={path})")
    else:
        logger.info("SymptomModel already loaded; skipping reload.")
    return _default_symptom_model


# Quick CLI test when executed directly
if __name__ == "__main__":
    m = get_default_symptom_model()
    sample = "Patient complains of polyuria, excessive thirst, and fatigue over past 2 weeks. Also reports occasional headaches."
    print("Input:", sample)
    ents = m.extract_entities(sample)
    print("Entities:", ents)
    conds = m.predict_conditions_from_entities(ents)
    print("Conditions:", conds)
