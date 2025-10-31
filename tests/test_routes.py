"""
Tests for FastAPI routes
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app  # FastAPI app entry point

client = TestClient(app)


def test_analyze_symptoms():
    payload = {
        "patient_id": "test_patient_1",
        "symptoms": "I have a headache and mild fever"
    }
    response = client.post("/analyze-symptoms/", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "patient_id" in data
    assert "predictions" in data
    assert isinstance(data["predictions"], list)


def test_summarize_report():
    payload = {
        "patient_id": "test_patient_1",
        "report_text": "Patient shows signs of fatigue and mild fever. Blood tests are normal."
    }
    response = client.post("/summarize-report/", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert isinstance(data["summary"], str)


def test_predict_risk():
    payload = {
        "patient_id": "test_patient_1",
        "symptoms": "Persistent cough and shortness of breath",
        "age": 45,
        "gender": "male"
    }
    response = client.post("/predict-risk/", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "risks" in data
    assert isinstance(data["risks"], list)


def test_personalization():
    payload = {
        "patient_id": "test_patient_1",
        "preferences": {"weight_adjustment": 0.1}
    }
    response = client.post("/personalization/", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "success"
