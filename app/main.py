from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import time
import uuid

from .config import settings
from .utils.logger import get_logger

# Import all routers
from .routes import (
    analyze,
    summarize,
    predict,
    personalization,
    history,            # ✅ NEW
    image_analysis,     # ✅ NEW
    fusion              # ✅ NEW
)

# Initialize app and logger
app = FastAPI(
    title="AI Health Assistant",
    description=(
        "Advanced AI backend for symptom analysis, report summarization, "
        "disease prediction, preventive care, and patient-specific personalization."
    ),
    version="2.0.0"
)

logger = get_logger(__name__)

# --------------------------
# CORS Configuration
# --------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS if hasattr(settings, "ALLOWED_ORIGINS") else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------
# Middleware: Request Tracing + Timing
# --------------------------
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Logs incoming requests with unique request ID, duration, and status.
    """
    request_id = str(uuid.uuid4())
    start_time = time.time()

    logger.info(f"➡️ Request Start | ID={request_id} | {request.method} {request.url.path}")

    try:
        response: Response = await call_next(request)
    except Exception as e:
        logger.exception(f"❌ Request Failed | ID={request_id} | Error={str(e)}")
        return Response(
            content=f"Internal server error | request_id={request_id}",
            status_code=500
        )

    process_time = time.time() - start_time
    logger.info(
        f"✅ Request Complete | ID={request_id} | Status={response.status_code} | "
        f"Time={process_time:.3f}s"
    )
    response.headers["X-Process-Time"] = str(process_time)
    response.headers["X-Request-ID"] = request_id
    return response


# --------------------------
# Startup Event
# --------------------------
@app.on_event("startup")
async def startup_event():
    """
    Load all required models and initialize services at startup.
    """
    logger.info("🚀 Starting AI Health Assistant backend...")

    try:
        from .services import (
            symptom_model,
            summary_model,
            disease_model,
            recommender,
            personalization_engine,
            image_model,        # ✅ NEW
            fusion_layer,       # ✅ NEW
            history_engine      # ✅ NEW
        )

        # Load all core models
        symptom_model.load_model(settings.SYMPTOM_MODEL_PATH)
        summary_model.load_model(settings.SUMMARY_MODEL_PATH)
        disease_model.load_model(settings.DISEASE_MODEL_PATH)

        # Initialize recommender & personalization
        recommender.init_engine()
        personalization_engine.initialize()

        # ✅ NEW: Load image and fusion modules
        image_model.get_default_image_model()
        fusion_layer.initialize()
        history_engine.initialize()

        logger.info("✅ All AI modules initialized successfully.")
    except Exception as e:
        logger.exception(f"❌ Startup failed: {str(e)}")


# --------------------------
# Shutdown Event
# --------------------------
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🧩 Shutting down AI backend gracefully...")
    try:
        from .services import personalization_engine
        personalization_engine.cleanup()
        logger.info("✅ Cleanup completed successfully.")
    except Exception as e:
        logger.warning(f"⚠️ Cleanup encountered an issue: {e}")


# --------------------------
# Register API Routers
# --------------------------
app.include_router(analyze.router, prefix="/analyze-symptoms", tags=["Symptom Analysis"])
app.include_router(summarize.router, prefix="/summarize-report", tags=["Report Summarization"])
app.include_router(predict.router, prefix="/predict-risk", tags=["Disease Prediction"])
app.include_router(personalization.router, prefix="/personalization", tags=["Personalization Engine"])
app.include_router(history.router, prefix="/patient-history", tags=["Patient History"])         # ✅ NEW
app.include_router(image_analysis.router, prefix="/image-analysis", tags=["Image Analysis"])    # ✅ NEW
app.include_router(fusion.router, prefix="/fusion", tags=["Fusion Layer"])                      # ✅ NEW


# --------------------------
# Health Check Endpoint
# --------------------------
@app.get("/health", tags=["System"])
async def health_check():
    """
    Used by deployment probes to verify service health.
    """
    return {
        "status": "healthy",
        "service": "AI Health Assistant",
        "version": app.version,
        "environment": settings.ENVIRONMENT if hasattr(settings, "ENVIRONMENT") else "dev"
    }


# --------------------------
# Factory Function
# --------------------------
def create_app():
    """Factory function for Gunicorn/Uvicorn deployment."""
    return app


# --------------------------
# Run Application
# --------------------------
if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.APP_PORT if hasattr(settings, "APP_PORT") else 8000,
        reload=settings.DEBUG if hasattr(settings, "DEBUG") else True
    )
