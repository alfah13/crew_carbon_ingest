"""
We define four schemas that help us normalized both the input data and the MRV calculation data
"""

from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    Integer,
    String,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class WastewaterPlant(Base):
    __tablename__ = "wastewater_plant_metadata"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="internal id for each ww plant")
    plant_id = Column(String, nullable=False, comment="human readable id for each ww plant")
    city = Column(String, nullable=False, comment="city of ww plant")
    state = Column(String, nullable=False, comment="state/region where plant is located")
    country = Column(String, nullable=False, comment="country where plant is located")
    operator = Column(String, nullable=False, comment="organization operating the plant")
    active = Column(Boolean, nullable=False, comment="status of plant - 0 = inactive, 1 = active")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CrewCarbonLabReading(Base):
    __tablename__ = "crewcarbon_lab_reading"
    id = Column(Integer, primary_key=True, autoincrement=True, comment="internal id for each reading")
    reading_id = Column(String, nullable=True, comment="id for each reading per source doocument")
    plant_id = Column(String, nullable=False, index=True, comment="human readable id for each ww plant")
    plant_unit_id = Column(
        String,
        nullable=True,
        index=False,
        comment="human readable id for each ww plant unit - can be primary calrifier or secondary clarifier",
    )
    source_file = Column(String, nullable=False, comment="file where data came from")
    sensor_id = Column(String, nullable=True, comment="sensor that value was collected by - if available")
    datetime = Column(DateTime, nullable=False, index=True, comment="date and time of measurement")
    parameter_name = Column(String, nullable=False, index=True, comment="Atom, Compound, or Parameter")
    medium = Column(String, nullable=False, index=True, comment="Physical medium such as aqeous")
    value = Column(Float, nullable=False, comment="actual value of reading")
    unit = Column(String, nullable=False, comment="actual unit of reading")
    uncertainty = Column(Float, nullable=True, comment="uncertainty reading from source file")
    reading_metadata = Column(JSON, nullable=True, comment="all other information")


class WasteWaterPlantOperation(Base):
    """Raw operational data from wastewater plant"""

    __tablename__ = "wastewater_plant_operation"

    id = Column(Integer, primary_key=True, autoincrement=True)
    plant_id = Column(String, nullable=False, index=True, comment="human readable id for each ww plant")
    date = Column(Date, nullable=False, index=True, comment="date of reading")

    # Flow data
    actual_eff_flow_mgd = Column(Float, nullable=True, comment="effluent flow of ww plant")
    actual_inf_flow_mgd = Column(Float, nullable=True, comment="influent flow of ww plant")
    max_eff_flow_mgd = Column(Float, nullable=True)
    min_eff_flow_mgd = Column(Float, nullable=True)
    bypass_flow_mgd = Column(Float, nullable=True, comment="bypass flow of ww plant")
    bypass_hours_per_day = Column(Float, nullable=True, comment="bypass hours of ww plant")

    # Chemistry measurements
    ca_upstream_mg_per_l = Column(Float, nullable=True, comment="Upstream calcium mg/L")
    ca_downstream_mg_per_l = Column(Float, nullable=True, comment="Downstream calcium mg/L")

    # Metadata
    source_file = Column(String(255), nullable=False, comment="file where data came from")
    created_at = Column(DateTime, server_default=func.now())


class CO2RemovalCalculation(Base):
    """Calculated CO2 removal with intermediate values"""

    __tablename__ = "crewcarbon_co2_removal_calculations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    # ops_id = Column(Integer, ForeignKey(
    #     'waste_water_plant_ops.id'), nullable=False, index=True)
    plant_id = Column(String, nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)

    # Inputs (denormalized)
    ca_upstream_mg_per_l = Column(Float, nullable=False, comment="Ca conc. at primary clarifier")
    ca_downstream_mg_per_l = Column(Float, nullable=False, comment="Ca conc. at secondary clarifier")
    flow_mgd = Column(Float, nullable=False, comment="plant flow rate in MGD")

    # Intermediate calculations
    ca_delta_mg_per_l = Column(Float, nullable=False, comment="(Ca_downstream - Ca_upstream)")
    flow_m3_per_day = Column(Float, nullable=False, comment="Flow * 3785.41")
    flow_l_per_day = Column(Float, nullable=False, comment="Flow_m3 * 1000")
    ca_to_caco3_ratio = Column(Float, nullable=False, comment="CaCO3_mass / Ca_mass")
    co2_to_caco3_ratio = Column(Float, nullable=False, comment="CO2_mass / CaCO3_mass")
    caco3_mg = Column(Float, nullable=False, comment="Ca_delta * Flow_L * ratio")
    co2_mg = Column(Float, nullable=False, comment="CaCO3_mg * ratio")

    # Final result
    co2_removed_metric_tons_per_day = Column(Float, nullable=False, comment="CO2_mg / 1e9")

    # Metadata
    calculation_version = Column(String(20), default="v1.0")
    quality_flag = Column(String(50), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
