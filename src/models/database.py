# src/models/database.py
"""
Database connection and session management with TimescaleDB + PostGIS support
"""
from sqlalchemy import create_engine, text, event
from sqlalchemy.orm import sessionmaker, Session as SQLAlchemySession
from contextlib import contextmanager
import os
from typing import Generator
from pathlib import Path

# Load environment variables from .env file
from dotenv import load_dotenv

from src.models.schemas import Base
from src.utils.logging_config import setup_logger

logger = setup_logger(__name__)

# Load .env file
# Look for .env in project root
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Get configuration from environment
DATABASE_URL = os.getenv('DATABASE_URL')
ENV = os.getenv('ENV', 'development')

# Validate required environment variables
if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL environment variable is not set. "
        "Please create a .env file with DATABASE_URL defined."
    )

logger.info(f"Environment: {ENV}")
logger.info(f"Database URL: {DATABASE_URL.replace(DATABASE_URL.split('@')[0].split('//')[1], '***')}")  # Hide password in logs

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=(ENV == 'development'),  # Show SQL queries in development
    pool_recycle=3600
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


@contextmanager
def get_db() -> Generator[SQLAlchemySession, None, None]:
    """
    Context manager for database sessions
    Automatically handles commits and rollbacks
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Database error: {e}", exc_info=True)
        raise
    finally:
        db.close()
