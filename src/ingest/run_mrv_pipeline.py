import os
from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from src.utils.logging_config import setup_logger
from src.mrv.utils import bulk_calculate_co2_removal

DATABASE_URL = os.getenv("DATABASE_URL")

if __name__ == "__main__":
    logger = setup_logger(__name__)
    engine = create_engine(DATABASE_URL)

    Session = sessionmaker(bind=engine)
    session = Session()

    plants = ["PLANT_A", "PLANT_B"]
    all_results = {}

    for plant_id in plants:
        logger.info(f"=== Calculating {plant_id} ===")
        results = bulk_calculate_co2_removal(
            session=session,
            plant_id=plant_id,
            start_date=date(2025, 4, 1),
            end_date=date(2025, 6, 30),
        )
        all_results[plant_id] = results

        # Calculate totals only for VALID records
        valid_results = [r for r in results if r.quality_flag == "VALID"]
        invalid_count = len(results) - len(valid_results)

        total_co2 = sum(r.co2_removed_metric_tons_per_day for r in valid_results)
        avg_co2 = total_co2 / len(valid_results) if valid_results else 0

        logger.info(f"{plant_id}: {len(results)} dates ({len(valid_results)} valid, {invalid_count} invalid)")
        logger.info(f"Total CO2 (valid only): {total_co2:.2f} MT")
        logger.info(f"Avg daily (valid only): {avg_co2:.4f} MT/day")

    # Grand total (valid records only)
    grand_total = sum(
        sum(r.co2_removed_metric_tons_per_day for r in results if r.quality_flag == "VALID")
        for results in all_results.values()
    )

    total_records = sum(len(results) for results in all_results.values())
    total_valid = sum(len([r for r in results if r.quality_flag == "VALID"]) for results in all_results.values())

    logger.info(f"=== Summary ===")
    logger.info(f"Total records: {total_records} ({total_valid} valid)")
    logger.info(f"Grand Total CO2 Removed (VALID only): {grand_total:.2f} MT")
