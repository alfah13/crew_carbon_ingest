from src.ingest.utils import transform_crew_data
from src.models.schemas import CrewCarbonLabReadings
import pandas as pd
import json


def run_ca_pipeline():
    FPATH = "data/crew_lab/IC_calcium.csv"
    crew_lab_ca = pd.read_csv(FPATH)
    crew_lab_ca["source_file"] = FPATH

    transformed_crew_lab_ca = transform_crew_data(
        df=crew_lab_ca,
        columns_to_keep=[
            "unique_id",
            "plant_id",
            "unit_type_id",
            "date",
            "parameter_name",
            "value",
            "units",
            "source_file",
            "uncertainty",
            "medium",
        ],
        columns_rename_mapper={
            "date": CrewCarbonLabReadings.datetime.name,
            "unit_type_id": CrewCarbonLabReadings.plant_unit_id.name,
            "unique_id": CrewCarbonLabReadings.reading_id.name,
            "units": CrewCarbonLabReadings.unit.name,
        },
        column_dtype_mapper={
            "value": "float64",
            "uncertainty": "float64",
            "plant_id": "string",
            "date": "datetime64[ns]",
        },
        metadata_col_name="reading_metadata",
    )
    transformed_crew_lab_ca["reading_metadata"] = transformed_crew_lab_ca[
        "reading_metadata"
    ].apply(
        lambda x: (
            json.dumps({k: (None if pd.isna(v) else v) for k, v in x.items()})
            if isinstance(x, dict)
            else None
        )
    )

    return transformed_crew_lab_ca
