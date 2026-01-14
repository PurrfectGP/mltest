from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from datetime import datetime


class ImageRating(BaseModel):
    """Schema for a single image rating."""
    image_id: str
    rating: int = Field(..., ge=1, le=5, description="Rating from 1-5 stars")


class CalibrationSubmission(BaseModel):
    """Schema for submitting calibration ratings."""
    ratings: Dict[str, int] = Field(
        ...,
        description="Map of image_id to rating (1-5)"
    )


class CalibrationImage(BaseModel):
    """Schema for calibration image metadata."""
    id: str
    filename: str
    url: str


class CalibrationImagesResponse(BaseModel):
    """Schema for calibration images list response."""
    images: List[CalibrationImage]
    total: int


class VisualVectorMeta(BaseModel):
    """Metadata section of visual vector."""
    user_id: str
    gender: Optional[str] = None
    preference_target: Optional[str] = None
    calibration_timestamp: Optional[str] = None
    images_rated: int = 0


class DetectedTraits(BaseModel):
    """Detected traits from visual analysis."""
    facial_landmarks: List[str] = []
    style_presentation: List[str] = []
    vibe_tags: List[str] = []


class SelfAnalysis(BaseModel):
    """Self analysis section of visual vector."""
    embedding_vector: List[float]
    detected_traits: DetectedTraits


class AttractionTriggers(BaseModel):
    """Attraction triggers from preference model."""
    mandatory_traits: List[str] = []
    negative_traits: List[str] = []


class PreferenceModel(BaseModel):
    """Preference model section of visual vector."""
    ideal_vector: List[float] = []
    attraction_triggers: AttractionTriggers
    calibration_confidence: float = 0.0


class VisualVectorResponse(BaseModel):
    """Schema for p1_visual_vector.json response."""
    meta: VisualVectorMeta
    self_analysis: SelfAnalysis
    preference_model: PreferenceModel
