# src/models/mrv_schemas.py
"""
MRV (Monitoring, Reporting, Verification) data models
"""
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Date,
    Text, DECIMAL, ForeignKey, Index, TIMESTAMP
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

from src.models.schemas import Base

class CalciumMeasurement(Base):
    """
    Dissolved calcium measurements from lab analysis
    Used for CaCO3 dissolution calculations
    """
    __tablename__ = 'calcium_measurements'
    
    timestamp = Column(TIMESTAMP(timezone=True), nullable=False, primary_key=True)
    plant_id = Column(String(50), ForeignKey('wastewater_facilities.plant_id'), nullable=False, primary_key=True)
    sample_id = Column(String(100), nullable=False, primary_key=True)
    
    # Measurement location
    location_type = Column(String(50), nullable=False)  # 'primary_clarifier' or 'secondary_clarifier'
    
    # Dissolved calcium concentration
    ca_concentration_mg_l = Column(DECIMAL(12, 6), nullable=False, comment="Dissolved calcium in mg/L")
    
    # Quality metadata
    quality_flag = Column(String(20), default='valid')
    detection_limit_mg_l = Column(DECIMAL(12, 6))
    lab_name = Column(String(255))
    analysis_method = Column(String(100))
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    plant = relationship("WasteWaterFacilities")
    
    __table_args__ = (
        Index('idx_calcium_plant_time', 'plant_id', 'timestamp'),
        Index('idx_calcium_location', 'location_type', 'timestamp'),
    )


class FlowMeasurement(Base):
    """
    Wastewater flow measurements
    Typically reported in Million Gallons per Day (MGD)
    """
    __tablename__ = 'flow_measurements'
    
    timestamp = Column(TIMESTAMP(timezone=True), nullable=False, primary_key=True)
    plant_id = Column(String(50), ForeignKey('wastewater_facilities.plant_id'), nullable=False, primary_key=True)
    
    # Flow rate
    flow_mgd = Column(DECIMAL(12, 6), nullable=False, comment="Flow in Million Gallons per Day")
    flow_m3_day = Column(DECIMAL(12, 6), comment="Flow in cubic meters per day (calculated)")
    
    # Quality metadata
    quality_flag = Column(String(20), default='valid')
    measurement_type = Column(String(50))  # 'influent', 'effluent', etc.
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    plant = relationship("WasteWaterFacilities")
    
    __table_args__ = (
        Index('idx_flow_plant_time', 'plant_id', 'timestamp'),
    )


class CaCO3DissolutionDaily(Base):
    """
    Daily CaCO3 dissolution calculations
    CaCO3 dissolution = Ca²⁺(downstream) - Ca²⁺(upstream)
    """
    __tablename__ = 'caco3_dissolution_daily'
    
    date = Column(Date, nullable=False, primary_key=True)
    plant_id = Column(String(50), ForeignKey('wastewater_facilities.plant_id'), nullable=False, primary_key=True)
    
    # Calcium measurements
    ca_upstream_mg_l = Column(DECIMAL(12, 6), comment="Upstream Ca concentration (primary clarifier)")
    ca_downstream_mg_l = Column(DECIMAL(12, 6), comment="Downstream Ca concentration (secondary clarifier)")
    ca_delta_mg_l = Column(DECIMAL(12, 6), comment="Change in Ca concentration")
    
    # Flow data
    avg_flow_mgd = Column(DECIMAL(12, 6), comment="Average daily flow in MGD")
    avg_flow_m3_day = Column(DECIMAL(12, 6), comment="Average daily flow in m³/day")
    
    # CaCO3 dissolution
    caco3_dissolution_kg_day = Column(DECIMAL(15, 6), comment="CaCO3 dissolution in kg/day")
    caco3_dissolution_metric_tons_day = Column(DECIMAL(15, 9), comment="CaCO3 dissolution in metric tons/day")
    
    # Data quality
    data_coverage_percent = Column(DECIMAL(5, 2), comment="Percentage of valid data points")
    quality_score = Column(String(20), comment="overall, good, fair, poor")
    notes = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    plant = relationship("WasteWaterFacilities")
    
    __table_args__ = (
        Index('idx_caco3_plant_date', 'plant_id', 'date'),
    )


class CO2RemovalDaily(Base):
    """
    Daily CO2 removal calculations
    CO2 removal = quantity of CO2 converted to HCO3⁻ via CaCO3 dissolution
    """
    __tablename__ = 'co2_removal_daily'
    
    date = Column(Date, nullable=False, primary_key=True)
    plant_id = Column(String(50), ForeignKey('wastewater_facilities.plant_id'), nullable=False, primary_key=True)
    
    # CaCO3 dissolution (input)
    caco3_dissolution_metric_tons = Column(DECIMAL(15, 9), comment="CaCO3 dissolved in metric tons")
    
    # CO2 removal (output)
    co2_removed_kg_day = Column(DECIMAL(15, 6), comment="CO2 removed in kg/day")
    co2_removed_metric_tons_day = Column(DECIMAL(15, 9), comment="CO2 removed in metric tons/day")
    co2_removed_metric_tons_cumulative = Column(DECIMAL(15, 9), comment="Cumulative CO2 removed")
    
    # Verification status
    verified = Column(Boolean, default=False)
    verification_date = Column(Date)
    verifier = Column(String(255))
    
    # Data quality
    confidence_level = Column(DECIMAL(5, 2), comment="Confidence percentage")
    quality_score = Column(String(20))
    notes = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    plant = relationship("WasteWaterFacilities")
    
    __table_args__ = (
        Index('idx_co2_plant_date', 'plant_id', 'date'),
    )
