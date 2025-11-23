import json
import os

import pandas as pd
from sqlalchemy import create_engine, inspect

from src.ingest.ca_pipeline import run_ca_pipeline
from src.ingest.ph_pipeline import run_ph_pipeline
from src.ingest.ops_plant_a_pipeline import run_ops_plant_a
from src.ingest.ops_plant_b_pipeline import run_ops_plant_b

from src.models.schemas import CrewCarbonLabReading, WasteWaterPlantOperation
from src.utils.logging_config import setup_logger


def clean_and_filter_data(df):
    df_clean = df.copy()

    # Get schema column names
    schema_columns = [
        col.name for col in CrewCarbonLabReading.__table__.columns if col.name != "id"
    ]

    # Filter DataFrame to only include columns in schema
    available_cols = [col for col in schema_columns if col in df_clean.columns]
    df_clean = df_clean[available_cols]

    # Clean metadata JSON
    if "reading_metadata" in df_clean.columns:

        def safe_json_dumps(obj):
            if obj is None or pd.isna(obj):
                return None
            if isinstance(obj, dict):
                cleaned = {k: (None if pd.isna(v) else v) for k, v in obj.items()}
                return json.dumps(cleaned)
            return None

        df_clean["reading_metadata"] = df_clean["reading_metadata"].apply(
            safe_json_dumps
        )

        # Handle NaN/None in all columns
        df_clean = df_clean.where(pd.notnull(df_clean), None)
    return df_clean


if __name__ == "__main__":
    logger = setup_logger(__name__)
    DATABASE_URL = os.getenv("DATABASE_URL")
    engine = create_engine(DATABASE_URL)
    inspector = inspect(engine)
    logger.info("Starting data pipeline...")

    # Load your data
    ca_data = run_ca_pipeline()  # Calcium data
    ph_data = run_ph_pipeline()  # pH data (if separate)

    # Clean and filter both datasets
    ca_data_clean = clean_and_filter_data(ca_data)
    ph_data_clean = clean_and_filter_data(ph_data)

    # Write to database
    logger.info(f"Writing {len(ca_data_clean)} calcium readings...")
    ca_data_clean.to_sql(
        CrewCarbonLabReading.__tablename__,
        con=engine,
        if_exists="append",
        index=False,
        chunksize=500,
    )
    logger.info(f"Successfully wrote {len(ca_data_clean)} rows to CrewCarbonLabReading")

    logger.info(f"Writing {len(ph_data_clean)} pH readings...")
    ph_data_clean.to_sql(
        CrewCarbonLabReading.__tablename__,
        con=engine,
        if_exists="append",
        index=False,
        chunksize=500,
    )

    logger.info(f"Successfully wrote {len(ph_data_clean)} rows to CrewCarbonLabReading")

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
