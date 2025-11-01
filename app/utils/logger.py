import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime
import json
from pathlib import Path

from app.config import settings


class JsonFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging.
    Useful for cloud logging (e.g., AWS CloudWatch, ELK stack).
    """

    def format(self, record):
        log_record = {
    "timestamp": datetime.utcnow().isoformat() + "Z",
    "level": record.levelname,
    "module": record.module,
    "function": record.funcName,
    "message": record.getMessage(),
    "patient_id": getattr(record, "patient_id", None),
    "request_id": getattr(record, "request_id", None),
}



        # Add exception info if present
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_record)

class ContextFilter(logging.Filter):
    """
    Injects contextual information (like patient_id or request_id) into all log records.
    This allows tracking per-user or per-request behavior across services.
    """
    def __init__(self, patient_id=None, request_id=None):
        super().__init__()
        self.patient_id = patient_id
        self.request_id = request_id

    def filter(self, record):
        record.patient_id = getattr(record, "patient_id", self.patient_id)
        record.request_id = getattr(record, "request_id", self.request_id)
        return True

def _ensure_log_directory_exists(log_path: str):
    """Ensure the log directory exists before writing log files."""
    log_dir = Path(log_path).parent
    if not log_dir.exists():
        log_dir.mkdir(parents=True, exist_ok=True)


def setup_logger():
    """
    Configure the root logger based on environment variables.

    - Console logging (colored) for development
    - Rotating file logging for production
    - JSON log option for structured logging
    """

    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    log_format = settings.LOG_FORMAT.lower()

    logger = logging.getLogger()
    logger.setLevel(log_level)
    # Attach context filter for patient/request tracing
    context_filter = ContextFilter()
    logger.addFilter(context_filter)

    # Remove existing handlers to avoid duplication
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # ---- Console Handler (Always On) ----
    console_handler = logging.StreamHandler()
    if log_format == "json":
        console_handler.setFormatter(JsonFormatter())
    else:
        console_formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        console_handler.setFormatter(console_formatter)

    logger.addHandler(console_handler)

    # ---- File Handler (Production Only) ----
    if not settings.DEBUG:
        _ensure_log_directory_exists(settings.LOG_FILE_PATH)
        file_handler = RotatingFileHandler(
            filename=settings.LOG_FILE_PATH,
            mode="a",
            maxBytes=5 * 1024 * 1024,  # 5 MB per log file
            backupCount=5,
            encoding="utf-8",
        )

        if log_format == "json":
            file_handler.setFormatter(JsonFormatter())
        else:
            file_formatter = logging.Formatter(
                fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            file_handler.setFormatter(file_formatter)

        logger.addHandler(file_handler)

    logger.info("Logger initialized successfully with level: %s", settings.LOG_LEVEL)
    # Optional remote streaming (future use)
    if getattr(settings, "ENABLE_REMOTE_LOGGING", False):
        try:
            logger.info("Remote logging enabled (placeholder). Future: push to blockchain/cloud.")
        except Exception as e:
            logger.warning("Remote logging setup failed: %s", e)

    return logger


def get_logger(name: str = None) -> logging.Logger:
    """
    Get a module-specific logger. Ensures consistent configuration across modules.
    Example:
        logger = get_logger(__name__)
        logger.info("Symptom analysis started")
    """
    return logging.getLogger(name or "ai_module")


# Initialize global logger at import time
logger = setup_logger()


# --- Example usage (can be removed in prod) ---
if __name__ == "__main__":
    log = get_logger(__name__)
    log.info("Logger test: info message")
    log.warning("Logger test: warning message")
    try:
        raise ValueError("Sample exception for test")
    except Exception:
        log.exception("Exception occurred")
