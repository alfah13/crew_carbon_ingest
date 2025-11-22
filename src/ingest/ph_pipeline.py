import json
import logging

import pandas as pd

from src.ingest.utils import transform_crew_data
from src.models.schemas import CrewCarbonLabReadings


def run_ph_pipeline():
    logger = logging.getLogger(__name__)
    FPATH1 = "data/minute_data/WB0038_PH_2025_sanitized.csv"
    FPATH2 = "data/minute_data/WB0039_PH_2025_sanitized.csv"
    minute_data_ph1 = pd.read_csv(FPATH1)
    minute_data_ph1["source_file"] = FPATH1

    minute_data_ph2 = pd.read_csv(FPATH2)
    minute_data_ph2["source_file"] = FPATH2

    ph_minute = pd.concat(
        [minute_data_ph1, minute_data_ph2], ignore_index=True, sort=False
    )
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
            "Timestamp": CrewCarbonLabReadings.datetime.name,
            "Measurement value": CrewCarbonLabReadings.value.name,
            "Process value": CrewCarbonLabReadings.parameter_name.name,
            "Unit": CrewCarbonLabReadings.unit.name,
            "unit_type_id": CrewCarbonLabReadings.plant_unit_id.name,
        },
        column_dtype_mapper={
            CrewCarbonLabReadings.value.name: "float64",
            CrewCarbonLabReadings.datetime.name: "datetime64[ns]",
        },
        metadata_col_name="reading_metadata",
    )

    transformed_ph_minute["reading_metadata"] = transformed_ph_minute[
        "reading_metadata"
    ].apply(
        lambda x: (
            json.dumps({k: (None if pd.isna(v) else v) for k, v in x.items()})
            if isinstance(x, dict)
            else None
        )
    )

    return transformed_ph_minute
