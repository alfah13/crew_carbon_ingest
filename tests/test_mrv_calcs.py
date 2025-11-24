# tests/test_mrv_calculations.py
import pytest
from datetime import date
from unittest.mock import Mock, MagicMock
from sqlalchemy.orm import Session

from src.mrv.utils import calculate_co2_removal_from_sources
from src.models.schemas import CO2RemovalCalculation, CrewCarbonLabReading, WasteWaterPlantOperation


def test_calculate_co2_removal_valid_data():
    """Test CO2 removal calculation with valid input data"""
    
    # Arrange: Create mock session and data
    mock_session = Mock(spec=Session)
    
    # Mock operational data
    mock_ops = Mock(spec=WasteWaterPlantOperation)
    mock_ops.actual_eff_flow_mgd = 31.2  # MGD
    
    # Mock upstream calcium reading
    mock_ca_upstream = Mock(spec=CrewCarbonLabReading)
    mock_ca_upstream.value = 39.8  # mg/L
    
    # Mock downstream calcium reading
    mock_ca_downstream = Mock(spec=CrewCarbonLabReading)
    mock_ca_downstream.value = 53.7  # mg/L
    
    # Setup query chain to return mocked data
    mock_session.query.return_value.filter.return_value.first.side_effect = [
        mock_ops,           # First query returns ops
        mock_ca_upstream,   # Second query returns upstream Ca
        mock_ca_downstream  # Third query returns downstream Ca
    ]
    
    # Act: Run the calculation
    result = calculate_co2_removal_from_sources(
        session=mock_session,
        plant_id="PLANT_A",
        calc_date=date(2025, 4, 10),
        quality_flag="VALID"
    )
    
    # Assert: Check result is not None and has expected values
    assert result is not None
    assert isinstance(result, CO2RemovalCalculation)
    assert result.plant_id == "PLANT_A"
    assert result.date == date(2025, 4, 10)
    assert result.ca_upstream_mg_per_l == 39.8
    assert result.ca_downstream_mg_per_l == 53.7
    assert result.flow_mgd == 31.2
    assert result.ca_delta_mg_per_l == pytest.approx(13.9, rel=0.01)  # 53.7 - 39.8
    assert result.quality_flag == "VALID"
    
    # Check CO2 calculation is positive
    assert result.co2_removed_metric_tons_per_day > 0
    assert result.co2_removed_metric_tons_per_day == pytest.approx(1.806, rel=0.01)
