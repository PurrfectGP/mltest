import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.database import init_db
from backend.routers import auth_router, calibration_router, psychometric_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup: Initialize database
    init_db()
    yield
    # Shutdown: cleanup if needed


app = FastAPI(
    title="Harmonia Phase 1",
    description="Visual Calibration PWA using MetaFBP Algorithm",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        os.getenv("FRONTEND_URL", "http://localhost:5173")
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(calibration_router)
app.include_router(psychometric_router)


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "harmonia-phase1"}


@app.get("/api/status")
async def get_status():
    """Get application status."""
    return {
        "version": "1.0.0",
        "phase": "1 - Visual Calibration",
        "features": [
            "User Registration",
            "Fixed Five Psychometric Questions",
            "Visual Calibration (1-5 Star Rating)",
            "MetaFBP Vector Generation"
        ]
    }
