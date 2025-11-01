"""
Recommender service (hybrid)

Responsibilities:
- Generate preventive-care suggestions (diet, exercise, screenings, follow-ups)
  based on:
    * disease risk scores (from DiseaseModel)
    * extracted symptoms (from SymptomModel)
    * patient profile & personalization settings
- Provide an "explain" structure that justifies each recommendation
- Allow ML-based scoring hooks (placeholder) for future upgrades
- Deterministic, testable, and safe for hackathon/demo
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import logging

from app.utils.logger import get_logger
from app.services.personalization_engine import PersonalizationEngine
from app.config import DEFAULT_WEIGHTS

logger = get_logger(__name__)


@dataclass
class Recommendation:
    code: str
    title: str
    text: str
    severity: str  # low|medium|high
    reasons: List[str]
    categories: List[str]  # e.g., ["diet", "exercise", "screening"]


class Recommender:
    """
    Hybrid recommender:
      - Core rule-based engine with clear deterministic rules.
      - Hooks for ML-based scoring (scored_recs) that can be plugged later.
      - Uses personalization settings to adjust thresholds and tone.
    """

    # Thresholds used for mapping probabilities to severity levels (can be overridden)
    DEFAULT_THRESHOLDS = {
        "low": 0.2,
        "medium": 0.5,
        "high": 0.75
    }

    def __init__(self, personalization_engine: Optional[PersonalizationEngine] = None):
        self.personalization_engine = personalization_engine or PersonalizationEngine()
        logger.info("Recommender initialized with personalization engine=%s", bool(personalization_engine))

    # ----------------------------
    # Public API
    # ----------------------------
    def get_recommendations(self,
                            patient_id: str,
                            risk_scores: Dict[str, float],
                            symptoms: Optional[List[Dict[str, str]]] = None,
                            profile: Optional[Dict[str, Any]] = None,
                            max_recs: int = 6) -> Dict[str, Any]:
        """
        Generate a prioritized list of recommendations and explanations.

        Returns:
            {
                "patient_id": str,
                "recommendations": [ {...}, ... ],
                "metadata": {...}
            }
        """
        profile = profile or {}
        symptoms = symptoms or []

        # load personalization settings (weights, thresholds, profile overrides)
        psettings = self.personalization_engine.load_patient_settings(patient_id)
        thresholds = self._merge_thresholds(self.DEFAULT_THRESHOLDS, psettings.get("thresholds", {}))
        weights = psettings.get("weights", DEFAULT_WEIGHTS)

        logger.debug("Generating recommendations for %s with risks=%s and thresholds=%s", patient_id, risk_scores, thresholds)

        # Core rule-based recs
        rule_recs = self._rule_based_recommendations(risk_scores, symptoms, profile, thresholds)

        # Optional ML-scored recommendations hook (returns scored dict {code: score})
        ml_scores = self._ml_scoring_hook(patient_id, risk_scores, symptoms, profile)

        # Merge and rank recommendations using ML scores (if available) + severity heuristic
        merged = self._merge_and_rank(rule_recs, ml_scores)

        # Limit to top-k
        top_recs = merged[:max_recs]

        # Format to serializable dicts
        recs_out = [self._to_dict(r) for r in top_recs]

        metadata = {
            "applied_thresholds": thresholds,
            "personalization": {
                "weights": weights,
                "overrides": psettings.get("weights", {})
            },
            "ml_hook_active": bool(ml_scores)
        }

        logger.info("Generated %d recommendations for patient_id=%s", len(recs_out), patient_id)
        return {"patient_id": patient_id, "recommendations": recs_out, "metadata": metadata}

    def explain(self, recommendation_code: str, risk_scores: Dict[str, float], profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Provide a structured explanation for a single recommendation code.
        """
        # Recompute rule reasons for that code
        # We produce the same reason format as in get_recommendations
        # For simplicity, call the rule engine and filter
        all_recs = self._rule_based_recommendations(risk_scores, [], profile, self.DEFAULT_THRESHOLDS)
        for r in all_recs:
            if r.code == recommendation_code:
                return {"code": r.code, "title": r.title, "reasons": r.reasons, "severity": r.severity}
        return {"code": recommendation_code, "error": "Recommendation code not found in rule engine"}

    # ----------------------------
    # Internal helpers
    # ----------------------------
    def _merge_thresholds(self, default: Dict[str, float], override: Dict[str, float]) -> Dict[str, float]:
        thresholds = dict(default)
        for k, v in override.items():
            try:
                thresholds[k] = float(v)
            except Exception:
                logger.debug("Invalid threshold override for %s: %s", k, v)
        return thresholds

    def _rule_based_recommendations(self,
                                    risk_scores: Dict[str, float],
                                    symptoms: List[Dict[str, str]],
                                    profile: Dict[str, Any],
                                    thresholds: Dict[str, float]) -> List[Recommendation]:
        """
        Build deterministic recommendations based on common clinical heuristics.
        Returns a list of Recommendation objects (unsorted).
        """
        recs: List[Recommendation] = []
        # utility
        def severity_from_score(score: float) -> str:
            if score >= thresholds["high"]:
                return "high"
            if score >= thresholds["medium"]:
                return "medium"
            return "low"

        # Example: Diabetes recommendations
        d_score = risk_scores.get("diabetes", 0.0)
        if d_score >= thresholds["low"]:
            sev = severity_from_score(d_score)
            reasons = [f"Estimated diabetes risk {d_score:.2f}"]
            # if fasting glucose indicated in profile/labs, provide more reason
            if profile.get("last_fasting_glucose"):
                reasons.append(f"Latest fasting glucose: {profile.get('last_fasting_glucose')}")
            recs.append(Recommendation(
                code="R_DIAB_1",
                title="Blood Glucose Follow-up & Diet",
                text="Schedule a fasting blood glucose and HbA1c test. Begin low-refined-carbohydrate diet and monitor sugars.",
                severity=sev,
                reasons=reasons,
                categories=["screening", "diet"]
            ))
            if sev in ("medium", "high"):
                recs.append(Recommendation(
                    code="R_DIAB_2",
                    title="Increase Physical Activity",
                    text="Start daily 30 minutes of moderate-intensity exercise; consider supervised program if high risk.",
                    severity=sev,
                    reasons=["Physical activity reduces risk of progression to diabetes."],
                    categories=["exercise"]
                ))

        # Hypertension recommendations
        h_score = risk_scores.get("hypertension", 0.0)
        if h_score >= thresholds["low"]:
            sev = severity_from_score(h_score)
            recs.append(Recommendation(
                code="R_HTN_1",
                title="BP Monitoring & Sodium Reduction",
                text="Monitor blood pressure at home; reduce salt intake; review antihypertensive therapy if already prescribed.",
                severity=sev,
                reasons=[f"Estimated hypertension risk {h_score:.2f}"],
                categories=["monitoring", "diet"]
            ))
            if profile.get("age") and int(profile.get("age")) > 60 and h_score >= thresholds["medium"]:
                recs.append(Recommendation(
                    code="R_HTN_2",
                    title="Cardiovascular Screening",
                    text="Recommend cardiovascular risk assessment and lipid profile; consider ECG if symptomatic.",
                    severity="medium",
                    reasons=["Age > 60 and elevated BP risk"],
                    categories=["screening"]
                ))

        # Cardiac recommendations
        c_score = risk_scores.get("cardiac", 0.0)
        if c_score >= thresholds["low"]:
            sev = severity_from_score(c_score)
            recs.append(Recommendation(
                code="R_CARD_1",
                title="Cardiology Review",
                text="If chest pain or palpitations are present, arrange urgent cardiology consult and ECG.",
                severity=sev,
                reasons=[f"Estimated cardiac risk {c_score:.2f}"] + ([f"Symptoms: {', '.join([s['entity'] for s in symptoms])}"] if symptoms else []),
                categories=["urgent", "consult"]
            ))

        # Lifestyle generic recs based on BMI
        bmi = profile.get("bmi")
        try:
            if bmi:
                bmi_val = float(bmi)
                if bmi_val >= 30:
                    recs.append(Recommendation(
                        code="R_BMI_1",
                        title="Weight Management Program",
                        text="Enroll in supervised weight loss program with dietary counselling and physical therapy.",
                        severity="medium",
                        reasons=[f"BMI {bmi_val} indicates obesity."],
                        categories=["diet", "exercise"]
                    ))
                elif 25 <= bmi_val < 30:
                    recs.append(Recommendation(
                        code="R_BMI_2",
                        title="Lifestyle Counseling",
                        text="Adopt calorie-controlled diet and increase physical activity to reduce cardiovascular risk.",
                        severity="low",
                        reasons=[f"BMI {bmi_val} in overweight range."],
                        categories=["diet", "exercise"]
                    ))
        except Exception:
            logger.debug("Invalid BMI in profile: %s", profile.get("bmi"))

        # Preventive screening for older adults
        age = profile.get("age")
        try:
            if age and int(age) >= 50:
                recs.append(Recommendation(
                    code="R_SCREEN_1",
                    title="Age-based Preventive Screening",
                    text="Recommend regular screening: lipid profile, colonoscopy (as per local guidelines), blood pressure and glucose monitoring.",
                    severity="low",
                    reasons=[f"Age {age} ≥ 50 triggers routine preventive screening."],
                    categories=["screening"]
                ))
        except Exception:
            logger.debug("Invalid age value: %s", age)

        # Merge duplicates (same code) preserving highest severity
        merged = self._merge_duplicate_recs(recs)
        return merged

    def _merge_duplicate_recs(self, recs: List[Recommendation]) -> List[Recommendation]:
        out: Dict[str, Recommendation] = {}
        severity_rank = {"low": 0, "medium": 1, "high": 2}
        for r in recs:
            if r.code in out:
                existing = out[r.code]
                # merge reasons & categories and pick highest severity
                combined_reasons = list(set(existing.reasons + r.reasons))
                combined_categories = list(set(existing.categories + r.categories))
                chosen_sev = r.severity if severity_rank.get(r.severity, 0) > severity_rank.get(existing.severity, 0) else existing.severity
                out[r.code] = Recommendation(
                    code=r.code,
                    title=r.title,
                    text=r.text,
                    severity=chosen_sev,
                    reasons=combined_reasons,
                    categories=combined_categories
                )
            else:
                out[r.code] = r
        return list(out.values())

    def _ml_scoring_hook(self,
                        patient_id: str,
                        risk_scores: Dict[str, float],
                        symptoms: List[Dict[str, str]],
                        profile: Dict[str, Any]) -> Dict[str, float]:
        """
        Placeholder for ML scoring of recommendations.
        Returns a dict mapping rec_code -> score (0..1). In the hybrid setup,
        rule-based recs are boosted by ML scores if available.
        For now, we return empty dict (no ML).
        """
        # Example: call a ranking model endpoint or local lightweight model.
        # For hackathon/demo, we don't have a trained ranking model; return empty.
        return {}

    def _merge_and_rank(self, recs: List[Recommendation], ml_scores: Dict[str, float]) -> List[Recommendation]:
        """
        Rank recommendations by composite score:
            composite_score = base_severity_score + ml_score_weight * ml_score
        where base_severity_score maps low|medium|high -> numeric values.
        """
        severity_map = {"low": 0.2, "medium": 0.6, "high": 0.9}
        ml_weight = 0.4  # how much ML influences final ranking (configurable)

        scored: List[Tuple[Recommendation, float]] = []
        for r in recs:
            base = severity_map.get(r.severity, 0.2)
            ml = ml_scores.get(r.code, 0.0)
            composite = base * (1.0 - ml_weight) + ml * ml_weight
            scored.append((r, composite))

        # sort by composite descending
        scored.sort(key=lambda x: x[1], reverse=True)
        return [r for r, _ in scored]

    def _to_dict(self, rec: Recommendation) -> Dict[str, Any]:
        return {
            "code": rec.code,
            "title": rec.title,
            "text": rec.text,
            "severity": rec.severity,
            "reasons": rec.reasons,
            "categories": rec.categories
        }
# --------------------------------------------------------------------------
# Optional global recommender engine instance and initialization hook
# --------------------------------------------------------------------------

recommender_instance: Optional[Recommender] = None

def init_engine() -> Recommender:
    """
    Initialize the Recommender engine globally.
    This ensures consistent startup behavior with other services like fusion_layer, etc.
    """
    global recommender_instance
    try:
        recommender_instance = Recommender()
        logger.info("✅ Recommender engine initialized successfully.")
        return recommender_instance
    except Exception as e:
        logger.exception("❌ Failed to initialize Recommender engine: %s", e)
        raise

def get_engine() -> Recommender:
    """
    Get a singleton instance of the recommender engine.
    If not initialized, automatically create one.
    """
    global recommender_instance
    if recommender_instance is None:
        recommender_instance = init_engine()
    return recommender_instance
