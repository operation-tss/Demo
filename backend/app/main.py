import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes.report_routes import router as report_router
from .api.v1.report_analyzer import router as report_analyzer_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("medical_report_analyzer")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Preload OCR models at application startup (Requirement 8)
    try:
        from .services.ocr_service import init_ocr_models
        init_ocr_models()
    except Exception as e:
        logger.warning(f"Failed to preload OCR models at startup: {e}")
    yield

app = FastAPI(
    title="Medical Report Analyzer API",
    description="Standalone local rule-based medical report analyzer. Strictly no AI or LLMs.",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for frontend Vite development server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routes
app.include_router(report_analyzer_router, prefix="/api/v1/report-analyzer", tags=["Report Analyzer"])
app.include_router(report_router)

@app.get("/api/health")
@app.get("/api/v1/health")
async def health_check():
    """Health status endpoint."""
    return {
        "status": "healthy",
        "service": "Medical Report Analyzer API",
        "mode": "deterministic-rule-based",
        "ai_used": False
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
