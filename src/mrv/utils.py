import os
from datetime import date

from sqlalchemy import inspect
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from src.models.schemas import (CO2RemovalCalculation, CrewCarbonLabReading,
                                WasteWaterPlantOperation)
from src.utils.logging_config import setup_logger


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

    logger = setup_logger(__name__)
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
        logger.warn(f"X No ops data found for {plant_id} on {calc_date}")
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
        logger.warn(f"X Missing calcium readings for {plant_id} on {calc_date} - skipping")
        return None

    ca_upstream = ca_upstream_reading.value
    ca_downstream = ca_downstream_reading.value
    flow_mgd = ops.actual_eff_flow_mgd

    # Check for missing flow data
    if flow_mgd is None or flow_mgd <= 0:
        logger.warn(f"X Missing or invalid flow data for {plant_id} on {calc_date} - skipping")
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

    calc_dict = {c.name: getattr(calc, c.name) for c in inspect(calc.__class__).mapper.columns}
    flag_symbol = "✓" if quality_flag == "VALID" else "⚠"
    logger.info(f"{flag_symbol} {plant_id} {calc_date}: CO2={co2_mt_day:.6f} MT/day [{quality_flag}]")

    return calc
