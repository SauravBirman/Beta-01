import pytest
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services import (
    symptom_model,
    summary_model,
    disease_model,
    recommender,
    personalization_engine,
    history_engine,
    image_model,
    fusion_layer
)


# -------------------------------------------------------
# Symptom Model Tests
# -------------------------------------------------------
def test_symptom_model_prediction_structure():
    symptoms = ["fever", "cough", "fatigue"]
    result = symptom_model.analyze_symptoms(symptoms)
    assert isinstance(result, dict)
    assert "conditions" in result
    assert isinstance(result["conditions"], list)
    for cond in result["conditions"]:
        assert "name" in cond and "score" in cond


def test_symptom_model_empty_input():
    result = symptom_model.analyze_symptoms([])
    assert result == {"conditions": []}


# -------------------------------------------------------
# Summary Model Tests
# -------------------------------------------------------
def test_summary_model_generate_summary():
    report_text = """
        Patient reports persistent fever and sore throat for three days.
        CBC indicates elevated WBC count.
    """
    summary = summary_model.generate_summary(report_text)
    assert isinstance(summary, str)
    assert len(summary) > 10
    assert "fever" in summary.lower()


def test_summary_model_handles_short_text():
    report_text = "Normal"
    summary = summary_model.generate_summary(report_text)
    assert isinstance(summary, str)
    assert len(summary) > 0


# -------------------------------------------------------
# Disease Model Tests
# -------------------------------------------------------
def test_disease_model_predict_risk_structure():
    patient_data = {
        "age": 45,
        "symptoms": ["fever", "cough"],
        "bp": 130,
        "cholesterol": 200
    }
    prediction = disease_model.predict_disease_risk(patient_data)
    assert isinstance(prediction, dict)
    assert "risk_score" in prediction
    assert "disease" in prediction
    assert isinstance(prediction["risk_score"], float)


def test_disease_model_invalid_input():
    result = disease_model.predict_disease_risk(None)
    assert isinstance(result, dict)
    assert "risk_score" in result


# -------------------------------------------------------
# Recommender Model Tests
# -------------------------------------------------------
def test_recommender_generate_recommendations():
    profile = {"age": 30, "bmi": 25, "activity_level": "moderate"}
    recs = recommender.generate_recommendations(profile)
    assert isinstance(recs, dict)
    assert "lifestyle" in recs
    assert "diet" in recs
    assert isinstance(recs["lifestyle"], list)
    assert isinstance(recs["diet"], list)


def test_recommender_empty_profile():
    recs = recommender.generate_recommendations({})
    assert "lifestyle" in recs
    assert "diet" in recs


# -------------------------------------------------------
# Personalization Engine Tests
# -------------------------------------------------------
def test_personalization_engine_weight_update(tmp_path):
    patient_id = "test_123"
    history = [{"feature": "fever", "weight": 0.8}]
    result = personalization_engine.update_patient_weights(patient_id, history)
    assert isinstance(result, dict)
    assert "patient_id" in result
    assert result["patient_id"] == patient_id
    assert "updated_weights" in result


def test_personalization_engine_merge_strategy():
    weights_a = {"fever": 0.7, "cough": 0.5}
    weights_b = {"fever": 0.9, "fatigue": 0.8}
    merged = personalization_engine.merge_weights(weights_a, weights_b)
    assert isinstance(merged, dict)
    assert "fever" in merged
    assert merged["fever"] >= 0.7


# -------------------------------------------------------
# History Engine Tests
# -------------------------------------------------------
def test_history_engine_record_and_retrieve(tmp_path):
    patient_id = "p_test"
    record = {"action": "predict", "timestamp": "2025-11-01T00:00:00Z"}
    result = history_engine.append_history(patient_id, record)
    assert result is True
    retrieved = history_engine.get_history(patient_id)
    assert isinstance(retrieved, list)
    assert any("action" in r for r in retrieved)


# -------------------------------------------------------
# Image Model Tests
# -------------------------------------------------------
def test_image_model_embedding_generation(tmp_path):
    fake_image_path = tmp_path / "fake.jpg"
    fake_image_path.write_bytes(b"\x00\x01\x02")  # minimal mock binary
    embedding = image_model.extract_features(str(fake_image_path))
    assert isinstance(embedding, list)
    assert all(isinstance(x, float) for x in embedding)
    assert len(embedding) > 16


# -------------------------------------------------------
# Fusion Layer Tests
# -------------------------------------------------------
def test_fusion_layer_combines_modalities():
    symptom_data = {"conditions": [{"name": "flu", "score": 0.9}]}
    report_data = {"summary_text": "Possible flu infection."}
    image_data = [0.2, 0.5, 0.3]
    fused = fusion_layer.combine_modalities(symptom_data, report_data, image_data)
    assert isinstance(fused, dict)
    assert "final_confidence" in fused
    assert "explanation" in fused
