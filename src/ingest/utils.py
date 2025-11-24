import pandas as pd
from typing import List, Dict, Optional
import logging
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from src.models.schemas import WastewaterPlant
from src.utils.logging_config import setup_logger

logger = setup_logger(__name__)


def create_wastewater_facilities(facility_data: list[dict], database_url: str = None) -> list[WastewaterPlant]:
    """
    Create wastewater facility records in the database

    Args:
        facility_data: List of dicts with facility information
        database_url: Database connection string (uses env var if not provided)

    Returns:
        List of created WastewaterPlant objects
    """
    if database_url is None:
        database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise ValueError("DATABASE_URL must be provided or set as environment variable")

    logger.info(f"Creating {len(facility_data)} wastewater facilities...")

    engine = create_engine(database_url)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    created_facilities = []

    try:
        for facility in facility_data:
            plant = WastewaterPlant(
                plant_id=facility.get("plant_id"),
                operator=facility.get("operator"),
                city=facility.get("city"),
                state=facility.get("state"),
                country=facility.get("country", "USA"),
                active=facility.get("active", True),
            )
            session.add(plant)
            created_facilities.append(plant)
            logger.info(f"  Added {plant.plant_id} in {plant.city}, {plant.state}")

        session.commit()
        logger.info(f"Successfully inserted {len(created_facilities)} waste water facilities")

        return created_facilities

    except Exception as e:
        session.rollback()
        logger.error(f"Error creating facilities: {e}")
        raise
    finally:
        session.close()


def transform_crew_data(
    df: pd.DataFrame,
    columns_to_keep: List[str],
    columns_rename_mapper: Optional[Dict[str, str]] = None,
    column_dtype_mapper: Optional[Dict[str, str]] = None,
    metadata_col_name: str = "reading_metadata",
    drop_duplicates: bool = True,
) -> pd.DataFrame:
    """
    Create DataFrame with selected columns, rename, cast dtypes, add metadata

    Args:
        df: Original DataFrame
        columns_to_keep: List of columns to keep
        columns_rename_mapper: Dictionary for renaming columns (e.g., {'old_name': 'new_name'})
        column_dtype_mapper: Dictionary for casting dtypes (e.g., {'col': 'float64'})
        metadata_col_name: Name for metadata column (default: 'metadata')
        drop_duplicates: Whether to drop duplicate rows (default: True)

    Returns:
        New DataFrame with selected columns + metadata

    Example:
        result = create_df_with_metadata(
            df=crew_lab_ca,
            columns_to_keep=['plant_id', 'date', 'value'],
            columns_rename_mapper={'plant_id': 'site_id'},
            column_dtype_mapper={'value': 'float64'}
        )
    """
    logger.info("Starting DataFrame transformation")
    logger.info(f"Input shape: {df.shape[0]} rows x {df.shape[1]} columns")

    # Step 0: Drop duplicate rows
    if drop_duplicates:
        logger.info("[transform_crew_data: Step 0/5] Removing duplicate rows")
        initial_row_count = len(df)
        df = df.drop_duplicates()
        final_row_count = len(df)
        duplicates_removed = initial_row_count - final_row_count

        if duplicates_removed > 0:
            logger.info(f"Removed {duplicates_removed} duplicate rows")
            logger.info(f"Rows before: {initial_row_count}, after: {final_row_count}")
        else:
            logger.info("No duplicate rows found")
    else:
        logger.info("[transform_crew_data: Step 0/5] Removing duplicate rows - SKIPPED")

    # Step 1: Select columns
    logger.info("[transform_crew_data:  Step 1/5] Selecting columns")
    missing_cols = [col for col in columns_to_keep if col not in df.columns]
    if missing_cols:
        logger.error(f"Columns not found in DataFrame: {missing_cols}")
        raise ValueError(f"Columns not found: {missing_cols}")

    new_df = df[columns_to_keep].copy()
    logger.info(f"Selected {len(columns_to_keep)} columns")

    # Step 2: Cast dtypes
    if column_dtype_mapper:
        logger.info("[transform_crew_data:  Step 2/5] Casting data types")
        valid_dtypes = {k: v for k, v in column_dtype_mapper.items() if k in new_df.columns}
        invalid_dtypes = set(column_dtype_mapper.keys()) - set(valid_dtypes.keys())

        if invalid_dtypes:
            logger.warning(f"Skipping dtypes for non-existent columns: {list(invalid_dtypes)}")

        if valid_dtypes:
            try:
                new_df = new_df.astype(valid_dtypes)
                logger.info(f"Successfully converted {len(valid_dtypes)} columns: {list(valid_dtypes.keys())}")
            except Exception as e:
                logger.error(f"Dtype conversion failed: {e}")
                raise
    else:
        logger.info("[transform_crew_data:  Step 2/5] Casting data types - SKIPPED")

    # Step 3: Rename columns
    if columns_rename_mapper:
        logger.info("[transform_crew_data:  Step 3/5] Renaming columns")
        valid_renames = {k: v for k, v in columns_rename_mapper.items() if k in new_df.columns}
        invalid_renames = set(columns_rename_mapper.keys()) - set(valid_renames.keys())

        if invalid_renames:
            logger.warning(f"Skipping renames for non-existent columns: {list(invalid_renames)}")

        if valid_renames:
            new_df = new_df.rename(columns=valid_renames)
            logger.info(f"Successfully renamed {len(valid_renames)} columns: {valid_renames}")
    else:
        logger.info("[transform_crew_data:  Step 3/5] Renaming columns - SKIPPED")

    # Step 4: Create metadata
    logger.info("[transform_crew_data:  Step 4/5] Creating metadata column")
    other_cols = [col for col in df.columns if col not in columns_to_keep]

    if other_cols:
        new_df[metadata_col_name] = df[other_cols].apply(dict, axis=1)
        logger.info(f"Created '{metadata_col_name}' column with {len(other_cols)} fields")
    else:
        new_df[metadata_col_name] = [{}] * len(df)
        logger.info(f"Created empty '{metadata_col_name}' column")

    # Step 5: Final summary
    logger.info("[transform_crew_data:  Step 5/5] Transformation complete")
    logger.info(f"Final shape: {new_df.shape[0]} rows x {new_df.shape[1]} columns")

    return new_df
