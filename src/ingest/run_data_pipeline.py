import json
import os

import pandas as pd
from sqlalchemy import create_engine, inspect

from src.ingest.ca_pipeline import run_ca_pipeline
from src.ingest.ph_pipeline import run_ph_pipeline
from src.models.schemas import CrewCarbonLabReadings
from src.utils.logging_config import setup_logger


def clean_and_filter_data(df):
    df_clean = df.copy()

    # Get schema column names
    schema_columns = [
        col.name for col in CrewCarbonLabReadings.__table__.columns if col.name != "id"
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
                cleaned = {k: (None if pd.isna(v) else v) for k, v 
                in obj.items()}
                return json.dumps(cleaned)
            return None

        df_clean["reading_metadata"] = df_clean["reading_metadata"].apply(
            safe_json_dumps
        )

        # Handle NaN/None in all columns
        df_clean = df_clean.where(pd.notnull(df_clean), None)
    return df_clean


if __name__ == "__main__":
    print("Starting data pipeline...")
    logger = setup_logger(__name__)
    DATABASE_URL = os.getenv("DATABASE_URL")
    engine = create_engine(DATABASE_URL)
    ca_data = run_ca_pipeline()
    inspector = inspect(engine)

    if "crew_carbon_lab_readings" not in inspector.get_table_names():
        # Create only the CrewLabReadings table
        CrewCarbonLabReadings.__table__.create(engine)
        print("Created table: crew_lab_readings")
    else:
        CrewCarbonLabReadings.__table__.drop(engine)
        print("Table crew_carbon_lab_readings already exists - dropping it")

    # Load your data
    ca_data = run_ca_pipeline()  # Calcium data
    ph_data = run_ph_pipeline()  # pH data (if separate)

    # Clean and filter both datasets
    ca_data_clean = clean_and_filter_data(ca_data)
    ph_data_clean = clean_and_filter_data(ph_data)

    # Write to database
    print(f"Writing {len(ca_data_clean)} calcium readings...")
    ca_data_clean.to_sql(
        CrewCarbonLabReadings.__tablename__,
        con=engine,
        if_exists="append",
        index=False,
        chunksize=500,
    )

    print(f"Writing {len(ph_data_clean)} pH readings...")
    ph_data_clean.to_sql(
        CrewCarbonLabReadings.__tablename__,
        con=engine,
        if_exists="append",
        index=False,
        chunksize=500,
    )

    print("✓ Successfully wrote all data to crew_carbon_lab_readings")
