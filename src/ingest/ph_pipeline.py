import json

import pandas as pd

from src.ingest.utils import transform_crew_data
from src.models.schemas import CrewCarbonLabReading
from src.utils.logging_config import setup_logger


def run_ph_pipeline():
    """
    runner for the logic behind
    the pH data ingest
    uses a generalized utility func
    called transform_crew_data
    """
    logger = setup_logger(__name__)
    FPATH1 = "data/minute_data/WB0038_PH_2025_sanitized.csv"
    FPATH2 = "data/minute_data/WB0039_PH_2025_sanitized.csv"
    minute_data_ph1 = pd.read_csv(FPATH1)
    minute_data_ph1["source_file"] = FPATH1
    logger.info(f"[run_ph_pipeline]: Done Loading CSV from {FPATH1}")

    minute_data_ph2 = pd.read_csv(FPATH2)
    minute_data_ph2["source_file"] = FPATH2
    logger.info(f"[run_ph_pipeline]: Done Loading CSV from {FPATH2}")

    ph_minute = pd.concat([minute_data_ph1, minute_data_ph2], ignore_index=True, sort=False)
    ph_minute["medium"] = "aqueous"

    transformed_ph_minute = transform_crew_data(
        df=ph_minute,
        columns_to_keep=[
            "Timestamp",
            "Measurement value",
            "Unit",
            "sensor_id",
            "unit_type_id",
            "plant_id",
            "Process value",
            "source_file",
            "medium",
        ],
        columns_rename_mapper={
            "Timestamp": CrewCarbonLabReading.datetime.name,
            "Measurement value": CrewCarbonLabReading.value.name,
            "Process value": CrewCarbonLabReading.parameter_name.name,
            "Unit": CrewCarbonLabReading.unit.name,
            "unit_type_id": CrewCarbonLabReading.plant_unit_id.name,
        },
        column_dtype_mapper={
            "Measurement value": "float64",
            "Timestamp": "datetime64[ns]",
        },
        metadata_col_name="reading_metadata",
    )
    logger.info(f"[run_ph_pipeline]: Done transforming `transformed_ph_minute` ")

    transformed_ph_minute["reading_metadata"] = transformed_ph_minute["reading_metadata"].apply(
        lambda x: (json.dumps({k: (None if pd.isna(v) else v) for k, v in x.items()}) if isinstance(x, dict) else None)
    )
    logger.info(f"[run_ph_pipeline]: Done compressing `reading_metadata` ")

    return transformed_ph_minute
