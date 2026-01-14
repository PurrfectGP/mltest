import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Use SQLite for Cloud Run (data stored in /app/data)
DATA_DIR = os.getenv("DATA_DIR", "/app/data")
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR}/harmonia.db")

# Create engine (SQLite needs check_same_thread=False for FastAPI)
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db():
    """Dependency for getting database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables."""
    # Import models to ensure they're registered
    import db_models  # noqa
    Base.metadata.create_all(bind=engine)
    print(f"Database initialized at {DATABASE_URL}")
