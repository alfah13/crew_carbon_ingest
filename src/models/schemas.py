"""
SQLAlchemy models with TimescaleDB + PostGIS support
"""
from datetime import datetime

import pytz
from geoalchemy2 import Geometry
from sqlalchemy import (ARRAY, DECIMAL, JSON, TIMESTAMP, Boolean,
                        CheckConstraint, Column, Date, DateTime, Float,
                        ForeignKey, Index, Integer, Interval, String, Text)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func

from src.models.constants import VALID_TIMEZONES, TimezoneEnum

Base = declarative_base()


class WastewaterPlants(Base):
    __tablename__ = 'wastewater_plants'

    id = Column(Integer, primary_key=True)
    plant_id = Column(String, nullable=False)
    city = Column(String, nullable=False)
    state = Column(String, nullable=False)
    country = Column(String, nullable=False)
    operator = Column(String, nullable=False)
    active = Column(Boolean, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)


class CrewCarbonLabReadings(Base):
    __tablename__ = 'crew_carbon_lab_readings'
    id = Column(Integer, primary_key=True, autoincrement=True)
    reading_id = Column(String, nullable=True)
    plant_id = Column(String, nullable=False, index=True)
    plant_unit_id = Column(String, nullable=True, index=False)
    source_file = Column(String, nullable=False)
    sensor_id = Column(String, nullable=True)
    datetime = Column(DateTime, nullable=False, index=True)
    parameter_name = Column(String, nullable=False, index=True)
    medium = Column(String, nullable=False, index=True)
    value = Column(Float, nullable=False)
    unit = Column(String, nullable=False)
    uncertainty = Column(Float, nullable=True)
    reading_metadata = Column(JSON, nullable=True)


class WasteWaterPlantOps(Base):
    """Raw operational data from wastewater plant"""
    __tablename__ = 'wastewater_plant_ops'

    id = Column(Integer, primary_key=True, autoincrement=True)
    plant_id = Column(String, nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)

    # Flow data
    actual_eff_flow_mgd = Column(Float, nullable=True)
    actual_inf_flow_mgd = Column(Float, nullable=True)
    max_eff_flow_mgd = Column(Float, nullable=True)
    min_eff_flow_mgd = Column(Float, nullable=True)
    bypass_flow_mgd = Column(Float, nullable=True)
    bypass_hours_per_day = Column(Float, nullable=True)

    # Chemistry measurements
    ca_upstream_mg_per_l = Column(
        Float, nullable=True, comment='Upstream calcium mg/L')
    ca_downstream_mg_per_l = Column(
        Float, nullable=True, comment='Downstream calcium mg/L')

    # Metadata
    source_file = Column(String(255), nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class CO2RemovalCalculation(Base):
    """Calculated CO2 removal with intermediate values"""
    __tablename__ = 'crew_carbon_co2_removal_calculations'

    id = Column(Integer, primary_key=True, autoincrement=True)
    # ops_id = Column(Integer, ForeignKey(
    #     'waste_water_plant_ops.id'), nullable=False, index=True)
    plant_id = Column(String, nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)

    # Inputs (denormalized)
    ca_upstream_mg_per_l = Column(Float, nullable=False)
    ca_downstream_mg_per_l = Column(Float, nullable=False)
    flow_mgd = Column(Float, nullable=False)

    # Intermediate calculations
    ca_delta_mg_per_l = Column(
        Float, nullable=False, comment='(Ca_downstream - Ca_upstream)')
    flow_m3_per_day = Column(Float, nullable=False, comment='Flow * 3785.41')
    flow_l_per_day = Column(Float, nullable=False, comment='Flow_m3 * 1000')
    ca_to_caco3_ratio = Column(
        Float, nullable=False, comment='CaCO3_mass / Ca_mass')
    co2_to_caco3_ratio = Column(
        Float, nullable=False, comment='CO2_mass / CaCO3_mass')
    caco3_mg = Column(Float, nullable=False,
                      comment='Ca_delta * Flow_L * ratio')
    co2_mg = Column(Float, nullable=False, comment='CaCO3_mg * ratio')

    # Final result
    co2_removed_metric_tons_per_day = Column(
        Float, nullable=False, comment='CO2_mg / 1e9')

    # Metadata
    calculation_version = Column(String(20), default='v1.0')
    quality_flag = Column(String(50), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
