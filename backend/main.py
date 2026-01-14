import os
import json
from pathlib import Path
from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database import init_db, get_db
from routers import auth_router, calibration_router, psychometric_router
from db_models import User


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

# CORS configuration - allow all for Cloud Run
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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


# ============ ADMIN/DEBUG ENDPOINTS ============

@app.get("/api/admin/users")
async def list_users(db: Session = Depends(get_db)):
    """List all registered users (for testing/admin)."""
    users = db.query(User).all()
    return {
        "total": len(users),
        "users": [
            {
                "id": u.id,
                "username": u.username,
                "email": u.email,
                "psychometric_complete": u.psychometric_complete,
                "calibration_complete": u.calibration_complete,
                "created_at": str(u.created_at)
            }
            for u in users
        ]
    }


@app.get("/api/admin/profiles")
async def list_profiles():
    """List all generated visual vector profiles."""
    data_dir = Path(os.getenv("DATA_DIR", "/app/data"))
    profiles_dir = data_dir / "profiles"

    profiles = []
    if profiles_dir.exists():
        for user_dir in profiles_dir.iterdir():
            if user_dir.is_dir():
                vector_file = user_dir / "p1_visual_vector.json"
                profile_info = {
                    "user_id": user_dir.name,
                    "has_vector": vector_file.exists(),
                    "vector_file": str(vector_file) if vector_file.exists() else None
                }

                if vector_file.exists():
                    try:
                        with open(vector_file) as f:
                            vector_data = json.load(f)
                        profile_info["vector_summary"] = {
                            "images_rated": vector_data.get("meta", {}).get("images_rated", 0),
                            "embedding_dim": len(vector_data.get("self_analysis", {}).get("embedding_vector", [])),
                            "calibration_confidence": vector_data.get("preference_model", {}).get("calibration_confidence", 0),
                            "timestamp": vector_data.get("meta", {}).get("calibration_timestamp")
                        }
                    except Exception as e:
                        profile_info["error"] = str(e)

                profiles.append(profile_info)

    return {
        "profiles_dir": str(profiles_dir),
        "total": len(profiles),
        "profiles": profiles
    }


@app.get("/api/admin/profiles/{user_id}")
async def get_profile_detail(user_id: str):
    """Get detailed profile data for a specific user."""
    data_dir = Path(os.getenv("DATA_DIR", "/app/data"))
    vector_file = data_dir / "profiles" / user_id / "p1_visual_vector.json"

    if not vector_file.exists():
        return {"error": "Profile not found", "user_id": user_id}

    with open(vector_file) as f:
        vector_data = json.load(f)

    return {
        "user_id": user_id,
        "vector_file": str(vector_file),
        "data": vector_data
    }


@app.get("/api/admin/db-info")
async def get_db_info(db: Session = Depends(get_db)):
    """Get database information."""
    from database import DATABASE_URL
    user_count = db.query(User).count()

    return {
        "database_url": DATABASE_URL.replace("://", "://***:***@") if "@" in DATABASE_URL else DATABASE_URL,
        "user_count": user_count
    }
