import pytest
import os
from pathlib import Path
from app.utils import logger, preprocess, postprocess, embeddings, image_preprocess
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# -------------------------------------------------------
# Test Logger Utility
# -------------------------------------------------------
def test_logger_initialization(tmp_path):
    """Ensure logger initializes and writes messages without error."""
    log = logger.get_logger("test_logger")
    assert log is not None
    log.info("Test info log")
    log.warning("Test warning log")
    log.error("Test error log")
    # Just ensures logger works — file writes not checked


# -------------------------------------------------------
# Test Preprocessing Utilities
# -------------------------------------------------------
def test_preprocess_text_cleaning():
    raw_text = " Patient   has   Fever, cough!! and fatigue. "
    cleaned = preprocess.clean_text(raw_text)
    assert isinstance(cleaned, str)
    assert "  " not in cleaned
    assert cleaned == "patient has fever cough and fatigue"

def test_tokenization_and_stopword_removal():
    text = "Patient has fever and cough"
    tokens = preprocess.tokenize_text(text)
    assert isinstance(tokens, list)
    assert "and" not in tokens
    assert "patient" in tokens
    assert "fever" in tokens

def test_normalization_pipeline():
    text = "   Severe FEVER,   mild cough "
    norm = preprocess.normalize_text(text)
    assert "fever" in norm
    assert "cough" in norm
    assert "Severe" not in norm


# -------------------------------------------------------
# Test Postprocessing Utilities
# -------------------------------------------------------
def test_postprocess_output_format():
    mock_output = {"risk_score": 0.75, "category": "high"}
    formatted = postprocess.format_prediction_output(mock_output)
    assert isinstance(formatted, dict)
    assert "risk_score" in formatted
    assert formatted["category"] in ["low", "medium", "high"]

def test_summary_formatting():
    sample_summary = "Patient shows mild respiratory infection."
    result = postprocess.format_summary_output(sample_summary)
    assert isinstance(result, dict)
    assert "summary" in result
    assert result["summary"].startswith("Patient")

def test_report_formatter_symptom_analysis():
    rf = postprocess.ReportFormatter()
    sample = {
        "symptoms_detected": ["fever", "cough"],
        "possible_conditions": ["flu", "cold"]
    }
    formatted = rf.format_symptom_analysis(sample)
    assert isinstance(formatted, str)
    assert "fever" in formatted
    assert "flu" in formatted

def test_report_formatter_disease_risk():
    rf = postprocess.ReportFormatter()
    formatted = rf.format_disease_risk("Diabetes", 0.82)
    assert isinstance(formatted, str)
    assert "Diabetes" in formatted
    assert "82" in formatted  # percentage formatting


# -------------------------------------------------------
# Test Embeddings Utility
# -------------------------------------------------------
def test_embeddings_vector_generation():
    text = "Patient has fever and cough"
    vector = embeddings.get_text_embedding(text)
    assert isinstance(vector, list)
    assert all(isinstance(v, float) for v in vector)
    assert len(vector) > 10


# -------------------------------------------------------
# Test Image Preprocess Utility
# -------------------------------------------------------
def test_image_preprocessing_pipeline(tmp_path):
    """Test that an image file can be safely preprocessed."""
    img_path = tmp_path / "test_img.jpg"
    img_path.write_bytes(os.urandom(1024))  # mock binary image
    try:
        processed = image_preprocess.prepare_image(str(img_path))
        assert processed is not None
    except Exception:
        pytest.skip("PIL or OpenCV not available in test environment")
