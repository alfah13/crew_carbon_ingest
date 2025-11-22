# scripts/run_pipeline.py
"""
Simple pipeline runner for local development
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ingestion.ingest_sensor_data import ingest_sensor_data
from src.qaqc.quality_checks import run_quality_checks
from src.mrv.carbon_calculations import calculate_carbon_removal
from src.utils.logging_config import setup_logger

logger = setup_logger(__name__)


def run_pipeline():
    """Run the full pipeline: Ingestion -> QAQC -> MRV"""
    
    logger.info("=" * 60)
    logger.info("Starting Crew Carbon MRV Pipeline")
    logger.info("=" * 60)
    
    try:
        # Step 1: Ingestion
        logger.info("\n[1/3] Running data ingestion...")
        ingested_data = ingest_sensor_data()
        logger.info(f"✓ Ingested {len(ingested_data)} records")
        
        # Step 2: QAQC
        logger.info("\n[2/3] Running QAQC checks...")
        validated_data, failed_checks = run_quality_checks(ingested_data)
        logger.info(f"✓ Validated {len(validated_data)} records")
        if failed_checks:
            logger.warning(f"⚠ {len(failed_checks)} records failed validation")
        
        # Step 3: MRV
        logger.info("\n[3/3] Calculating carbon removal...")
        mrv_results = calculate_carbon_removal(validated_data)
        logger.info(f"✓ Generated MRV results")
        
        logger.info("\n" + "=" * 60)
        logger.info("Pipeline completed successfully!")
        logger.info("=" * 60)
        
        return mrv_results
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    run_pipeline()
