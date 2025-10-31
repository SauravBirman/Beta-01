"""
Tests for utility functions: preprocess and postprocess
"""

import pytest
from app.utils import preprocess, postprocess


def test_preprocess_text():
    raw_text = "Hello World! Visit https://example.com"
    cleaned = preprocess.preprocess_text(raw_text)
    assert "http" not in cleaned
    assert "!" not in cleaned
    assert cleaned == "hello world visit"


def test_tokenize_text():
    text = "Fever and cough"
    tokens = preprocess.tokenize_text(text)
    assert isinstance(tokens, list)
    assert tokens == ["fever", "and", "cough"]


def test_vectorize_symptoms():
    text = "Headache and nausea"
    vector = preprocess.vectorize_symptoms(text)
    assert isinstance(vector, list)
    assert all(isinstance(v, float) for v in vector)


def test_format_symptom_output():
    raw_predictions = [{"disease": "flu", "probability": 0.85732}]
    formatted = postprocess.format_symptom_output(raw_predictions)
    assert formatted[0]["probability"] == 0.8573


def test_format_summary_output():
    summary = "  This is a test summary.  "
    formatted = postprocess.format_summary_output(summary)
    assert formatted == "This is a test summary."


def test_format_disease_output():
    raw_risks = [{"disease": "cold", "probability": 0.65432}]
    formatted = postprocess.format_disease_output(raw_risks)
    assert formatted[0]["probability"] == 0.6543
