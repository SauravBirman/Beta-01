# app/config.py
"""
Central configuration for AI Health Assistant ML module.

- Uses pydantic.BaseSettings to allow environment variable overrides.
- Validates paths and provides convenient property access for model locations.
- Includes toggles for local vs remote storage (S3/IPFS) and runtime tuning knobs.
"""

from pydantic_settings import BaseSettings

from pydantic import Field, AnyUrl, validator
from pathlib import Path
from typing import Optional, Dict, Any
import os

class Settings(BaseSettings):
    # General
    APP_NAME: str = "AI Health Assistant - ML Module"
    ENV: str = Field("development", description="Environment: development|staging|production")
    DEBUG: bool = Field(True, description="Enable debug logging and model hot-reload (dev only)")
    LOG_LEVEL: str = Field("INFO")
    LOG_FORMAT: str = Field("text", description="Logging format: text | json")

    # Directories
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    MODELS_DIR: Path = Field(default_factory=lambda: Path(__file__).resolve().parent.parent / "models")
    PRETRAINED_DIR: Path = Field(default_factory=lambda: Path(__file__).resolve().parent.parent / "models" / "pretrained")
    PERSONALIZED_DIR: Path = Field(default_factory=lambda: Path(__file__).resolve().parent.parent / "models" / "personalized")
    DATA_DIR: Path = Field(default_factory=lambda: Path(__file__).resolve().parent.parent / "data")
    TEXT_EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    # Model filenames (default names; can be overridden via env)
    SYMPTOM_MODEL_NAME: str = Field("symptom_model.pt")
    SUMMARY_MODEL_NAME: str = Field("summary_model.pt")
    DISEASE_MODEL_NAME: str = Field("disease_model.pkl")
    IMAGE_MODEL_NAME: str = Field("image_model.pt")
    HISTORY_ENGINE_NAME: str = Field("history_engine.pkl")
    FUSION_LAYER_NAME: str = Field("fusion_layer.pkl")
    # Model full paths (computed properties)
    @property
    def SYMPTOM_MODEL_PATH(self) -> Path:
        return self.PRETRAINED_DIR / self.SYMPTOM_MODEL_NAME

    @property
    def SUMMARY_MODEL_PATH(self) -> Path:
        return self.PRETRAINED_DIR / self.SUMMARY_MODEL_NAME

    @property
    def DISEASE_MODEL_PATH(self) -> Path:
        return self.PRETRAINED_DIR / self.DISEASE_MODEL_NAME
    @property
    def IMAGE_MODEL_PATH(self) -> Path:
        return self.PRETRAINED_DIR / self.IMAGE_MODEL_NAME

    @property
    def HISTORY_ENGINE_PATH(self) -> Path:
        return self.PRETRAINED_DIR / self.HISTORY_ENGINE_NAME

    @property
    def FUSION_LAYER_PATH(self) -> Path:
        return self.PRETRAINED_DIR / self.FUSION_LAYER_NAME
    # Fusion & personalization defaults
    DEFAULT_WEIGHTS: Dict[str, float] = Field(
        default_factory=lambda: {"tabular": 0.5, "text": 0.3, "image": 0.2},
        description="Default modality weights for deterministic fusion"
    )
    # Fusion layer configuration
    FUSION_STRATEGY: str = Field(
        "weighted",
        description="Fusion method: weighted | attention | learned"
    )
    WEIGHT_TUNING_ENABLED: bool = Field(True, description="Allow dynamic weight adjustment during inference")

    # Runtime & concurrency
    MAX_WORKERS: int = Field(4, description="Max threadpool workers for CPU-bound inference tasks")
    INFERENCE_TIMEOUT_SEC: int = Field(30, description="Inference timeout per request")
        # History engine configuration
    HISTORY_RETENTION_DAYS: int = Field(180, description="Days to retain patient history")
    HISTORY_USE_PREVIOUS_REPORTS: bool = Field(True)
    HISTORY_EMBEDDING_DIM: int = Field(256)
    HISTORY_CACHE_DIR: Path = Field(default_factory=lambda: Path(__file__).resolve().parent.parent / "data" / "history_cache")

    # Image model configuration
    IMAGE_INPUT_SIZE: int = Field(224, description="Expected image input size")
    IMAGE_NORMALIZATION: str = Field("imagenet", description="Normalization: imagenet | custom")
    IMAGE_EMBEDDING_DIM: int = Field(512)

    # Storage options (local vs S3/IPFS)
    STORAGE_BACKEND: str = Field("local", description="local | s3 | ipfs")
    # S3 placeholders
    S3_ENDPOINT: Optional[str] = None
    S3_BUCKET: Optional[str] = None
    S3_REGION: Optional[str] = None
    # IPFS placeholders
    IPFS_API_URL: Optional[AnyUrl] = None

    # Security / keys (do not store secrets in repo; use env in production)
    AES_ENCRYPTION_KEY: Optional[str] = Field(None, description="Base64 AES key for client-side encryption (if used)")
    JWT_SECRET: Optional[str] = Field(None, description="JWT secret for signing tokens (set in env for prod)")

    # Model serving metadata (versions)
    MODEL_METADATA: Dict[str, Any] = Field(default_factory=lambda: {
    "symptom_model": {"version": "0.1.0", "framework": "pytorch"},
    "summary_model": {"version": "0.1.0", "framework": "pytorch"},
    "disease_model": {"version": "0.1.0", "framework": "sklearn"},
    "image_model": {"version": "0.1.0", "framework": "torchvision"},
    "history_engine": {"version": "0.1.0", "framework": "sklearn"},
    "fusion_layer": {"version": "0.1.0", "framework": "torch or sklearn hybrid"}
})


    # Misc
    ALLOWED_UPLOAD_TYPES: str = Field("application/json,text/plain,image/jpeg,image/png,application/pdf")
    MAX_UPLOAD_SIZE_BYTES: int = Field(5 * 1024 * 1024)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    # Validators to ensure directories exist
    @validator("PRETRAINED_DIR", "PERSONALIZED_DIR", "DATA_DIR", "HISTORY_CACHE_DIR", pre=True, always=True)
    def ensure_paths(cls, v):
        path = Path(v)
        try:
            path.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
        return path


    @validator("STORAGE_BACKEND")
    def check_storage_backend(cls, v):
        if v not in ("local", "s3", "ipfs"):
            raise ValueError("STORAGE_BACKEND must be one of ['local','s3','ipfs']")
        return v

# Singleton settings instance
settings = Settings()

# Convenience exports for older code that imports variables
BASE_DIR = settings.BASE_DIR
MODELS_DIR = settings.MODELS_DIR
PRETRAINED_DIR = settings.PRETRAINED_DIR
PERSONALIZED_DIR = settings.PERSONALIZED_DIR
DATA_DIR = settings.DATA_DIR
DEFAULT_WEIGHTS = settings.DEFAULT_WEIGHTS
MAX_WORKERS = settings.MAX_WORKERS
INFERENCE_TIMEOUT_SEC = settings.INFERENCE_TIMEOUT_SEC
SYMPTOM_MODEL_PATH = settings.SYMPTOM_MODEL_PATH
SUMMARY_MODEL_PATH = settings.SUMMARY_MODEL_PATH
DISEASE_MODEL_PATH = settings.DISEASE_MODEL_PATH
MODEL_METADATA = settings.MODEL_METADATA
STORAGE_BACKEND = settings.STORAGE_BACKEND
IMAGE_MODEL_PATH = settings.IMAGE_MODEL_PATH
HISTORY_ENGINE_PATH = settings.HISTORY_ENGINE_PATH
FUSION_LAYER_PATH = settings.FUSION_LAYER_PATH
