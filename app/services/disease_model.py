"""
DiseaseModel service

Responsibilities:
- Load a pretrained tabular disease classifier (sklearn, xgboost, or lightgbm).
- Provide a stable API for inference:
    * predict_proba(features: Dict[str, float]) -> Dict[str, float]
    * predict_batch(feature_matrix: List[Dict[str, float]]) -> List[Dict[str, float]]
- Validate & align feature vectors (feature ordering)
- Optional explainability via SHAP (if available)
- Robust fallback to rule-based heuristics when no model is available (for demo)
"""

from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import threading
import logging
import json
import numpy as np

from app.utils.logger import get_logger
from app.config import settings, DISEASE_MODEL_PATH

logger = get_logger(__name__)

# Optional imports for model backends and explainability
try:
    import joblib
    SKLEARN_AVAILABLE = True
except Exception:
    SKLEARN_AVAILABLE = False
    logger.debug("joblib not available; sklearn models cannot be loaded.")

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except Exception:
    XGBOOST_AVAILABLE = False

try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except Exception:
    LIGHTGBM_AVAILABLE = False

try:
    import shap
    SHAP_AVAILABLE = True
except Exception:
    SHAP_AVAILABLE = False
    logger.debug("shap not available; explainability disabled.")


class ModelNotLoadedError(RuntimeError):
    pass


