import os
from datetime import date, datetime

import pandas as pd
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.sql import func
from src.utils.logging_config import setup_logger
from src.models.schemas import CO2RemovalCalculation, CrewCarbonLabReading, WasteWaterPlantOperation


def calculate_co2_removal_from_sources(
    session: Session,
    plant_id: str,
    calc_date: date,
    quality_flag: str = "VALID",
) -> CO2RemovalCalculation | None:
    """
    Calculate CO2 removal by joining ops data and lab readings

    Args:
        session: SQLAlchemy session
        plant_id: Plant identifier (string like 'PLANT_A')
        calc_date: Date to calculate for
        quality_flag: Optional quality flag (default: "VALID")

    Returns:
        CO2RemovalCalculation record or None if data constraints violated
    """

    # Get ops data for this plant and date
    ops = (
        session.query(WasteWaterPlantOperation)
        .filter(
            WasteWaterPlantOperation.plant_id == plant_id,
            WasteWaterPlantOperation.date == calc_date,
        )
        .first()
    )

    if not ops:
        print(f"✗ No ops data found for {plant_id} on {calc_date}")
        return None

    # Get calcium readings for this plant and date
    ca_upstream_reading = (
        session.query(CrewCarbonLabReading)
        .filter(
            CrewCarbonLabReading.plant_id == plant_id,
            CrewCarbonLabReading.parameter_name == "calcium",
            CrewCarbonLabReading.plant_unit_id == "primary_clarifier",
            func.date(CrewCarbonLabReading.datetime) == calc_date,
        )
        .first()
    )

    ca_downstream_reading = (
        session.query(CrewCarbonLabReading)
        .filter(
            CrewCarbonLabReading.plant_id == plant_id,
            CrewCarbonLabReading.parameter_name == "calcium",
            CrewCarbonLabReading.plant_unit_id == "secondary_clarifier",
            func.date(CrewCarbonLabReading.datetime) == calc_date,
        )
        .first()
    )

    # Check for missing required data - skip if not present
    if not ca_upstream_reading or not ca_downstream_reading:
        print(f"✗ Missing calcium readings for {plant_id} on {calc_date} - skipping")
        return None

    ca_upstream = ca_upstream_reading.value
    ca_downstream = ca_downstream_reading.value
    flow_mgd = ops.actual_eff_flow_mgd

    # Check for missing flow data
    if flow_mgd is None or flow_mgd <= 0:
        print(f"✗ Missing or invalid flow data for {plant_id} on {calc_date} - skipping")
        return None

    # Molecular weights (g/mol)
    MW_Ca = 40.078
    MW_CaCO3 = 100.0869
    MW_CO2 = 44.0095

    # Calculate intermediate values
    ca_delta = ca_downstream - ca_upstream

    # Check for negative or zero delta - flag as INVALID but calculate
    if ca_delta <= 0:
        quality_flag = "INVALID"

    # Flow calculations
    flow_m3_day = flow_mgd * 3785.41
    flow_l_day = flow_m3_day * 1000

    # Molecular weight ratios
    ca_to_caco3 = MW_CaCO3 / MW_Ca
    co2_to_caco3 = MW_CO2 / MW_CaCO3

    # Mass calculations
    caco3_mg = ca_delta * flow_l_day * ca_to_caco3
    co2_mg = caco3_mg * co2_to_caco3
    co2_mt_day = co2_mg / 1_000_000_000

    # Store calculation
    calc = CO2RemovalCalculation(
        plant_id=plant_id,
        date=calc_date,
        ca_upstream_mg_per_l=ca_upstream,
        ca_downstream_mg_per_l=ca_downstream,
        flow_mgd=flow_mgd,
        ca_delta_mg_per_l=ca_delta,
        flow_m3_per_day=flow_m3_day,
        flow_l_per_day=flow_l_day,
        ca_to_caco3_ratio=ca_to_caco3,
        co2_to_caco3_ratio=co2_to_caco3,
        caco3_mg=caco3_mg,
        co2_mg=co2_mg,
        co2_removed_metric_tons_per_day=co2_mt_day,
        quality_flag=quality_flag,
    )

    # Print the calculation details
    from sqlalchemy import inspect
    calc_dict = {c.name: getattr(calc, c.name) for c in inspect(calc.__class__).mapper.columns}
    flag_symbol = "✓" if quality_flag == "VALID" else "⚠"
    print(f"{flag_symbol} {plant_id} {calc_date}: CO2={co2_mt_day:.6f} MT/day [{quality_flag}]")

    return calc


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
