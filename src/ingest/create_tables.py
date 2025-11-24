from sqlalchemy import create_engine, inspect
from src.models.schemas import Base
import os
from src.utils.logging_config import setup_logger


logger = setup_logger(__name__)


DATABASE_URL = os.getenv("DATABASE_URL")

def recreate_schema():
    """Drop and recreate all tables using SQLAlchemy"""
    logger.info("=" * 60)
    logger.info("RECREATING DATABASE SCHEMA")
    logger.info("=" * 60)

    if not DATABASE_URL:
        logger.error("DATABASE_URL environment variable not set")
        raise ValueError("DATABASE_URL is required")

    logger.info(f"Connecting to database...")
    engine = create_engine(DATABASE_URL)

    # Get list of existing tables before dropping
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    if existing_tables:
        logger.info(f"Found {len(existing_tables)} existing tables to drop:")
        for table in existing_tables:
            logger.info(f"  - {table}")
    else:
        logger.info("No existing tables found")

    # Drop all tables defined in Base metadata
    logger.info("Dropping all tables...")
    try:
        Base.metadata.drop_all(engine)
        logger.info("✓ All tables dropped successfully")
    except Exception as e:
        logger.error(f"Error dropping tables: {e}")
        raise

    # Create all tables defined in Base metadata
    logger.info("Creating all tables...")
    try:
        Base.metadata.create_all(engine)
        logger.info("✓ All tables created successfully")
    except Exception as e:
        logger.error(f"Error creating tables: {e}")
        raise

    # List created tables
    tables = list(Base.metadata.tables.keys())
    logger.info(f"Created {len(tables)} tables:")
    for table in tables:
        logger.info(f"  ✓ {table}")

    # Verify tables exist in database
    inspector = inspect(engine)
    db_tables = inspector.get_table_names()

    if len(db_tables) == len(tables):
        logger.info(f"Verified: All {len(tables)} tables exist in database")
    else:
        logger.warning(f"Mismatch: Expected {len(tables)} tables, found {len(db_tables)} in database")

    logger.info("=" * 60)
    logger.info("✓ Schema recreation complete")
    logger.info("=" * 60)


if __name__ == "__main__":
    try:
        recreate_schema()
    except Exception as e:
        logger.error(f"Schema recreation failed: {e}")
        raise
