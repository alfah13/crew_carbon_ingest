import os
from datetime import date, datetime

import pandas as pd
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.sql import func
from src.utils.logging_config import setup_logger
from src.models.schemas import CO2RemovalCalculation, CrewCarbonLabReading, WasteWaterPlantOperation
from src.mrv.utils import calculate_co2_removal_from_sources



def bulk_calculate_co2_removal(
    session: Session, plant_id: str, start_date: date = None, end_date: date = None
) -> list[CO2RemovalCalculation]:
    """Calculate CO2 removal for a range of dates"""

    # Get all ops dates for this plant
    query = session.query(WasteWaterPlantOperation.date).filter(
        WasteWaterPlantOperation.plant_id == plant_id
    )

    if start_date:
        query = query.filter(WasteWaterPlantOperation.date >= start_date)
    if end_date:
        query = query.filter(WasteWaterPlantOperation.date <= end_date)

    dates = [row[0] for row in query.distinct().all()]

    results = []
    skipped_count = 0
    
    for calc_date in dates:
        calc = calculate_co2_removal_from_sources(
            session=session,
            plant_id=plant_id,
            calc_date=calc_date,
            quality_flag="VALID",
        )
        
        if calc is not None:
            results.append(calc)
            session.add(calc)
        else:
            skipped_count += 1

    # Commit all valid calculations
    session.commit()
    
    print(f"\n{plant_id}: {len(results)} records calculated, {skipped_count} skipped due to missing data")
    
    return results


# Usage
if __name__ == "__main__":
    logger = setup_logger(__name__)
    DATABASE_URL = os.getenv("DATABASE_URL")
    engine = create_engine(DATABASE_URL)
    # CO2RemovalCalculation.__table__.drop(engine, checkfirst=True)
    # CO2RemovalCalculation.__table__.create(engine, checkfirst=True)

    Session = sessionmaker(bind=engine)
    session = Session()

    plants = ["PLANT_A", "PLANT_B"]
    all_results = {}

    for plant_id in plants:
        logger.info(f"\n=== Calculating {plant_id} ===")
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

        logger.info(f" {plant_id}: {len(results)} dates ({len(valid_results)} valid, {invalid_count} invalid)")
        logger.info(f"  Total CO2 (valid only): {total_co2:.2f} MT")
        logger.info(f"  Avg daily (valid only): {avg_co2:.4f} MT/day")

    # Grand total (valid records only)
    grand_total = sum(
        sum(r.co2_removed_metric_tons_per_day for r in results if r.quality_flag == "VALID")
        for results in all_results.values()
    )
    
    total_records = sum(len(results) for results in all_results.values())
    total_valid = sum(len([r for r in results if r.quality_flag == "VALID"]) for results in all_results.values())
    
    logger.info(f"\n=== Summary ===")
    logger.info(f"Total records: {total_records} ({total_valid} valid)")
    logger.info(f"Grand Total CO2 Removed (VALID only): {grand_total:.2f} MT")
