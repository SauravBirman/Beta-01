"""
Logger Utility for AI Health Assistant

Provides production-grade logging with:
- Console logging
- File logging with rotation
- Optional structured logs (JSON)
- Integration with settings from config.py
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
import json
from app.config import settings


class JsonFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logs
    """
    def format(self, record):
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "name": record.name,
            "level": record.levelname,
            "message": record.getMessage(),
            "filename": record.filename,
            "lineno": record.lineno
        }
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_record)


def setup_logger(name: str = "ai_module", json_format: bool = False, max_bytes: int = 10*1024*1024, backup_count: int = 5):
    """
    Setup a logger with console and rotating file handlers.
    
    Args:
        name (str): Logger name
        json_format (bool): Whether to use JSON structured logging
        max_bytes (int): Max file size before rotation
        backup_count (int): Number of backup files
    Returns:
        logging.Logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(settings.log_level)

    if logger.hasHandlers():
        # Avoid duplicate handlers
        logger.handlers.clear()

    # ----------------------------
    # Console Handler
    # ----------------------------
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(settings.log_level)
    if json_format:
        ch.setFormatter(JsonFormatter())
    else:
        ch.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    logger.addHandler(ch)

    # ----------------------------
    # Rotating File Handler
    # ----------------------------
    fh = RotatingFileHandler(
        filename=settings.log_file,
        maxBytes=max_bytes,
        backupCount=backup_count
    )
    fh.setLevel(settings.log_level)
    if json_format:
        fh.setFormatter(JsonFormatter())
    else:
        fh.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    logger.addHandler(fh)

    logger.debug(f"Logger '{name}' initialized. JSON format={json_format}, File={settings.log_file}")
    return logger
# ----------------------------
# Helper logging functions
# ----------------------------

_logger = setup_logger(name="ai_module", json_format=False)  # Default logger

def log_debug(message: str, **kwargs):
    """Log a debug message with optional extra context."""
    if kwargs:
        _logger.debug(f"{message} | Context: {kwargs}")
    else:
        _logger.debug(message)

def log_info(message: str, **kwargs):
    """Log an info message with optional extra context."""
    if kwargs:
        _logger.info(f"{message} | Context: {kwargs}")
    else:
        _logger.info(message)

def log_warning(message: str, **kwargs):
    """Log a warning message with optional extra context."""
    if kwargs:
        _logger.warning(f"{message} | Context: {kwargs}")
    else:
        _logger.warning(message)

def log_error(message: str, exc: Exception = None, **kwargs):
    """Log an error message with exception info and optional context."""
    if exc:
        if kwargs:
            _logger.error(f"{message} | Context: {kwargs}", exc_info=exc)
        else:
            _logger.error(message, exc_info=exc)
    else:
        if kwargs:
            _logger.error(f"{message} | Context: {kwargs}")
        else:
            _logger.error(message)

# ----------------------------
# Exception logging decorator
# ----------------------------
def log_exceptions(func):
    """
    Decorator to log exceptions in a function and re-raise them.
    Usage:
        @log_exceptions
        def some_function(...):
            ...
    """
    import functools

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            log_error(f"Exception in {func.__name__}", exc=e, args=args, kwargs=kwargs)
            raise
    return wrapper
