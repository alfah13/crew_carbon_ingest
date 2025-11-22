import pandas as pd

from src.models.schemas import WasteWaterPlantOps
from src.utils.logging_config import setup_logger

logger = setup_logger(__name__)


def run_ops_plant_a():

    plant_a_apr25_fpath = pd.read_excel("data/ops/PLANT_A-OPS DATA-APR25.xlsx")
    plant_a_jun25_fpath = pd.read_excel("data/ops/PLANT_A-OPS DATA-JUNE25.xls")
    plant_a_may25_fpath = pd.read_excel("data/ops/PLANT_A-OPS DATA-MAY25.xls")
    print("done loading files")
    # Define all column mappings
    OPERATOR_COLUMN_MAPPING = {
        "Plnt Ef_50050_FLOW MGD_MGD_Daily": "actual_eff_flow_mgd",
        "Max Effluent Flow_50047_FLOW MAX MGD_MGD_Daily": "max_eff_flow_mgd",
        "Min Effluent Flow_50048_FLOW MIN MGD_MGD_Daily": "min_eff_flow_mgd",
        "Bypass_50050_FLOW MGD_MGD_Daily": "bypass_flow_mgd",
        "Bypass_DIVERSION/HRS_HRS/DAY_Daily": "bypass_hours_per_day",
        "INFLUENT DATA_1_RAW_INF_FLOW_Unnamed: 1_level_5_MGD": "raw_influent_flow_mgd",
        "EFFLUENT DATA_7_FIN_EFF_FLOW_Unnamed: 7_level_5_MGD": "fin_eff_flow_mgd",
    }

    def standardize_operator_columns(df, date_col_pattern=None):
        """
        Standardize operator data column names

        Args:
            df: DataFrame with operator data
            date_col_pattern: Pattern to identify date column (optional)

        Returns:
            DataFrame with standardized column names
        """
        logger.info(
            f"Standardizing columns for dataframe with {len(df.columns)} columns"
        )

        # Replace \n with underscores
        df.columns = df.columns.str.replace("\n", "_")

        # Rename known columns
        existing_renames = {
            k: v for k, v in OPERATOR_COLUMN_MAPPING.items() if k in df.columns
        }
        df.rename(columns=existing_renames, inplace=True)

        logger.info(f"Renamed {len(existing_renames)} columns")

        # Handle date column if pattern provided
        if date_col_pattern:
            date_cols = [col for col in df.columns if date_col_pattern in col]
            if date_cols:
                df.rename(columns={date_cols[0]: "date"}, inplace=True)
                logger.info(f"Renamed date column: {date_cols[0]} -> date")

        return df[
            [
                "date",
                "actual_eff_flow_mgd",
                "max_eff_flow_mgd",
                "min_eff_flow_mgd",
                "bypass_flow_mgd",
                "bypass_hours_per_day",
            ]
        ]

    # Usage
    plant_a_apr25_fpath = standardize_operator_columns(
        plant_a_apr25_fpath, date_col_pattern="OPERATOR DATA_Daily_4"
    )
    plant_a_apr25_fpath["source_file"] = "PLANT_A-OPS DATA-APR25"
    plant_a_apr25_fpath["plant_id"] = "PLANT_A"

    plant_a_may25_fpath = standardize_operator_columns(
        plant_a_may25_fpath, date_col_pattern="OPERATOR DATA_Daily_5"
    )
    plant_a_may25_fpath["source_file"] = "PLANT_A-OPS DATA-JUNE25"
    plant_a_may25_fpath["plant_id"] = "PLANT_A"

    plant_a_jun25_fpath = standardize_operator_columns(
        plant_a_jun25_fpath, date_col_pattern="OPERATOR DATA_Daily_6"
    )
    plant_a_jun25_fpath["source_file"] = "PLANT_A-OPS DATA-MAY25"
    plant_a_jun25_fpath["plant_id"] = "PLANT_A"

    plant_a_combined_df = pd.concat(
        [plant_a_apr25_fpath, plant_a_may25_fpath, plant_a_jun25_fpath],
        ignore_index=True,
    )

    plant_a_combined_df["date"] = pd.to_datetime(
        plant_a_combined_df["date"], errors="coerce"
    )

    plant_a_combined_df =
    plant_a_combined_df[
        plant_a_combined_df["date"].notna()]

    logger.info("All dataframes standardized")

    return plant_a_combined_df


if __name__ == "__main__":
    import os

    import pandas as pd
    from sqlalchemy import create_engine

    from src.models.schemas import WasteWaterPlantOps
    from src.utils.logging_config import setup_logger

    DATABASE_URL = os.getenv("DATABASE_URL")
    engine = create_engine(DATABASE_URL)
    # TODO
    ##
    # WasteWaterPlantOps.__table__.drop(engine)

    WasteWaterPlantOps.__table__.create(engine)
    ops_plant_data = run_ops_plant_a()

    print(f"Writing {len(ops_plant_data)} ops_plant_data...")
    ops_plant_data.to_sql(
        name=WasteWaterPlantOps.__tablename__,
        con=engine,
        # schema=WasteWaterPlantOps,
        if_exists="append",
        index=False,
        chunksize=500,
    )
    print("✓ Successfully wrote all data to ops_plant_data")
