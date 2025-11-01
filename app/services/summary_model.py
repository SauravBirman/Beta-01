"""
SummaryModel service

Responsibilities:
- Provide clinical report summarization.
- Prefer abstractive summarization via HuggingFace transformers (e.g., T5/BART variants) if available.
- Fall back to extractive summarization (sentence scoring) when transformer or models are unavailable.
- Support batching, device selection (CPU/GPU), lazy initialization, and safe truncation for very long inputs.
"""

from typing import Optional, List
import logging
import math
import textwrap
import time
from functools import lru_cache

from app.utils.logger import get_logger
from app.config import settings, SUMMARY_MODEL_PATH

logger = get_logger(__name__)

# optional imports
try:
    from transformers import (
        AutoTokenizer,
        AutoModelForSeq2SeqLM,
        pipeline,
        Pipeline,
        PreTrainedTokenizer,
    )
    TRANSFORMERS_AVAILABLE = True
except Exception:
    TRANSFORMERS_AVAILABLE = False
    logger.info("transformers not available — SummaryModel will use extractive fallback.")


class SummaryModel:
    """
    Wrapper around a summarization model.

    - If a HF seq2seq model is available at SUMMARY_MODEL_PATH or specified by name, use it.
    - Otherwise use an extractive summarizer that picks top sentences by keyword score.
    """

    # default abstractive model name (can be overridden by passing model_name_or_path)
    DEFAULT_MODEL_NAME = "sshleifer/distilbart-cnn-12-6"  # compact summarizer; replace with clinical T5 if available

    def __init__(self,
                 model_name_or_path: Optional[str] = None,
                 device: Optional[int] = None,
                 max_input_tokens: int = 4096,
                 max_summary_length: int = 256):
        """
        Args:
            model_name_or_path: path to local HF model or model id (overrides default)
            device: int device id for HF pipeline (None => auto CPU or CUDA if available)
            max_input_tokens: maximum token length acceptable by model (truncate if exceeded)
            max_summary_length: maximum generated summary token length
        """
        self.model_name_or_path = model_name_or_path or (str(SUMMARY_MODEL_PATH) if SUMMARY_MODEL_PATH else self.DEFAULT_MODEL_NAME)
        self.device = device if device is not None else (0 if self._gpu_available() else -1)
        self._pipeline: Optional["Pipeline"] = None
        self._tokenizer: Optional["PreTrainedTokenizer"] = None
        self._max_input_tokens = max_input_tokens
        self._max_summary_length = max_summary_length
        self._initialized = False

        logger.info("SummaryModel initialized. model_source=%s device=%s", self.model_name_or_path, self.device)

    def _gpu_available(self) -> bool:
        try:
            import torch
            return torch.cuda.is_available()
        except Exception:
            return False

    def _init_transformer(self):
        """Lazy load HuggingFace pipeline for summarization."""
        if not TRANSFORMERS_AVAILABLE:
            logger.debug("Transformers package not installed; skipping transformer init.")
            self._initialized = True
            return

        try:
            logger.info("Loading summarization pipeline from '%s' on device %s", self.model_name_or_path, self.device)
            # load tokenizer & model via pipeline for convenience
            self._pipeline = pipeline("summarization", model=self.model_name_or_path, tokenizer=self.model_name_or_path, device=self.device)
            # also store tokenizer for token-length checks if needed
            self._tokenizer = self._pipeline.tokenizer if hasattr(self._pipeline, "tokenizer") else None
            self._initialized = True
            logger.info("Summarization pipeline loaded successfully.")
        except Exception as exc:
            logger.exception("Failed to load summarization transformer pipeline: %s. Falling back to extractive.", exc)
            self._pipeline = None
            self._tokenizer = None
            self._initialized = True

    def summarize(self, text: str, max_sentences: int = 3, clean_output: bool = True) -> str:
        """
        Summarize the input text.

        Args:
            text: raw clinical report or notes
            max_sentences: fallback parameter for extractive summarizer
            clean_output: strip/normalize whitespace in result

        Returns:
            summary string
        """
        if not isinstance(text, str) or not text.strip():
            return ""

        # Lazy init if necessary
        if not self._initialized:
            self._init_transformer()

        # If transformer pipeline is available, use it
        if self._pipeline:
            try:
                # Truncate safely if tokenizer available
                input_text = self._truncate_for_model(text)
                # Transformers summarization may be heavy; call with length settings
                result = self._pipeline(input_text, max_length=self._max_summary_length, min_length=30, truncation=True)
                if isinstance(result, list) and result:
                    summary = result[0].get("summary_text", "")
                else:
                    summary = str(result)

                if clean_output:
                    summary = self._cleanup_summary(summary)
                return summary
            except Exception as exc:
                logger.exception("Transformer summarization failed: %s. Falling back to extractive.", exc)
                # fallback to extractive

        # Extractive fallback
        try:
            return self._extractive_summarize(text, max_sentences=max_sentences)
        except Exception as exc:
            logger.exception("Extractive summarizer failed: %s", exc)
            # Last resort: return truncated cleaned text
            truncated = textwrap.shorten(text, width=400, placeholder="...")
            return truncated

    def _truncate_for_model(self, text: str) -> str:
        """
        If tokenizer is available, ensure token length <= max_input_tokens; otherwise
        perform a conservative character-based truncation.
        """
        if self._tokenizer:
            try:
                tokens = self._tokenizer.encode(text, truncation=False)
                if len(tokens) <= self._max_input_tokens:
                    return text
                # decode first N tokens safely
                truncated = self._tokenizer.decode(tokens[: self._max_input_tokens], skip_special_tokens=True, clean_up_tokenization_spaces=True)
                logger.debug("Truncated input from %d tokens to %d tokens for summarization model.", len(tokens), self._max_input_tokens)
                return truncated
            except Exception as exc:
                logger.debug("Tokenizer truncation failed: %s. Falling back to char truncation.", exc)

        # Fallback: character-based truncation (approximate)
        avg_token_len = 4  # heuristic
        approx_chars = int(self._max_input_tokens * avg_token_len)
        if len(text) > approx_chars:
            logger.debug("Char-truncating input for summarizer from %d to %d chars.", len(text), approx_chars)
            return text[:approx_chars]
        return text

    def _cleanup_summary(self, text: str) -> str:
        """
        Normalizes whitespace and punctuation in generated summary.
        """
        s = " ".join(text.split())
        return s.strip()

    def _extractive_summarize(self, text: str, max_sentences: int = 3) -> str:
        """
        Lightweight extractive summarizer:
          - Split into sentences
          - Score sentences by presence of clinical keywords and term frequency
          - Return top-k sentences joined as summary
        """
        sentences = [s.strip() for s in _split_into_sentences(text) if s.strip()]
        if not sentences:
            return ""

        # Score sentences
        keywords = {"diagnosis", "symptom", "result", "impression", "glucose", "blood", "pressure", "hypertension", "diabetes", "cholesterol", "infection"}
        scores = []
        for idx, sent in enumerate(sentences):
            # keyword hits
            sent_lower = sent.lower()
            kw_score = sum(1 for kw in keywords if kw in sent_lower)
            # length score (prefer medium length sentences)
            len_score = 1.0 - abs(len(sent) - 100) / max(len(sent), 100)
            tf_score = _term_frequency_score(sent_lower)
            total_score = kw_score * 2.0 + len_score + tf_score
            scores.append((idx, total_score))

        # pick top sentences by score
        scores.sort(key=lambda x: x[1], reverse=True)
        top_idxs = [idx for idx, _ in scores[:max_sentences]]
        top_idxs.sort()
        top_sentences = [sentences[i] for i in top_idxs]
        summary = " ".join(top_sentences)
        return self._cleanup_summary(summary)


