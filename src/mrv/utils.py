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

    # ✅ Use validation functions from qaqc.mrv_utils
    should_calculate, quality_flag, validation_message = validate_all_inputs(
        ops, ca_upstream_reading, ca_downstream_reading, plant_id, calc_date, logger
    )

    # If validation failed critically, skip calculation
    if not should_calculate:
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

    # Log the calculation details
    flag_symbol = "✓" if quality_flag == "VALID" else "⚠"
    logger.info(f"{flag_symbol} {plant_id} {calc_date}: CO2={co2_mt_day:.6f} MT/day [{quality_flag}]")

    if validation_message:
        logger.info(f"  Note: {validation_message}")

    return calc


def bulk_calculate_co2_removal(
    session: Session, plant_id: str, start_date: date = None, end_date: date = None
) -> list[CO2RemovalCalculation]:
    """Calculate CO2 removal for a range of dates"""

    # Get all ops dates for this plant
    query = session.query(WasteWaterPlantOperation.date).filter(WasteWaterPlantOperation.plant_id == plant_id)

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
