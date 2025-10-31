"""
FastAPI application entrypoint and app factory.

This module creates and configures the FastAPI app, registers routers,
adds middleware, configures logging, and loads models lazily.

Usage:
    # for development
    uvicorn app.main:app --reload

    # or when using as module
    from app.main import create_app
    app = create_app()
"""

import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Callable, Optional

from .config import settings
from .utils.logger import setup_logging

# List of routers to include
ROUTERS = [
    ("app.routes.analyze", "router"),
    ("app.routes.summarize", "router"),
    ("app.routes.predict", "router"),
    ("app.routes.personalization", "router"),
]

def _import_router(module_path: str):
    """Dynamic import helper for routers to avoid circular imports."""
    import importlib
    module = importlib.import_module(module_path)
    return getattr(module, "router")

def create_app(debug: Optional[bool] = None) -> FastAPI:
    """Application factory.

    Args:
        debug: override settings.DEBUG if provided.

    Returns:
        configured FastAPI app
    """
    debug = settings.DEBUG if debug is None else debug

    # Setup logging first
    setup_logging(debug=debug)
    logger = logging.getLogger("ai_module")

    app = FastAPI(
        title="AI Health Assistant",
        description="APIs for symptom analysis, report summarization, disease risk prediction, and personalization.",
        version="0.1.0",
        debug=debug,
    )

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request logging middleware
    @app.middleware("http")
    async def logging_middleware(request: Request, call_next: Callable):
        logger.info(f"Incoming request: {request.method} {request.url.path}")
        try:
            response = await call_next(request)
        except Exception as exc:
            logger.exception("Unhandled exception in request handling")
            raise
        logger.info(f"Completed request: {request.method} {request.url.path} -> {response.status_code}")
        return response

    # Register routers dynamically
    for router_module, attr in [(r[0], r[1]) for r in ROUTERS]:
        try:
            router = _import_router(router_module)
            app.include_router(router)
            logger.debug(f"Included router from {router_module}")
        except Exception as e:
            logger.exception(f"Failed to include router {router_module}: {e}")

    # Health check endpoint
    @app.get("/health", tags=["health"])
    async def health():
        return {"status": "ok", "version": app.version}

    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.exception(f"Unhandled error for request {request.method} {request.url}")
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )

    # Startup event
    @app.on_event("startup")
    async def on_startup():
        logger.info("Application startup: loading lightweight resources")

    # Shutdown event
    @app.on_event("shutdown")
    async def on_shutdown():
        logger.info("Application shutdown: releasing resources")

    return app

# Default app instance for uvicorn
app = create_app()
