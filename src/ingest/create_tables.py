from sqlalchemy import create_engine
from src.models.schemas import Base
import os
from src.utils.logging_config import setup_logger

logger = setup_logger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")

def recreate_schema():
    """Drop and recreate all tables using SQLAlchemy"""
    logger.info("="*60)
    logger.info("RECREATING DATABASE SCHEMA")
    logger.info("="*60)
    
    engine = create_engine(DATABASE_URL)
    
    # Drop all tables defined in Base metadata
    logger.info("Dropping all tables...")
    Base.metadata.drop_all(engine)
    logger.info("✓ All tables dropped")
    
    # Create all tables defined in Base metadata
    logger.info("\nCreating all tables...")
    Base.metadata.create_all(engine)
    logger.info("✓ All tables created")
    
    # List created tables
    tables = list(Base.metadata.tables.keys())
    logger.info(f"\nCreated {len(tables)} tables:")
    for table in tables:
        logger.info(f"  - {table}")
    
    logger.info("="*60)
    logger.info("✓ Schema recreation complete")
    logger.info("="*60)

if __name__ == "__main__":
    recreate_schema()
