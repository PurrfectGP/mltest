import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database configuration
# Supports: SQLite (local dev) or Cloud SQL PostgreSQL (production)

DATA_DIR = os.getenv("DATA_DIR", "/app/data")
DATABASE_URL = os.getenv("DATABASE_URL", "")
CLOUD_SQL_CONNECTION_NAME = os.getenv("CLOUD_SQL_CONNECTION_NAME", "")

# Base class for models
Base = declarative_base()


def get_engine():
    """Create database engine based on environment."""

    # Option 1: Cloud SQL PostgreSQL via Unix socket (Cloud Run)
    if CLOUD_SQL_CONNECTION_NAME:
        # Cloud SQL uses Unix socket in Cloud Run
        socket_path = f"/cloudsql/{CLOUD_SQL_CONNECTION_NAME}"
        db_user = os.getenv("DB_USER", "postgres")
        db_pass = os.getenv("DB_PASS", "")
        db_name = os.getenv("DB_NAME", "harmonia")

        url = f"postgresql+pg8000://{db_user}:{db_pass}@/{db_name}?unix_sock={socket_path}/.s.PGSQL.5432"
        return create_engine(url, pool_size=5, max_overflow=2, pool_pre_ping=True)

    # Option 2: Direct PostgreSQL URL
    if DATABASE_URL and DATABASE_URL.startswith("postgresql"):
        return create_engine(DATABASE_URL, pool_size=5, max_overflow=2, pool_pre_ping=True)

    # Option 3: SQLite for local development (default)
    sqlite_url = DATABASE_URL or f"sqlite:///{DATA_DIR}/harmonia.db"
    return create_engine(sqlite_url, connect_args={"check_same_thread": False})


# Create engine
engine = get_engine()

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependency for getting database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables."""
    import db_models  # noqa - registers models with Base
    Base.metadata.create_all(bind=engine)

    db_type = "Cloud SQL PostgreSQL" if CLOUD_SQL_CONNECTION_NAME else \
              "PostgreSQL" if DATABASE_URL and "postgresql" in DATABASE_URL else "SQLite"
    print(f"Database initialized: {db_type}")