class DiseaseModel:
    """
    Wrapper for tabular disease risk models.

    Usage:
        dm = DiseaseModel(model_path="/path/to/model.pkl", feature_columns=["FastingGlucose","hr_mean",...])
        probs = dm.predict_proba({"FastingGlucose": 0.8, "hr_mean": 0.7})
    """

    _load_lock = threading.Lock()

    def __init__(self,
                 model_path: Optional[str] = None,
                 feature_columns: Optional[List[str]] = None,
                 model_type: Optional[str] = None,
                 enable_shap: bool = False):
        """
        Args:
            model_path: local filesystem path to the serialized model (joblib / xgb / lgbm)
            feature_columns: ordered list of feature names expected by the model
            model_type: optional override; one of "sklearn", "xgboost", "lightgbm"
            enable_shap: enable SHAP explainability (requires shap)
        """
        self.model_path = Path(model_path) if model_path else Path(DISEASE_MODEL_PATH)
        self.feature_columns = feature_columns or []
        self.model = None
        self.model_type = model_type
        self._is_loaded = False
        self.enable_shap = enable_shap and SHAP_AVAILABLE
        self._explainer = None
        logger.info("DiseaseModel init: model_path=%s, enable_shap=%s", self.model_path, self.enable_shap)

    # -------------------------
    # Loading & helper methods
    # -------------------------
    def load(self, force: bool = False) -> None:
        """
        Load model from disk. Thread-safe.
        """
        with DiseaseModel._load_lock:
            if self._is_loaded and not force:
                logger.debug("DiseaseModel already loaded; skipping reload.")
                return

            if not self.model_path.exists():
                logger.warning("DiseaseModel file not found at %s. Model will run in fallback mode.", self.model_path)
                self.model = None
                self._is_loaded = False
                return

            # Try joblib first (sklearn, xgboost sklearn wrapper, lightgbm sklearn wrapper)
            try:
                logger.info("Attempting to load model with joblib from %s", self.model_path)
                self.model = joblib.load(str(self.model_path))
                # attempt to infer model type if not provided
                if not self.model_type:
                    self.model_type = self._infer_model_type_from_object(self.model)
                logger.info("Model loaded via joblib. Inferred type: %s", self.model_type)
                self._is_loaded = True
            except Exception as exc:
                logger.debug("joblib load failed: %s", exc)
                # Try XGBoost native loading
                if XGBOOST_AVAILABLE and self.model_path.suffix in (".json", ".model", ".bin"):
                    try:
                        logger.info("Attempting XGBoost native load from %s", self.model_path)
                        self.model = xgb.Booster()
                        self.model.load_model(str(self.model_path))
                        self.model_type = "xgboost"
                        self._is_loaded = True
                        logger.info("XGBoost model loaded.")
                    except Exception as exc2:
                        logger.exception("XGBoost load failed: %s", exc2)
                        self.model = None
                        self._is_loaded = False
                elif LIGHTGBM_AVAILABLE and self.model_path.suffix in (".txt", ".model", ".bin"):
                    try:
                        logger.info("Attempting LightGBM native load from %s", self.model_path)
                        self.model = lgb.Booster(model_file=str(self.model_path))
                        self.model_type = "lightgbm"
                        self._is_loaded = True
                        logger.info("LightGBM model loaded.")
                    except Exception as exc3:
                        logger.exception("LightGBM load failed: %s", exc3)
                        self.model = None
                        self._is_loaded = False
                else:
                    logger.warning("No compatible model loader succeeded. Running in fallback mode.")
                    self.model = None
                    self._is_loaded = False

            # Attempt to load feature_columns if stored alongside model (e.g., model metadata)
            try:
                meta_path = self.model_path.with_suffix(self.model_path.suffix + ".meta")
                if meta_path.exists():
                    with open(meta_path, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                        if not self.feature_columns and isinstance(meta.get("feature_columns"), list):
                            self.feature_columns = meta["feature_columns"]
                            logger.info("Loaded feature_columns from metadata (%d features).", len(self.feature_columns))
            except Exception as exc:
                logger.debug("Failed to load metadata file: %s", exc)

            # If shap requested and model loaded, init explainer
            if self._is_loaded and self.enable_shap:
                self._init_shap_explainer()

    def _infer_model_type_from_object(self, model_obj: Any) -> str:
        """
        Heuristic inference for model type
        """
        try:
            import sklearn
            if hasattr(model_obj, "predict_proba"):
                return "sklearn"
            # xgboost sklearn wrapper has __class__.__name__ == 'XGBClassifier' etc.
            cname = model_obj.__class__.__name__.lower()
            if "xgb" in cname or "xgboost" in cname:
                return "xgboost"
            if "lgbm" in cname or "lightgbm" in cname or "lgb" in cname:
                return "lightgbm"
        except Exception:
            pass
        return "unknown"

    def _init_shap_explainer(self):
        """
        Initialize SHAP explainer. Works for tree-based models primarily.
        """
        try:
            if not SHAP_AVAILABLE:
                logger.warning("SHAP not available; cannot initialize explainer.")
                return
            logger.info("Initializing SHAP explainer for the model.")
            # For tree models, use TreeExplainer; fallback to KernelExplainer if needed
            if self.model_type in ("xgboost", "lightgbm", "sklearn"):
                try:
                    self._explainer = shap.TreeExplainer(self.model)
                except Exception:
                    # Kernel explainer fallback (slow)
                    self._explainer = shap.KernelExplainer(self.model.predict_proba, np.zeros((1, max(1, len(self.feature_columns)))))
                logger.info("SHAP explainer initialized.")
        except Exception as exc:
            logger.exception("Failed to initialize SHAP explainer: %s", exc)
            self._explainer = None

    # -------------------------
    # Prediction methods
    # -------------------------
    def _validate_and_vectorize(self, features: Dict[str, float]) -> Tuple[np.ndarray, List[str]]:
        """
        Align user-supplied feature dict into ordered numpy vector as expected by the model.
        If feature_columns is empty, infer from features keys (sorted) — but this is not ideal.
        """
        if not isinstance(features, dict):
            raise ValueError("Features must be a dict mapping feature_name->numeric_value")

        if not self.feature_columns:
            # Infer ordering deterministically: sorted keys
            logger.debug("Feature columns not provided; inferring from provided feature dict keys (sorted).")
            self.feature_columns = sorted(list(features.keys()))

        vector = []
        for fname in self.feature_columns:
            v = features.get(fname)
            if v is None:
                # Missing value: use 0.0 as neutral placeholder and log a warning
                logger.debug("Feature '%s' missing from input; substituting 0.0", fname)
                vector.append(0.0)
            else:
                try:
                    vector.append(float(v))
                except Exception:
                    logger.debug("Feature '%s' with non-numeric value '%s'; substituting 0.0", fname, v)
                    vector.append(0.0)
        return np.array(vector, dtype=float).reshape(1, -1), list(self.feature_columns)

    def predict_proba(self, features: Dict[str, float]) -> Dict[str, float]:
        """
        Single-instance probability prediction.

        Returns dict mapping disease_name -> probability in [0,1].
        If no model is loaded, returns rule-based heuristic probabilities.
        """
        # Ensure model loaded (try lazy load)
        if not self._is_loaded:
            self.load()

        # Validate & vectorize
        x_vec, cols = self._validate_and_vectorize(features)

        # If no model available, use fallback heuristics
        if not self._is_loaded or self.model is None:
            logger.debug("Model not loaded; using rule-based fallback for disease prediction.")
            return self._rule_based_predict(features)

        try:
            probs = None
            if self.model_type == "sklearn" or hasattr(self.model, "predict_proba"):
                # scikit-learn API
                pred = self.model.predict_proba(x_vec)
                # pred shape: (n_samples, n_classes)
                probs = self._map_proba_array_to_dict(pred[0])
            elif self.model_type == "xgboost" and XGBOOST_AVAILABLE:
                # XGBoost Booster: use DMatrix & predict
                dmat = xgb.DMatrix(x_vec, feature_names=cols)
                raw = self.model.predict(dmat)
                # xgboost may return shape (n_samples, n_classes) for multiclass or (n,) for binary
                probs = self._map_xgb_output_to_dict(raw)
            elif self.model_type == "lightgbm" and LIGHTGBM_AVAILABLE:
                raw = self.model.predict(x_vec)
                probs = self._map_xgb_output_to_dict(raw)
            else:
                # Unknown model type: try generic predict_proba if present
                if hasattr(self.model, "predict_proba"):
                    pred = self.model.predict_proba(x_vec)
                    probs = self._map_proba_array_to_dict(pred[0])
                else:
                    logger.warning("Model loaded but type unsupported; using fallback.")
                    return self._rule_based_predict(features)

            # Ensure probabilities are in [0,1] and numeric
            probs = {k: float(max(0.0, min(1.0, float(v)))) for k, v in probs.items()}
            logger.debug("Predicted probabilities: %s", probs)
            return probs
        except Exception as exc:
            logger.exception("Model prediction failed, falling back to rules: %s", exc)
            return self._rule_based_predict(features)

    def predict_batch(self, feature_list: List[Dict[str, float]]) -> List[Dict[str, float]]:
        """
        Predict probabilities for a batch of feature dicts.
        """
        results = []
        for f in feature_list:
            results.append(self.predict_proba(f))
        return results

    # -------------------------
    # Helpers: mapping model outputs to disease dicts
    # -------------------------
    def _map_proba_array_to_dict(self, proba_array: np.ndarray) -> Dict[str, float]:
        """
        Map sklearn proba arrays to disease dictionary. Requires that model.classes_ exists.
        """
        try:
            classes = getattr(self.model, "classes_", None)
            if classes is None:
                # fallback naming
                return {"disease_0": float(proba_array[0])}
            # if binary classifier with shape (n_samples,2) and classes [0,1], we may map to a default disease
            # For multiclass, classes might be disease labels
            if len(classes) == 2:
                # interpret second column as positive-class probability; use meta mapping if available
                # Try to read mapping from model if present
                disease_label = getattr(self.model, "disease_label", None) or "positive_class"
                return {str(disease_label): float(proba_array[1])}
            else:
                return {str(c): float(proba_array[idx]) for idx, c in enumerate(classes)}
        except Exception as exc:
            logger.debug("Failed to map proba array to dict: %s", exc)
            # fallback: create generic keys
            return {f"disease_{i}": float(p) for i, p in enumerate(proba_array)}

    def _map_xgb_output_to_dict(self, raw_output: Any) -> Dict[str, float]:
        """
        Interpret xgboost/lightgbm raw output.
        - For binary classification, xgboost returns a float array of shape (n,) with probability for positive class.
        - For multiclass, it returns shape (n, num_class) flattened; xgboost python API may return list of lists.
        """
        try:
            arr = np.array(raw_output)
            if arr.ndim == 1:
                # binary: arr -> prob positive
                return {"positive_class": float(arr[0])}
            elif arr.ndim == 2:
                # multiclass: return generic mapping
                return {f"class_{i}": float(v) for i, v in enumerate(arr[0])}
            else:
                return {"score": float(arr.flatten()[0])}
        except Exception as exc:
            logger.debug("Failed to map xgboost output: %s", exc)
            return {"score": 0.0}

    # -------------------------
    # Explainability (SHAP)
    # -------------------------
    def explain(self, features: Dict[str, float], max_features: int = 10) -> Optional[Dict[str, float]]:
        """
        Return SHAP values for the provided feature vector (dict mapping).
        Requires enable_shap=True and shap installed.
        """
        if not self.enable_shap or not SHAP_AVAILABLE:
            logger.warning("SHAP explainability not enabled or shap not installed.")
            return None

        if not self._is_loaded or self.model is None:
            logger.warning("Model not loaded; cannot compute SHAP values.")
            return None

        try:
            x_vec, cols = self._validate_and_vectorize(features)
            shap_values = self._explainer.shap_values(x_vec)
            # shap_values may be list (per-class) or array
            # For binary, shap_values[1] typical; handle generically by averaging absolute contributions
            if isinstance(shap_values, list):
                # choose the set with same length as number of features
                arr = np.array(shap_values[0]) if len(shap_values) > 0 else np.array(shap_values)
            else:
                arr = np.array(shap_values)
            # arr shape: (num_class?, n_features)
            # reduce to (n_features,) by averaging magnitude
            if arr.ndim == 2:
                vals = np.mean(np.abs(arr), axis=0)
            else:
                vals = np.abs(arr).flatten()
            # map top features
            idxs = np.argsort(-vals)[:max_features]
            return {cols[i]: float(vals[i]) for i in idxs}
        except Exception as exc:
            logger.exception("SHAP explanation failed: %s", exc)
            return None

    # -------------------------
    # Fallback heuristics
    # -------------------------
    def _rule_based_predict(self, features: Dict[str, float]) -> Dict[str, float]:
        """
        Lightweight deterministic heuristics for demo. Important to replace with real model outputs.
        Example:
            - Diabetes: FastingGlucose normalized > 0.2 -> risk proportional
            - Hypertension: bp_sys_mean > 0.6 -> risk
        """
        diabetes = 0.0
        if "FastingGlucose" in features:
            try:
                val = float(features.get("FastingGlucose", 0.0))
                diabetes = min(max(val, 0.0), 1.0)
            except Exception:
                diabetes = 0.0

        hypertension = 0.0
        if "bp_sys_mean" in features:
            try:
                bp = float(features.get("bp_sys_mean", 0.0))
                # map typical normalized values to probability
                hypertension = float(min(max((bp - 0.5) * 2.0, 0.0), 1.0))
            except Exception:
                hypertension = 0.0

        cardiac = 0.0
        if "hr_mean" in features:
            try:
                hr = float(features.get("hr_mean", 0.0))
                cardiac = float(min(max((hr - 0.6) * 1.5, 0.0), 1.0))
            except Exception:
                cardiac = 0.0

        return {
            "diabetes": round(diabetes, 4),
            "hypertension": round(hypertension, 4),
            "cardiac": round(cardiac, 4)
        }


# Singleton default instance for convenience
_default_disease_model: Optional[DiseaseModel] = None


def get_default_disease_model(model_path: Optional[str] = None,
                              feature_columns: Optional[List[str]] = None,
                              model_type: Optional[str] = None,
                              enable_shap: bool = False) -> DiseaseModel:
    global _default_disease_model
    if _default_disease_model is None:
        _default_disease_model = DiseaseModel(model_path=model_path, feature_columns=feature_columns, model_type=model_type, enable_shap=enable_shap)
    return _default_disease_model

def load_model(force: bool = False):
    """
    Module-level loader for global default disease model.
    This allows main.py to call disease_model.load_model() safely.
    """
    global _default_disease_model
    if _default_disease_model is None:
        _default_disease_model = DiseaseModel()
    _default_disease_model.load(force=force)
    return _default_disease_model


# Quick CLI test
if __name__ == "__main__":
    dm = get_default_disease_model()
    # example synthetic features (normalized)
    sample = {"FastingGlucose": 0.8, "bp_sys_mean": 0.6, "hr_mean": 0.75}
    print("Predict:", dm.predict_proba(sample))
    if SHAP_AVAILABLE:
        print("Explain:", dm.explain(sample))
