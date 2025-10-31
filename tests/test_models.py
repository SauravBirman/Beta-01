"""
Tests for AI model services
"""

import pytest
from app.services.symptom_model import SymptomModelService
from app.services.summary_model import SummaryModelService
from app.services.disease_model import DiseaseModelService
from app.services.recommender import RecommenderService
from app.services.personalization_engine import PersonalizationEngine


def test_symptom_model_service():
    service = SymptomModelService()
    predictions = service.predict("I have a headache and fever")
    assert isinstance(predictions, list)
    assert "disease" in predictions[0]
    assert "probability" in predictions[0]


def test_summary_model_service():
    service = SummaryModelService()
    summary = service.summarize("Patient has mild fever and fatigue. Blood tests normal.")
    assert isinstance(summary, str)
    assert len(summary) > 0


def test_disease_model_service():
    service = DiseaseModelService()
    risks = service.predict(symptoms="Persistent cough", age=30, gender="female")
    assert isinstance(risks, list)
    assert "disease" in risks[0]
    assert "probability" in risks[0]


def test_recommender_service():
    recommender = RecommenderService()
    risks = [{"disease": "diabetes", "probability": 0.8}]
    recommendations = recommender.get_recommendations(risks)
    assert isinstance(recommendations, dict)
    assert "diabetes" in recommendations


def test_personalization_engine():
    engine = PersonalizationEngine()
    success = engine.update_personalization("test_patient_1", {"weight_adjustment": 0.1})
    assert success is True
