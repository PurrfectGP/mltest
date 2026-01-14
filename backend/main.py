import os
import json
import logging
import traceback
from pathlib import Path
from contextlib import asynccontextmanager
from typing import List
from datetime import datetime, timezone

from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
from sqlalchemy.orm import Session

from database import init_db, get_db
from routers import auth_router, calibration_router, psychometric_router
from db_models import User
from auth import get_current_user

# ==================== LOGGING SETUP ====================
LOG_DIR = Path(os.getenv("DATA_DIR", "/app/data")) / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "harmonia.log"

# Configure logging with both console and file output
logging.basicConfig(
    level=logging.DEBUG if os.getenv("DEBUG", "false").lower() == "true" else logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
    handlers=[
        logging.StreamHandler(),  # Console output
        logging.FileHandler(LOG_FILE, mode='a')  # File output
    ]
)
logger = logging.getLogger(__name__)
logger.info(f"=== Harmonia Starting === Log file: {LOG_FILE}")


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

# CORS configuration - use environment variable in production
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== GLOBAL ERROR HANDLER ====================
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions and return JSON response."""
    # Log detailed error info
    error_id = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
    tb = traceback.format_exc()

    logger.error(f"""
================================================================================
ERROR ID: {error_id}
TIME: {datetime.now(timezone.utc).isoformat()}
PATH: {request.method} {request.url.path}
QUERY: {request.query_params}
EXCEPTION TYPE: {type(exc).__name__}
EXCEPTION: {exc}
TRACEBACK:
{tb}
================================================================================
""")

    debug_mode = os.getenv("DEBUG", "false").lower() == "true"
    return JSONResponse(
        status_code=500,
        content={
            "detail": str(exc) if debug_mode else "Internal server error",
            "type": type(exc).__name__,
            "error_id": error_id,
            "hint": "Check /api/logs for full details" if debug_mode else None
        }
    )

# Include API routers
app.include_router(auth_router)
app.include_router(calibration_router)
app.include_router(psychometric_router)

# Serve static files (frontend)
STATIC_DIR = Path(__file__).parent / "static"
if STATIC_DIR.exists():
    # Serve assets at /assets path (matches Vite build output)
    assets_dir = STATIC_DIR / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")
    # Serve other static files at root
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# ==================== ROOT & FRONTEND ====================

@app.get("/")
async def serve_frontend():
    """Serve the main frontend application."""
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"message": "Harmonia Phase 1 API", "docs": "/docs"}


@app.get("/manifest.webmanifest")
async def serve_manifest():
    return FileResponse(STATIC_DIR / "manifest.webmanifest", media_type="application/manifest+json")


@app.get("/vite.svg")
async def serve_vite_svg():
    return FileResponse(STATIC_DIR / "vite.svg", media_type="image/svg+xml")


@app.get("/registerSW.js")
async def serve_register_sw():
    return FileResponse(STATIC_DIR / "registerSW.js", media_type="application/javascript")


@app.get("/sw.js")
async def serve_sw():
    return FileResponse(STATIC_DIR / "sw.js", media_type="application/javascript")


@app.get("/workbox-{filename}")
async def serve_workbox(filename: str):
    return FileResponse(STATIC_DIR / f"workbox-{filename}", media_type="application/javascript")


# ==================== API ENDPOINTS ====================

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


# ==================== ADMIN/DEBUG ENDPOINTS (Protected) ====================

@app.get("/api/admin/users")
async def list_users(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all registered users (protected - requires auth)."""
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
async def list_profiles(current_user: User = Depends(get_current_user)):
    """List all generated visual vector profiles (protected - requires auth)."""
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
async def get_profile_detail(user_id: str, current_user: User = Depends(get_current_user)):
    """Get detailed profile data for a specific user (protected - requires auth)."""
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
async def get_db_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get database information (protected - requires auth)."""
    from database import DATABASE_URL
    user_count = db.query(User).count()

    return {
        "database_url": DATABASE_URL.replace("://", "://***:***@") if "@" in DATABASE_URL else DATABASE_URL,
        "user_count": user_count
    }


# ==================== LOG VIEWING ENDPOINT ====================

@app.get("/api/logs")
async def get_logs(lines: int = 100, search: str = None):
    """
    View application logs (no auth required for debugging).
    - lines: Number of lines to return (default 100, max 1000)
    - search: Optional search term to filter logs
    """
    lines = min(lines, 1000)  # Cap at 1000 lines

    if not LOG_FILE.exists():
        return PlainTextResponse("No logs yet.", media_type="text/plain")

    try:
        with open(LOG_FILE, 'r') as f:
            all_lines = f.readlines()

        # Get last N lines
        log_lines = all_lines[-lines:]

        # Filter by search term if provided
        if search:
            log_lines = [l for l in log_lines if search.lower() in l.lower()]

        log_content = ''.join(log_lines)

        return PlainTextResponse(
            f"=== Harmonia Logs (last {len(log_lines)} lines) ===\n"
            f"=== Log file: {LOG_FILE} ===\n"
            f"=== Total lines in file: {len(all_lines)} ===\n\n"
            f"{log_content}",
            media_type="text/plain"
        )
    except Exception as e:
        return PlainTextResponse(f"Error reading logs: {e}", media_type="text/plain")


@app.delete("/api/logs")
async def clear_logs(current_user: User = Depends(get_current_user)):
    """Clear the log file (protected - requires auth)."""
    try:
        with open(LOG_FILE, 'w') as f:
            f.write(f"=== Logs cleared at {datetime.now(timezone.utc).isoformat()} ===\n")
        return {"message": "Logs cleared", "file": str(LOG_FILE)}
    except Exception as e:
        return {"error": str(e)}


# ==================== PROFILE DOWNLOAD ENDPOINT ====================

@app.get("/api/profile/download")
async def download_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Download user profile and MetaFBP calibration data as JSON."""
    from services import VisualService

    # Get visual vector
    service = VisualService(data_dir=os.getenv("DATA_DIR", "/app/data"))
    vector_data = service.load_vector(current_user.id)

    # Get calibration ratings from DB
    from db_models import CalibrationRating, PsychometricResponse
    ratings = db.query(CalibrationRating).filter(
        CalibrationRating.user_id == current_user.id
    ).all()

    psychometric = db.query(PsychometricResponse).filter(
        PsychometricResponse.user_id == current_user.id
    ).all()

    # Build complete profile
    profile = {
        "user": {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "gender": current_user.gender,
            "preference_target": current_user.preference_target,
            "created_at": str(current_user.created_at),
            "calibration_complete": current_user.calibration_complete,
            "psychometric_complete": current_user.psychometric_complete
        },
        "calibration_ratings": [
            {"image_id": r.image_id, "rating": r.rating, "created_at": str(r.created_at)}
            for r in ratings
        ],
        "psychometric_responses": [
            {"question_id": p.question_id, "selected_option_id": p.selected_option_id,
             "traits_extracted": p.traits_extracted, "created_at": str(p.created_at)}
            for p in psychometric
        ],
        "metafbp_vector": vector_data,
        "export_timestamp": datetime.now(timezone.utc).isoformat()
    }

    from fastapi.responses import Response
    return Response(
        content=json.dumps(profile, indent=2),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename=harmonia_profile_{current_user.id}.json"}
    )


# ==================== SPA CATCH-ALL (must be last) ====================

@app.get("/{full_path:path}")
async def spa_catch_all(full_path: str):
    """Catch-all route for SPA - serves index.html for client-side routing."""
    # Don't catch API routes
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="Not found")
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    raise HTTPException(status_code=404, detail="Not found")
