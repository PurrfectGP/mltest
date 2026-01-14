import os
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from database import get_db
from db_models import User, CalibrationRating
from schemas import (
    CalibrationSubmission,
    CalibrationImagesResponse,
    CalibrationImage,
    VisualVectorResponse
)
from auth import get_current_user
from services import VisualService

router = APIRouter(prefix="/api/calibration", tags=["calibration"])

# Initialize VisualService (lazy loading in production)
DATA_DIR = os.getenv("DATA_DIR", "/app/data")


def get_visual_service() -> VisualService:
    """Get or create VisualService instance."""
    return VisualService(data_dir=DATA_DIR)


@router.get("/images", response_model=CalibrationImagesResponse)
async def get_calibration_images(
    count: int = 20,
    current_user: User = Depends(get_current_user)
):
    """Get list of calibration images for rating."""
    service = get_visual_service()
    images = service.get_calibration_images(count=count)

    return CalibrationImagesResponse(
        images=[CalibrationImage(**img) for img in images],
        total=len(images)
    )


@router.get("/images/{filename}")
async def get_calibration_image(filename: str):
    """Serve a calibration image file."""
    image_path = Path(DATA_DIR) / "global_calibration" / filename

    if not image_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found"
        )

    return FileResponse(image_path)


@router.post("/submit", response_model=VisualVectorResponse)
async def submit_calibration(
    submission: CalibrationSubmission,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit image ratings and generate visual vector."""
    # Validate ratings
    if not submission.ratings:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No ratings provided"
        )

    for image_id, rating in submission.ratings.items():
        if not 1 <= rating <= 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid rating for {image_id}: must be 1-5"
            )

    # Store ratings in database
    for image_id, rating in submission.ratings.items():
        db_rating = CalibrationRating(
            user_id=current_user.id,
            image_id=image_id,
            rating=str(rating)
        )
        db.add(db_rating)

    # Generate visual vector using VisualService
    service = get_visual_service()

    try:
        vector_data = service.calibrate_user(
            user_id=current_user.id,
            ratings=submission.ratings,
            gender=current_user.gender,
            preference_target=current_user.preference_target
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Calibration failed: {str(e)}"
        )

    # Update user progress
    current_user.calibration_complete = True
    db.commit()

    return vector_data


@router.get("/vector", response_model=VisualVectorResponse)
async def get_visual_vector(
    current_user: User = Depends(get_current_user)
):
    """Get the current user's visual vector if calibration is complete."""
    if not current_user.calibration_complete:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Calibration not yet completed"
        )

    service = get_visual_service()
    vector = service.load_vector(current_user.id)

    if not vector:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Visual vector not found"
        )

    return vector
