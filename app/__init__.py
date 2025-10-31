"""
ai_module.app
Package initialization for the FastAPI application.
Sets package-level logger and exposes a factory to create the app instance
for importing by uvicorn or tests.
"""

from .main import create_app  # re-export factory for convenience

__all__ = ("create_app",)
