import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Boolean, Text, JSON

from database import Base


def generate_uuid():
    return str(uuid.uuid4())


def utc_now():
    """Return current UTC time (timezone-aware)."""
    return datetime.now(timezone.utc)


class User(Base):
    """User database model."""
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    gender = Column(String(20), nullable=True)
    preference_target = Column(String(20), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    # Progress flags
    calibration_complete = Column(Boolean, default=False)
    psychometric_complete = Column(Boolean, default=False)


class PsychometricResponse(Base):
    """Store user's psychometric question responses."""
    __tablename__ = "psychometric_responses"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), nullable=False, index=True)
    question_id = Column(String(50), nullable=False)
    selected_option_id = Column(String(50), nullable=True)
    open_response = Column(Text, nullable=True)
    scale_value = Column(String(10), nullable=True)
    traits_extracted = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)


class CalibrationRating(Base):
    """Store user's image calibration ratings."""
    __tablename__ = "calibration_ratings"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), nullable=False, index=True)
    image_id = Column(String(100), nullable=False)
    rating = Column(String(1), nullable=False)  # 1-5
    created_at = Column(DateTime(timezone=True), default=utc_now)
