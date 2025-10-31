"""
Configuration module for AI Health Assistant

Handles environment variables, model paths, logging setup, and device configuration.
Designed for production-grade flexibility and maintainability.
"""

import os
from pathlib import Path
import logging
import sys

# --------------------------
# Base directories
# --------------------------
BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR.parent / "models"
PERSONALIZED_MODEL_DIR = MODEL_DIR / "personalized"
LOG_DIR = BASE_DIR.parent / "logs"

# Ensure necessary directories exist
for directory in [MODEL_DIR, PERSONALIZED_MODEL_DIR, LOG_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# --------------------------
# Model paths (pretrained)
# --------------------------
SYMPTOM_MODEL_PATH = MODEL_DIR / "pretrained" / "symptom_model.pt"
SUMMARY_MODEL_PATH = MODEL_DIR / "pretrained" / "summary_model.pt"
DISEASE_MODEL_PATH = MODEL_DIR / "pretrained" / "disease_model.pkl"

# --------------------------
# Device configuration
# --------------------------
USE_CUDA = os.getenv("USE_CUDA", "True").lower() == "true"
DEVICE = "cuda" if USE_CUDA else "cpu"

# --------------------------
# Logging configuration
# --------------------------
LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG").upper()
LOG_FILE = LOG_DIR / "ai_module.log"

def setup_logging():
    """
    Sets up production-grade logging with console and file handlers.
    """
    logger = logging.getLogger("ai_module")
    logger.setLevel(LOG_LEVEL)

    # Prevent duplicate handlers if setup_logging is called multiple times
    if not logger.handlers:
        # Console handler
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(LOG_LEVEL)
        ch_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        ch.setFormatter(ch_formatter)
        logger.addHandler(ch)

        # File handler
        fh = logging.FileHandler(LOG_FILE)
        fh.setLevel(LOG_LEVEL)
        fh_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        fh.setFormatter(fh_formatter)
        logger.addHandler(fh)

    return logger
# --------------------------
# External service configuration
# --------------------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", None)
EXTERNAL_EMBEDDING_SERVICE = os.getenv("EXTERNAL_EMBEDDING_SERVICE", "local")  # "openai" or "local"

# --------------------------
# Model parameters and defaults
# --------------------------
SYMPTOM_TOP_K = int(os.getenv("SYMPTOM_TOP_K", 5))
DISEASE_TOP_K = int(os.getenv("DISEASE_TOP_K", 5))
SUMMARY_MAX_TOKENS = int(os.getenv("SUMMARY_MAX_TOKENS", 512))

# --------------------------
# Personalization settings
# --------------------------
PERSONALIZATION_BASE_DIR = PERSONALIZED_MODEL_DIR
PERSONALIZATION_HISTORY_FILENAME = "history.csv"
PERSONALIZATION_WEIGHTS_FILENAME = "weights.json"

# --------------------------
# Settings class for central access
# --------------------------
class Settings:
    """
    Centralized settings object for AI Health Assistant.
    Provides all paths, device info, and model parameters.
    """

    def __init__(self):
        # Directories
        self.base_dir = BASE_DIR
        self.model_dir = MODEL_DIR
        self.personalized_model_dir = PERSONALIZED_MODEL_DIR
        self.log_dir = LOG_DIR

        # Model paths
        self.symptom_model_path = SYMPTOM_MODEL_PATH
        self.summary_model_path = SUMMARY_MODEL_PATH
        self.disease_model_path = DISEASE_MODEL_PATH

        # Device
        self.use_cuda = USE_CUDA
        self.device = DEVICE

        # Logging
        self.log_level = LOG_LEVEL
        self.log_file = LOG_FILE
        self.logger = setup_logging()

        # External services
        self.openai_api_key = OPENAI_API_KEY
        self.external_embedding_service = EXTERNAL_EMBEDDING_SERVICE

        # Model parameters
        self.symptom_top_k = SYMPTOM_TOP_K
        self.disease_top_k = DISEASE_TOP_K
        self.summary_max_tokens = SUMMARY_MAX_TOKENS

        # Personalization
        self.personalization_base_dir = PERSONALIZATION_BASE_DIR
        self.personalization_history_filename = PERSONALIZATION_HISTORY_FILENAME
        self.personalization_weights_filename = PERSONALIZATION_WEIGHTS_FILENAME

        # Display settings at initialization
        self.logger.info(f"Settings initialized. Device={self.device}, Log File={self.log_file}")

# Instantiate settings for import across modules
settings = Settings()
