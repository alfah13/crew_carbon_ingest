import os

import pandas as pd
from sqlalchemy import create_engine

from src.models.schemas import WasteWaterPlantOperation
from src.utils.logging_config import setup_logger


def run_ops_plant_b():
    logger = setup_logger(__name__)

    files = {
        "plant_b_mar25": "data/ops/PLANT_B-MPOR_Crew_04042025to04252025.xlsx",
        "plant_b_apr25_1": "data/ops/PLANT_B-MPOR_Crew_04042025to04252025.xlsx",
        "plant_b_apr25_2": "data/ops/PLANT_B-MPOR_Crew_04182025to05232025.xlsx",
        "plant_b_may25_1": "data/ops/PLANT_B-MPOR_Crew_05162025to06072025.xlsx",
        "plant_b_may25_2": "data/ops/PLANT_B-MPOR_Crew_05302025to06232025.xlsx",
        "plant_b_jun25": "data/ops/PLANT_B-MPOR_Crew_06132025to07112025.xlsx",
    }

    # Values to exclude from date column
    exclude_values = ["TOTAL", "MAX", "MIN", "AVG"]

    all_dataframes = []

    logger.info(f"Loading {len(files)} files")

    for name, fpath in files.items():
        try:
            logger.info(f"Loading {name}...")
            df = pd.read_excel(fpath, header=[5, 6, 7, 8, 9, 10, 11])

            # Clean columns
            df.columns = ["_".join(str(x) for x in col).strip() for col in df.columns.values]

            initial_rows = len(df)

            # Drop all-NaN rows
            df = df.dropna(how="all")
            dropped_all_na = initial_rows - len(df)

            # Drop rows with summary statistics
            date_col = (
                [col for col in df.columns if "DATE" in col][0] if any("DATE" in col for col in df.columns) else None
            )

            if date_col:
                df = df[~df[date_col].isin(exclude_values)]
                dropped_summaries = initial_rows - dropped_all_na - len(df)
                logger.info(f"  Dropped {dropped_summaries} rows with TOTAL/MAX/MIN/AVG")
            else:
                dropped_summaries = 0
                logger.warning("  Could not find DATE column to filter TOTAL/MAX/MIN/AVG")

            df["source_file"] = name
            df["plant_id"] = "PLANT_B"
            all_dataframes.append(df)

            logger.info(
                f"  Final {name}: {len(df)} rows (dropped {dropped_all_na} all-NaN, {dropped_summaries} summary stats)"
            )
        except Exception as e:
            logger.error(f"  Failed to load {name}: {e}")

    # Combine all
    combined_df = pd.concat(all_dataframes, ignore_index=True)
    combined_df.rename(
        columns={
            "EFFLUENT DATA_7_FIN_EFF_FLOW_Unnamed: 7_level_5_MGD": "actual_eff_flow_mgd",
            "INFLUENT DATA_1_RAW_INF_FLOW_Unnamed: 1_level_5_MGD": "actual_inf_flow_mgd",
            "Unnamed: 0_level_0_Unnamed: 0_level_1_DATE_Unnamed: 0_level_3_Unnamed: 0_level_4_Unnamed: 0_level_5_Unnamed: 0_level_6": "date",
        },
        inplace=True,
    )

    logger.info(f"Combined: {combined_df.shape[0]} rows x {combined_df.shape[1]} columns")
    combined_df["date"] = pd.to_datetime(combined_df["date"], errors="coerce")

    # Keep only valid dates
    combined_df = combined_df[combined_df["date"].notna()]

    return combined_df[
        [
            "actual_eff_flow_mgd",
            "actual_inf_flow_mgd",
            "date",
            "plant_id",
            "source_file",
        ]
    ]
