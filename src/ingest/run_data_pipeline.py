import json
import os

import pandas as pd
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

from src.ingest.ca_pipeline import run_ca_pipeline
from src.ingest.ops_plant_a_pipeline import run_ops_plant_a
from src.ingest.ops_plant_b_pipeline import run_ops_plant_b
from src.ingest.ph_pipeline import run_ph_pipeline
from src.ingest.utils import create_wastewater_facilities
from src.models.schemas import (CrewCarbonLabReading,
                                WasteWaterPlantOperation)
from src.utils.logging_config import setup_logger

DATABASE_URL = os.getenv("DATABASE_URL")

if __name__ == "__main__":
    logger = setup_logger(__name__)
    engine = create_engine(DATABASE_URL)
    inspector = inspect(engine)

    logger.info("Starting data pipeline...")

    # Step 1: Create Waste Water Plants by defining their params
    facilities_to_create = [
        {
            "plant_id": "PLANT_A",
            "operator": "Connecticut Water Authority",
            "city": "New Haven",
            "state": "CT",
            "country": "USA",
            "active": True,
        },
        {
            "plant_id": "PLANT_B",
            "operator": "New York City DEP",
            "city": "New York",
            "state": "NY",
            "country": "USA",
            "active": False,
        },
    ]

    created_plants = create_wastewater_facilities(facilities_to_create)

    # Step 2: Start the transformation of the chemical data
    ca_data = run_ca_pipeline()  # Calcium data transformation
    ph_data = run_ph_pipeline()  # pH data transformation

    # 
    ca_data_clean = ca_data # clean_and_filter_data(ca_data)
    ph_data_clean = ph_data # clean_and_filter_data(ph_data)

    # Step 2: write the transformed data to tables
    logger.info(f"Writing {len(ca_data)} calcium readings...")
    ca_data.to_sql(
        CrewCarbonLabReading.__tablename__,
        con=engine,
        if_exists="append",
        index=False,
        chunksize=500,
    )
    logger.info(f"Successfully wrote {len(ca_data)} rows to CrewCarbonLabReading")

    logger.info(f"Writing {len(ph_data)} pH readings...")
    ph_data.to_sql(
        CrewCarbonLabReading.__tablename__,
        con=engine,
        if_exists="append",
        index=False,
        chunksize=500,
    )

    logger.info(f"Successfully wrote {len(ph_data)} rows to CrewCarbonLabReading")

    # Step 3: Transform the plan ops data (PLANT A)
    ops_plant_data_a = run_ops_plant_a()

    logger.info(f"Writing {len(ops_plant_data_a)} WasteWaterPlantOperation...")
    ops_plant_data_a.to_sql(
        name=WasteWaterPlantOperation.__tablename__,
        con=engine,
        if_exists="append",
        index=False,
        chunksize=500,
    )
    logger.info(f"Successfully wrote {len(ops_plant_data_a)} rows to WasteWaterPlantOperation")

    # Step 3: Transform the plan ops data (PLANT B)
    ops_plant_data_b = run_ops_plant_b()

    logger.info(f"Writing {len(ops_plant_data_b)} WasteWaterPlantOperation...")
    ops_plant_data_b.to_sql(
        name=WasteWaterPlantOperation.__tablename__,
        con=engine,
        if_exists="append",
        index=False,
        chunksize=500,
    )
    logger.info(f"Successfully wrote {len(ops_plant_data_b)} rows to WasteWaterPlantOperation")
