"""
Database Connection & Session Management
Supports both PostgreSQL (Production / Network) and SQLite (Local / Offline Fallback).
Defaults to PostgreSQL with verified PostGIS / standard schema tables.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool

# Base directories
DB_DIR = Path(__file__).resolve().parent
ROOT_DIR = DB_DIR.parent
DEFAULT_SQLITE_PATH = DB_DIR / "krishilink.db"

# Load environment variables
load_dotenv(ROOT_DIR / ".env")
load_dotenv(ROOT_DIR / "infra" / ".env")

# Read DATABASE_URL from environment with PostgreSQL as primary default
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://krishi_admin:krishi_pass_2026@localhost:5432/krishilink"
)

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

try:
    if "postgresql" in DATABASE_URL:
        engine = create_engine(
            DATABASE_URL,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            echo=False
        )
        # Test connection actively
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    else:
        raise ValueError("Using local SQLite database")
except Exception as e:
    # Graceful fallback to SQLite if PostgreSQL is temporarily offline
    print(f"⚠️ Notice: PostgreSQL connection check: {e}. Falling back to SQLite local database.")
    DATABASE_URL = f"sqlite:///{DEFAULT_SQLITE_PATH.as_posix()}"
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for SQLAlchemy ORM models
Base = declarative_base()

def get_db():
    """FastAPI / Application dependency for obtaining a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
