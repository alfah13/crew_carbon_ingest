# scripts/setup_db.py
"""
Initialize database tables for local development
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models.database import engine, Base
from src.models.schemas import RawData, ValidatedData, MRVResult
from src.utils.logging_config import setup_logger

logger = setup_logger(__name__)


def setup_database():
    """Create all database tables"""
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("✓ Database tables created successfully")


if __name__ == "__main__":
    setup_database()
