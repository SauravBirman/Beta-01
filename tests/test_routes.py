import pytest
from fastapi.testclient import TestClient
from pydantic import BaseModel, ValidationError
from app.main import app
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# ---------------------------------------------------------------------
# ✅ Fixtures
# ---------------------------------------------------------------------

@pytest.fixture(scope="module")
def client():
    """Create a single FastAPI TestClient instance for all tests."""
    return TestClient(app)


# ---------------------------------------------------------------------
# ✅ Response Schemas for Validation
# ---------------------------------------------------------------------

class AnalyzeResponse(BaseModel):
    analysis: dict
    confidence: float


class SummaryResponse(BaseModel):
    summary: str
    key_findings: list


class PredictionResponse(BaseModel):
    risk_score: float
    probable_conditions: list


class PersonalizationResponse(BaseModel):
    status: str
    details: dict


# ---------------------------------------------------------------------
# ✅ /analyze-symptoms Endpoint Tests
# ---------------------------------------------------------------------

def test_analyze_symptoms_valid(client):
    payload = {"symptoms": ["headache", "fatigue", "nausea"]}
    response = client.post("/analyze-symptoms", json=payload)
    assert response.status_code == 200
    try:
        AnalyzeResponse(**response.json())
    except ValidationError:
        pytest.fail("Response schema validation failed for /analyze-symptoms")


def test_analyze_symptoms_invalid(client):
    payload = {"invalid_key": ["abc"]}
    response = client.post("/analyze-symptoms", json=payload)
    assert response.status_code in [400, 422]


# ---------------------------------------------------------------------
# ✅ /summarize-report Endpoint Tests
# ---------------------------------------------------------------------

def test_summarize_report_valid(client):
    payload = {"report_text": "Patient has high fever and mild cough."}
    response = client.post("/summarize-report", json=payload)
    assert response.status_code == 200
    try:
        SummaryResponse(**response.json())
    except ValidationError:
        pytest.fail("Response schema validation failed for /summarize-report")
    assert response.elapsed.total_seconds() < 2  # performance check


def test_summarize_report_invalid(client):
    response = client.post("/summarize-report", json={})
    assert response.status_code in [400, 422]


# ---------------------------------------------------------------------
# ✅ /predict-risk Endpoint Tests
# ---------------------------------------------------------------------

def test_predict_risk_valid(client):
    payload = {"features": {"age": 45, "bmi": 24.3, "cholesterol": 210}}
    response = client.post("/predict-risk", json=payload)
    assert response.status_code == 200
    try:
        PredictionResponse(**response.json())
    except ValidationError:
        pytest.fail("Response schema validation failed for /predict-risk")


def test_predict_risk_invalid(client):
    response = client.post("/predict-risk", json={})
    assert response.status_code in [400, 422]


# ---------------------------------------------------------------------
# ✅ /personalize/<patient_id> Endpoints Tests
# ---------------------------------------------------------------------

@pytest.mark.parametrize("patient_id", ["p001", "p002"])
def test_personalize_get(client, patient_id):
    response = client.get(f"/personalize/{patient_id}")
    assert response.status_code in [200, 404]
    if response.status_code == 200:
        try:
            PersonalizationResponse(**response.json())
        except ValidationError:
            pytest.fail("Response schema validation failed for /personalize GET")


@pytest.mark.parametrize("patient_id", ["p001"])
def test_personalize_update(client, patient_id):
    payload = {"preferences": {"diet": "low sugar", "exercise": "yoga"}}
    response = client.put(f"/personalize/{patient_id}", json=payload)
    assert response.status_code in [200, 400]
    if response.status_code == 200:
        try:
            PersonalizationResponse(**response.json())
        except ValidationError:
            pytest.fail("Response schema validation failed for /personalize PUT")


# ---------------------------------------------------------------------
# ✅ Health check and generic performance tests
# ---------------------------------------------------------------------

def test_health_check(client):
    """Ensure that the base API is responsive."""
    response = client.get("/")
    assert response.status_code in [200, 404]
    assert response.elapsed.total_seconds() < 1


# ---------------------------------------------------------------------
# ✅ Placeholder for Future Endpoints (to be implemented later)
# ---------------------------------------------------------------------

@pytest.mark.skip(reason="Fusion endpoint not implemented yet")
def test_fusion_endpoint(client):
    response = client.post("/fusion", json={"inputs": ["symptoms", "report"]})
    assert response.status_code == 200


@pytest.mark.skip(reason="Image analysis endpoint not implemented yet")
def test_image_analysis_endpoint(client):
    files = {"image": ("scan.png", b"dummybytes", "image/png")}
    response = client.post("/image-analysis", files=files)
    assert response.status_code == 200


@pytest.mark.skip(reason="History endpoint not implemented yet")
def test_history_endpoint(client):
    response = client.get("/history/p001")
    assert response.status_code in [200, 404]
