"""
PersonalizationEngine

Extended version with contextual updates:
- update_history_context(): integrates patient history embeddings
- update_image_context(): stores image-derived metrics
- auto_adapt_weights_from_context(): heuristic fusion adaptation
"""

from typing import Dict, Any, Optional
from pathlib import Path
import json
import csv
import threading
from datetime import datetime
import tempfile
import shutil
import logging
import os

from app.config import PERSONALIZED_DIR, DEFAULT_WEIGHTS
from app.utils.logger import get_logger

logger = get_logger(__name__)

_write_locks: Dict[str, threading.Lock] = {}


def _get_lock(patient_id: str) -> threading.Lock:
    if patient_id not in _write_locks:
        _write_locks[patient_id] = threading.Lock()
    return _write_locks[patient_id]


class PersonalizationEngine:
    """File-backed personalization and context manager."""

    WEIGHTS_FILENAME = "weights.json"
    HISTORY_FILENAME = "history.csv"
    HISTORY_CONTEXT_FILENAME = "context_history.json"
    IMAGE_CONTEXT_FILENAME = "context_image.json"

    def __init__(self, personalized_dir: Optional[Path] = None):
        self.personalized_dir = Path(personalized_dir or PERSONALIZED_DIR)
        self.personalized_dir.mkdir(parents=True, exist_ok=True)
        logger.info("PersonalizationEngine initialized: dir=%s", self.personalized_dir)

    def _patient_dir(self, patient_id: str) -> Path:
        pdir = self.personalized_dir / str(patient_id)
        pdir.mkdir(parents=True, exist_ok=True)
        return pdir

    # -------------------- Core Personalization --------------------

    def load_patient_settings(self, patient_id: str) -> Dict[str, Any]:
        pdir = self._patient_dir(patient_id)
        weights_path = pdir / self.WEIGHTS_FILENAME
        if not weights_path.exists():
            return {"weights": DEFAULT_WEIGHTS.copy(), "thresholds": {}, "profile": {}}
        try:
            with open(weights_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            data.setdefault("weights", DEFAULT_WEIGHTS.copy())
            data.setdefault("thresholds", {})
            data.setdefault("profile", {})
            return data
        except Exception as exc:
            logger.exception("Failed to load personalization for %s: %s", patient_id, exc)
            return {"weights": DEFAULT_WEIGHTS.copy(), "thresholds": {}, "profile": {}}

    def save_patient_settings(self, patient_id: str, settings: Dict[str, Any], author: Optional[str] = None) -> None:
        if not isinstance(settings, dict):
            raise ValueError("settings must be a dict")

        pdir = self._patient_dir(patient_id)
        weights_path = pdir / self.WEIGHTS_FILENAME
        history_path = pdir / self.HISTORY_FILENAME

        lock = _get_lock(patient_id)
        with lock:
            try:
                tmp_fd, tmp_path = tempfile.mkstemp(dir=str(pdir))
                with open(tmp_fd, "w", encoding="utf-8") as tmpf:
                    json.dump(settings, tmpf, indent=2)
                shutil.move(tmp_path, str(weights_path))
                logger.info("Saved personalization for %s", patient_id)
            except Exception as exc:
                logger.exception("Failed to save personalization file for %s: %s", patient_id, exc)
                raise

            try:
                now = datetime.utcnow().isoformat() + "Z"
                entry = {
                    "timestamp": now,
                    "author": author or "system",
                    "summary": self._history_summary(settings)
                }
                write_header = not history_path.exists()
                with open(history_path, "a", newline="", encoding="utf-8") as hf:
                    writer = csv.DictWriter(hf, fieldnames=["timestamp", "author", "summary"])
                    if write_header:
                        writer.writeheader()
                    writer.writerow(entry)
            except Exception as exc:
                logger.exception("Failed to append personalization history: %s", exc)

    def _history_summary(self, settings: Dict[str, Any]) -> str:
        try:
            w = settings.get("weights", {})
            t = settings.get("thresholds", {})
            parts = []
            if w:
                parts.append("weights:" + ",".join(f"{k}={v}" for k, v in w.items()))
            if t:
                parts.append("thresholds:" + ",".join(f"{k}={v}" for k, v in t.items()))
            return ";".join(parts)[:200] if parts else "no-changes"
        except Exception:
            return "update"

    # -------------------- Contextual Extensions --------------------

    def update_history_context(self, patient_id: str, history_data: Dict[str, Any]) -> None:
        """Store patient history embeddings or structured summaries."""
        pdir = self._patient_dir(patient_id)
        history_path = pdir / self.HISTORY_CONTEXT_FILENAME
        try:
            existing = {}
            if history_path.exists():
                with open(history_path, "r", encoding="utf-8") as f:
                    existing = json.load(f)
            existing.update({
                datetime.utcnow().isoformat() + "Z": history_data
            })
            with open(history_path, "w", encoding="utf-8") as f:
                json.dump(existing, f, indent=2)
            logger.info("Updated history context for %s (%d entries)", patient_id, len(existing))
        except Exception as exc:
            logger.exception("Failed to update history context for %s: %s", patient_id, exc)

    def update_image_context(self, patient_id: str, image_metrics: Dict[str, Any]) -> None:
        """Store image-derived biomarkers or scores."""
        pdir = self._patient_dir(patient_id)
        image_path = pdir / self.IMAGE_CONTEXT_FILENAME
        try:
            existing = {}
            if image_path.exists():
                with open(image_path, "r", encoding="utf-8") as f:
                    existing = json.load(f)
            existing.update({
                datetime.utcnow().isoformat() + "Z": image_metrics
            })
            with open(image_path, "w", encoding="utf-8") as f:
                json.dump(existing, f, indent=2)
            logger.info("Updated image context for %s (%d entries)", patient_id, len(existing))
        except Exception as exc:
            logger.exception("Failed to update image context for %s: %s", patient_id, exc)

    def auto_adapt_weights_from_context(self, patient_id: str, base_weights: Optional[Dict[str, float]] = None) -> Dict[str, float]:
        """Heuristic adaptation of weights based on stored context (non-learning)."""
        base_weights = base_weights or DEFAULT_WEIGHTS.copy()
        try:
            pdir = self._patient_dir(patient_id)
            hist_path = pdir / self.HISTORY_CONTEXT_FILENAME
            img_path = pdir / self.IMAGE_CONTEXT_FILENAME

            history_text = ""
            if hist_path.exists():
                with open(hist_path, "r", encoding="utf-8") as f:
                    history_text = json.dumps(json.load(f)).lower()

            img_text = ""
            if img_path.exists():
                with open(img_path, "r", encoding="utf-8") as f:
                    img_text = json.dumps(json.load(f)).lower()

            adapted = dict(base_weights)
            # Example rule-based deltas
            if "chronic" in history_text or "long-term" in history_text:
                adapted["disease"] = min(adapted.get("disease", 1.0) * 1.2, 2.0)
            if "inflammation" in history_text:
                adapted["symptom"] = adapted.get("symptom", 1.0) * 1.1
            if "retina" in img_text or "lesion" in img_text:
                adapted["image"] = adapted.get("image", 1.0) * 1.15

            logger.info("Auto-adapted weights for %s: %s", patient_id, adapted)
            return adapted
        except Exception as exc:
            logger.exception("Failed auto adaptation for %s: %s", patient_id, exc)
            return base_weights

    # -------------------- Profile and Thresholds --------------------

    def update_weights(self, patient_id: str, new_weights: Dict[str, float], author: Optional[str] = None) -> None:
        settings = self.load_patient_settings(patient_id)
        settings.setdefault("weights", DEFAULT_WEIGHTS.copy())
        for k, v in new_weights.items():
            try:
                settings["weights"][k] = float(v)
            except Exception:
                logger.debug("Invalid weight value ignored: %s=%s", k, v)
        self.save_patient_settings(patient_id, settings, author=author)

    def update_thresholds(self, patient_id: str, new_thresholds: Dict[str, float], author: Optional[str] = None) -> None:
        settings = self.load_patient_settings(patient_id)
        settings.setdefault("thresholds", {})
        for k, v in new_thresholds.items():
            try:
                settings["thresholds"][k] = float(v)
            except Exception:
                logger.debug("Invalid threshold ignored: %s=%s", k, v)
        self.save_patient_settings(patient_id, settings, author=author)

    def update_profile(self, patient_id: str, profile_updates: Dict[str, Any], author: Optional[str] = None) -> None:
        settings = self.load_patient_settings(patient_id)
        settings.setdefault("profile", {})
        settings["profile"].update(profile_updates)
        self.save_patient_settings(patient_id, settings, author=author)

    # -------------------- Fine-tuning Stub --------------------

    def fine_tune_model_stub(self, patient_id: str, training_data_path: Optional[Path] = None) -> Dict[str, Any]:
        logger.info("fine_tune_model_stub called for %s", patient_id)
        now = datetime.utcnow().isoformat() + "Z"
        return {"status": "queued", "patient_id": patient_id, "queued_at": now}


# --------------------------------------------------------------------------
# Lifecycle Management Hooks for Startup and Shutdown
# --------------------------------------------------------------------------

def initialize():
    """
    Called on FastAPI startup to initialize personalization resources.
    """
    global personalization_session
    try:
        logger.info("🚀 Initializing PersonalizationEngine resources...")
        personalization_session = {}
        cache_dir = os.path.join(os.getcwd(), "models", "personalized")
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
        personalization_session["cache_dir"] = cache_dir
        logger.info("✅ PersonalizationEngine initialization complete.")
    except Exception as e:
        logger.warning(f"⚠️ PersonalizationEngine initialization encountered an issue: {e}")


def cleanup():
    """
    Called on FastAPI shutdown to gracefully release personalization resources.
    """
    global personalization_session
    try:
        logger.info("🧹 Cleaning up PersonalizationEngine resources...")
        personalization_session = {}
        logger.info("✅ PersonalizationEngine cleanup complete.")
    except Exception as e:
        logger.warning(f"⚠️ PersonalizationEngine cleanup encountered an issue: {e}")
