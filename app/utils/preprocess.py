"""
Preprocessing utilities for AI Health Assistant

Includes:
- Text cleaning
- Medical abbreviation expansion
- Tokenization
- Symptom vectorization for AI models
- Spell correction (basic)
- Logging and error handling
"""

import re
import string
from typing import List, Dict, Optional
import logging

from app.utils.logger import log_debug, log_info, log_error, log_exceptions
from app.config import settings

# --------------------------
# Medical abbreviations dictionary
# --------------------------
MEDICAL_ABBREVIATIONS = {
    "bp": "blood pressure",
    "hr": "heart rate",
    "temp": "temperature",
    "c/o": "complains of",
    "h/o": "history of",
    "s/p": "status post",
    "dx": "diagnosis",
    "tx": "treatment",
    "sx": "symptoms"
    # Add more abbreviations as needed
}

# --------------------------
# Text cleaning and normalization
# --------------------------
@log_exceptions
def preprocess_text(text: str) -> str:
    """
    Clean and normalize input text.

    Args:
        text (str): Raw input text

    Returns:
        str: Cleaned and normalized text
    """
    if not text:
        return ""

    # Lowercase
    text = text.lower()

    # Expand medical abbreviations
    for abbr, full in MEDICAL_ABBREVIATIONS.items():
        text = re.sub(rf"\b{abbr}\b", full, text)

    # Remove URLs
    text = re.sub(r"http\S+|www\S+|https\S+", "", text)

    # Remove punctuation
    text = text.translate(str.maketrans("", "", string.punctuation))

    # Remove extra spaces
    text = re.sub(r"\s+", " ", text).strip()

    log_debug("Text preprocessed", original=text, cleaned=text)
    return text


# --------------------------
# Tokenization
# --------------------------
@log_exceptions
def tokenize_text(text: str) -> List[str]:
    """
    Tokenize text into words.

    Args:
        text (str): Preprocessed text

    Returns:
        List[str]: Tokens
    """
    text = preprocess_text(text)
    tokens = text.split()
    log_debug("Text tokenized", tokens=tokens)
    return tokens


# --------------------------
# Basic spell correction
# --------------------------
COMMON_MISSPELLINGS = {
    "feaver": "fever",
    "headake": "headache",
    "nausia": "nausea",
    "caugh": "cough"
    # Add more common misspellings
}

@log_exceptions
def correct_spelling(tokens: List[str]) -> List[str]:
    """
    Correct common misspellings.

    Args:
        tokens (List[str]): List of tokens

    Returns:
        List[str]: Tokens with corrected spelling
    """
    corrected = [COMMON_MISSPELLINGS.get(tok, tok) for tok in tokens]
    log_debug("Tokens spell-corrected", original=tokens, corrected=corrected)
    return corrected
# --------------------------
# Symptom vectorization (for AI models)
# --------------------------
import numpy as np

@log_exceptions
def vectorize_symptoms(tokens: List[str], embedding_model: Optional[object] = None) -> np.ndarray:
    """
    Convert symptom tokens into numerical feature vector for AI models.
    
    Args:
        tokens (List[str]): Tokenized and corrected symptoms
        embedding_model (Optional[object]): Pretrained embedding model (e.g., BioBERT, Word2Vec)
    
    Returns:
        np.ndarray: Numeric vector representation
    """
    if not tokens:
        return np.zeros(300)  # Default vector if empty

    # Placeholder: Using simple average of token lengths if no embedding provided
    if embedding_model is None:
        vector = np.array([len(tok)/10.0 for tok in tokens])
        log_debug("Vectorized symptoms using token length placeholder", tokens=tokens, vector=vector.tolist())
        return vector

    # If embedding model is provided
    try:
        embeddings = []
        for tok in tokens:
            if hasattr(embedding_model, 'get_vector'):  # e.g., Word2Vec
                emb = embedding_model.get_vector(tok)
            elif hasattr(embedding_model, 'encode'):  # e.g., HuggingFace model
                emb = embedding_model.encode(tok)
            else:
                emb = np.zeros(300)
            embeddings.append(emb)
        vector = np.mean(embeddings, axis=0)
        log_debug("Vectorized symptoms using embedding model", tokens=tokens, vector=vector.tolist())
        return vector
    except Exception as e:
        log_error("Error vectorizing symptoms", exc=e, tokens=tokens)
        return np.zeros(300)

# --------------------------
# Full pipeline: preprocess + tokenize + spell correct + vectorize
# --------------------------
@log_exceptions
def preprocess_pipeline(text: str, embedding_model: Optional[object] = None) -> np.ndarray:
    """
    Full preprocessing pipeline for symptom text:
    - Clean text
    - Tokenize
    - Correct spelling
    - Vectorize for AI models

    Args:
        text (str): Raw symptom text
        embedding_model (Optional[object]): Pretrained embedding model

    Returns:
        np.ndarray: Final symptom vector
    """
    tokens = tokenize_text(text)
    corrected_tokens = correct_spelling(tokens)
    vector = vectorize_symptoms(corrected_tokens, embedding_model=embedding_model)
    log_info("Preprocessing pipeline completed", text=text, tokens=corrected_tokens, vector_shape=vector.shape)
    return vector
