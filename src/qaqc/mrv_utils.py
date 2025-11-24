"""
MRV validation utilities for CO2 removal calculations
"""
from typing import Tuple, Optional
from dataclasses import dataclass
from datetime import date


@dataclass
class ValidationResult:
    """Result of data validation"""
    is_valid: bool
    quality_flag: str
    message: Optional[str] = None


def validate_ops_data(
    ops,  # WasteWaterPlantOperation or None
    plant_id: str,
    calc_date: date,
    logger
) -> ValidationResult:
    """
    Validate operational data exists and has valid flow
    
    Returns:
        ValidationResult with validity status and quality flag
    """
    if not ops:
        logger.warning(f"✗ No ops data found for {plant_id} on {calc_date}")
        return ValidationResult(
            is_valid=False,
            quality_flag="NO_OPS_DATA",
            message="No operational data found"
        )
    
    if ops.actual_eff_flow_mgd is None or ops.actual_eff_flow_mgd <= 0:
        logger.warning(f"✗ Missing or invalid flow data for {plant_id} on {calc_date}")
        return ValidationResult(
            is_valid=False,
            quality_flag="INVALID_FLOW",
            message=f"Flow data invalid: {ops.actual_eff_flow_mgd}"
        )
    
    return ValidationResult(is_valid=True, quality_flag="VALID")


def validate_calcium_readings(
    ca_upstream_reading,  # CrewCarbonLabReading or None
    ca_downstream_reading,  # CrewCarbonLabReading or None
    plant_id: str,
    calc_date: date,
    logger
) -> ValidationResult:
    """
    Validate calcium readings exist
    
    Returns:
        ValidationResult with validity status and quality flag
    """
    if not ca_upstream_reading or not ca_downstream_reading:
        missing = []
        if not ca_upstream_reading:
            missing.append("upstream")
        if not ca_downstream_reading:
            missing.append("downstream")
        
        logger.warning(
            f"✗ Missing calcium readings ({', '.join(missing)}) for {plant_id} on {calc_date}"
        )
        return ValidationResult(
            is_valid=False,
            quality_flag="MISSING_CA_READINGS",
            message=f"Missing {', '.join(missing)} calcium readings"
        )
    
    return ValidationResult(is_valid=True, quality_flag="VALID")


def validate_ca_delta(
    ca_upstream: float,
    ca_downstream: float,
    plant_id: str,
    calc_date: date,
    logger
) -> ValidationResult:
    """
    Validate calcium delta is positive
    
    Returns:
        ValidationResult - still valid but flagged if delta <= 0
    """
    ca_delta = ca_downstream - ca_upstream
    
    if ca_delta <= 0:
        logger.warning(
            f"⚠ Non-positive ca_delta ({ca_delta:.4f}) for {plant_id} on {calc_date} - "
            f"upstream: {ca_upstream}, downstream: {ca_downstream}"
        )
        return ValidationResult(
            is_valid=True,  # Still calculate, but flag it
            quality_flag="INVALID",
            message=f"Non-positive ca_delta: {ca_delta:.4f}"
        )
    
    return ValidationResult(is_valid=True, quality_flag="VALID")


def validate_all_inputs(
    ops,  # WasteWaterPlantOperation or None
    ca_upstream_reading,  # CrewCarbonLabReading or None
    ca_downstream_reading,  # CrewCarbonLabReading or None
    plant_id: str,
    calc_date: date,
    logger
) -> Tuple[bool, str, Optional[str]]:
    """
    Run all validation checks
    
    Returns:
        Tuple of (should_calculate, quality_flag, message)
        - should_calculate: False means skip calculation entirely
        - quality_flag: "VALID" or reason for invalidity
        - message: Optional validation message
    """
    # Validate ops data
    ops_result = validate_ops_data(ops, plant_id, calc_date, logger)
    if not ops_result.is_valid:
        return False, ops_result.quality_flag, ops_result.message
    
    # Validate calcium readings
    ca_result = validate_calcium_readings(
        ca_upstream_reading,
        ca_downstream_reading,
        plant_id,
        calc_date,
        logger
    )
    if not ca_result.is_valid:
        return False, ca_result.quality_flag, ca_result.message
    
    # Validate ca_delta (this returns valid=True even if delta is negative)
    ca_delta_result = validate_ca_delta(
        ca_upstream_reading.value,
        ca_downstream_reading.value,
        plant_id,
        calc_date,
        logger
    )
    
    # Return True to calculate, but with appropriate quality flag
    return True, ca_delta_result.quality_flag, ca_delta_result.message
