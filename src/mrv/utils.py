import os
from datetime import date

from sqlalchemy import inspect
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from src.models.schemas import CO2RemovalCalculation, CrewCarbonLabReading, WasteWaterPlantOperation
from src.utils.logging_config import setup_logger
from src.qaqc.mrv_utils import (
    validate_ops_data,
    validate_calcium_readings,
    validate_ca_delta,
    validate_all_inputs,
    ValidationResult,
)

logger = setup_logger(__name__)


def calculate_co2_removal_from_sources(
    session: Session,
    plant_id: str,
    calc_date: date,
) -> CO2RemovalCalculation | None:
    """
    Calculate CO2 removal by joining ops data and lab readings

    Args:
        session: SQLAlchemy session
        plant_id: Plant identifier (string like 'PLANT_A')
        calc_date: Date to calculate for

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

    # Run all validations - THIS IS KEY
    should_calculate, quality_flag, validation_message = validate_all_inputs(
        ops, ca_upstream_reading, ca_downstream_reading, plant_id, calc_date, logger
    )

    # If validation failed critically, return None (but log why)
    if not should_calculate:
        logger.warning(
            f"✗ Skipping {plant_id} {calc_date}: {quality_flag} - {validation_message}"
        )
        return None

    # Extract values (we know they exist from validation)
    ca_upstream = ca_upstream_reading.value
    ca_downstream = ca_downstream_reading.value
    flow_mgd = ops.actual_eff_flow_mgd

    # Molecular weights (g/mol)
    MW_Ca = 40.078
    MW_CaCO3 = 100.0869
    MW_CO2 = 44.0095

    # Calculate intermediate values
    ca_delta = ca_downstream - ca_upstream

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

    # Create calculation record with BOTH quality_flag AND validation_message
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
        validation_message=validation_message,  # ← ADD THIS
    )

    # Log the calculation
    flag_symbol = "✓" if quality_flag == "VALID" else "⚠"
    logger.info(
        f"{flag_symbol} {plant_id} {calc_date}: "
        f"CO2={co2_mt_day:.6f} MT/day "
        f"[{quality_flag}]"
    )

    if validation_message:
        logger.info(f"  └─ {validation_message}")

    return calc


def bulk_calculate_co2_removal(
    session: Session, 
    plant_id: str, 
    start_date: date = None, 
    end_date: date = None
) -> tuple[list[CO2RemovalCalculation], dict]:

    """
    Calculate CO2 removal for a range of dates
    
    Returns:
        dict with summary stats including calculated/skipped/invalid counts
    """

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
    quality_flags = {}  # Track distribution of quality flags

    logger.info(f"Processing {len(dates)} dates for {plant_id}")

    for calc_date in dates:
        calc = calculate_co2_removal_from_sources(
            session=session,
            plant_id=plant_id,
            calc_date=calc_date,
        )

        if calc is not None:
            results.append(calc)
            session.add(calc)
            
            # Track quality flags
            flag = calc.quality_flag
            quality_flags[flag] = quality_flags.get(flag, 0) + 1
        else:
            skipped_count += 1

    # Commit all valid calculations
    session.commit()

    # Print summary
    summary = {
        'plant_id': plant_id,
        'total_dates': len(dates),
        'calculated': len(results),
        'skipped': skipped_count,
        'quality_flags': quality_flags,
    }

    logger.info(f"Summary for {plant_id}")
    logger.info(f"{'='*60}")
    logger.info(f"Total dates processed:        {summary['total_dates']}")
    logger.info(f"Successfully calculated:     {summary['calculated']}")
    logger.info(f"Skipped (no data):           {summary['skipped']}")
    logger.info(f"Quality Flag Breakdown:")
    for flag, count in sorted(quality_flags.items()):
        pct = (count / len(results) * 100) if results else 0
        logger.info(f"  {flag:20s}: {count:4d} ({pct:5.1f}%)")
    logger.info(f"{'='*60}\n")

    return results, summary