# Helper utilities
def _split_into_sentences(text: str) -> List[str]:
    """
    Rudimentary sentence splitter using punctuation. For production replace with
    NLP sentence tokenizer (e.g., nltk.sent_tokenize or spacy).
    """
    import re
    # split on . ! ? followed by space or EOL
    parts = re.split(r'(?<=[\.\?\!])\s+', text.replace("\n", " ").strip())
    return parts


def _term_frequency_score(sentence: str) -> float:
    """
    Simple term-frequency based score normalized by sentence length.
    """
    words = [w for w in sentence.split() if len(w) > 2]
    if not words:
        return 0.0
    tf = {}
    for w in words:
        tf[w] = tf.get(w, 0) + 1
    max_freq = max(tf.values())
    # normalized score
    score = sum(v / max_freq for v in tf.values()) / len(words)
    return float(score)

class SummaryService:
    """Service for summarizing medical reports using a pretrained transformer model."""
    def __init__(self):
        from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
        from app.config import settings
        from app.utils.logger import get_logger
        import os, torch

        self.logger = get_logger(__name__)
        self.logger.info("Initializing SummaryService...")

        model_path = settings.SUMMARY_MODEL_PATH
        model_path = str(model_path) if model_path is not None else ""
        fallback_model = "facebook/bart-large-cnn"

        try:
            # Handle all valid cases
            if not model_path:
                self.logger.warning("No SUMMARY_MODEL_PATH configured. Using default model.")
                model_name = fallback_model

            elif os.path.isdir(model_path):
                # ✅ Hugging Face model folder
                self.logger.info(f"Loading model from local directory: {model_path}")
                model_name = model_path

            elif os.path.isfile(model_path) and model_path.endswith(".pt"):
                # ✅ PyTorch checkpoint
                self.logger.info(f"Loading checkpoint from: {model_path}")
                base_model = fallback_model
                self.tokenizer = AutoTokenizer.from_pretrained(base_model)
                self.model = AutoModelForSeq2SeqLM.from_pretrained(base_model)
                state = torch.load(model_path, map_location="cpu")
                self.model.load_state_dict(state, strict=False)
                self.logger.info("Loaded .pt checkpoint into base model successfully.")
                return  # ✅ early return after loading checkpoint

            else:
                # ❌ Invalid path fallback
                self.logger.warning(f"Invalid model path '{model_path}', using fallback.")
                model_name = fallback_model

            # ✅ Load tokenizer + model normally
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
            self.logger.info(f"Loaded summarization model: {model_name}")

        except Exception as e:
            self.logger.error(f"Failed to load summarization model: {e}. Falling back to {fallback_model}")
            self.tokenizer = AutoTokenizer.from_pretrained(fallback_model)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(fallback_model)

    def summarize(self, text: str) -> str:
        """Generate a concise summary for input text."""
        if not text.strip():
            return "No content provided to summarize."

        inputs = self.tokenizer(text, return_tensors="pt", max_length=1024, truncation=True)
        summary_ids = self.model.generate(
            inputs["input_ids"],
            num_beams=4,
            max_length=200,
            early_stopping=True
        )
        return self.tokenizer.decode(summary_ids[0], skip_special_tokens=True)

# Optional singleton for reuse
_default_summary_model: Optional[SummaryService] = None


def get_default_summary_model() -> SummaryService:
    global _default_summary_model
    if _default_summary_model is None:
        _default_summary_model = SummaryService()
    return _default_summary_model


def load_model(path: Optional[str] = None):
    """
    Compatibility loader for main.py startup event.
    Initializes and caches a SummaryService model for report summarization.
    """
    global _default_summary_model
    try:
        if '_default_summary_model' not in globals() or _default_summary_model is None:
            _default_summary_model = SummaryService(model_path=path)
            logger.info(f"✅ Summary model loaded successfully (path={path})")
        else:
            logger.info("Summary model already loaded; skipping reload.")
    except Exception as e:
        logger.error(f"❌ Failed to load summary model: {e}")
        raise
    return _default_summary_model



if __name__ == "__main__":
    sm = get_default_summary_model()
    sample = (
        "Clinical history: 56-year-old male with chest pain and shortness of breath. "
        "Investigations: ECG shows ... Impression: Possible myocardial ischemia. "
        "Plan: Start aspirin, refer for coronary angiography. Labs: fasting glucose 140 mg/dL."
    )
    print("SUMMARY:")
    print(sm.summarize(sample))
