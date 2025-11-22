from sqlalchemy.orm import Session
from sqlalchemy import create_engine, select
from datetime import date, datetime
import pandas as pd
from src.models.schemas import CO2RemovalCalculation, CrewCarbonLabReadings, WasteWaterPlantOps, WastewaterPlants
from sqlalchemy.sql import func
from sqlalchemy.orm import sessionmaker


def calculate_co2_removal_from_sources(
    session: Session,
    plant_id: str,  # Changed to String
    calc_date: date,
    quality_flag: str = None
) -> CO2RemovalCalculation:
    """
    Calculate CO2 removal by joining ops data and lab readings

    Args:
        session: SQLAlchemy session
        plant_id: Plant identifier (string like 'PLANT_A')
        calc_date: Date to calculate for
        quality_flag: Optional quality flag

    Returns:
        CO2RemovalCalculation record
    """

    # Get ops data for this plant and date
    ops = session.query(WasteWaterPlantOps).filter(
        WasteWaterPlantOps.plant_id == plant_id,
        WasteWaterPlantOps.date == calc_date
    ).first()

    if not ops:
        raise ValueError(f"No ops data found for {plant_id} on {calc_date}")

    # Get calcium readings for this plant and date
    # Assuming upstream is 'primary_clarifier' and downstream is 'secondary_clarifier'
    ca_upstream_reading = session.query(CrewCarbonLabReadings).filter(
        CrewCarbonLabReadings.plant_id == plant_id,
        CrewCarbonLabReadings.parameter_name == 'calcium',
        CrewCarbonLabReadings.plant_unit_id == 'primary_clarifier',
        func.date(CrewCarbonLabReadings.datetime) == calc_date
    ).first()

    ca_downstream_reading = session.query(CrewCarbonLabReadings).filter(
        CrewCarbonLabReadings.plant_id == plant_id,
        CrewCarbonLabReadings.parameter_name == 'calcium',
        CrewCarbonLabReadings.plant_unit_id == 'secondary_clarifier',
        func.date(CrewCarbonLabReadings.datetime) == calc_date
    ).first()

    if not ca_upstream_reading or not ca_downstream_reading:
        raise ValueError(
            f"Missing calcium readings for {plant_id} on {calc_date}")

    # Extract values
    ca_upstream = ca_upstream_reading.value
    ca_downstream = ca_downstream_reading.value
    flow_mgd = ops.actual_eff_flow_mgd

    if flow_mgd is None:
        raise ValueError(f"No flow data for {plant_id} on {calc_date}")

    # Calculate intermediate values
    ca_delta = ca_downstream - ca_upstream
    flow_m3_day = flow_mgd * 3785.41
    flow_l_day = flow_m3_day * 1000

    # Molecular weights (g/mol) - hardcoded for reliability
    MW_Ca = 40.078
    MW_CaCO3 = 100.0869
    MW_CO2 = 44.0095

    # Calculate intermediate values
    ca_delta = ca_downstream - ca_upstream
    flow_m3_day = flow_mgd * 3785.41
    flow_l_day = flow_m3_day * 1000

    # Molecular weight ratios
    ca_to_caco3 = MW_CaCO3 / MW_Ca
    co2_to_caco3 = MW_CO2 / MW_CaCO3

    # Mass calculations
    caco3_mg = ca_delta * flow_l_day * ca_to_caco3
    co2_mg = caco3_mg * co2_to_caco3
    co2_mt_day = co2_mg / 1_000_000_000

    # Store calculation
    calc = CO2RemovalCalculation(
        plant_id=plant_id,  # Now a string
        date=calc_date,
        ca_upstream_mg_per_l=ca_upstream,
        ca_downstream_mg_per_l=ca_downstream,
        flow_mgd=flow_mgd,
        ca_delta_mg_per_l=ca_delta,
        flow_m3_per_day=flow_m3_day,
        flow_l_per_day=flow_l_day,
        ca_to_caco3_ratio=ca_to_caco3,
        co2_to_caco3_ratio=co2_to_caco3,
        caco3_mg=caco3_mg,
        co2_mg=co2_mg,
        co2_removed_metric_tons_per_day=co2_mt_day,
        quality_flag=quality_flag
    )

    session.add(calc)
    session.commit()
    return calc


def bulk_calculate_co2_removal(
    session: Session,
    plant_id: str,
    start_date: date = None,
    end_date: date = None
) -> list[CO2RemovalCalculation]:
    """Calculate CO2 removal for a range of dates"""

    # Get all ops dates for this plant
    query = session.query(WasteWaterPlantOps.date).filter(
        WasteWaterPlantOps.plant_id == plant_id
    )

    if start_date:
        query = query.filter(WasteWaterPlantOps.date >= start_date)
    if end_date:
        query = query.filter(WasteWaterPlantOps.date <= end_date)

    dates = [row[0] for row in query.distinct().all()]

    results = []
    for calc_date in dates:
        try:
            calc = calculate_co2_removal_from_sources(
                session=session,
                plant_id=plant_id,
                calc_date=calc_date,
                quality_flag='VALID'
            )
            results.append(calc)
            print(
                f"✓ Calculated CO2 for {plant_id} on {calc_date}: {calc.co2_removed_metric_tons_per_day:.6f} MT/day")
        except ValueError as e:
            print(f"✗ Skipped {calc_date}: {e}")

    return results


# Usage
if __name__ == "__main__":
    DATABASE_URL = os.getenv('DATABASE_URL')
    engine = create_engine(DATABASE_URL)
    CO2RemovalCalculation.__table__.drop(engine, checkfirst=True)
    CO2RemovalCalculation.__table__.create(engine, checkfirst=True)

    Session = sessionmaker(bind=engine)
    session = Session()

    plants = ['PLANT_A', 'PLANT_B']
    all_results = {}

    for plant_id in plants:
        print(f"\n=== Calculating {plant_id} ===")
        results = bulk_calculate_co2_removal(
            session=session,
            plant_id=plant_id,
            start_date=date(2025, 4, 1),
            end_date=date(2025, 6, 30)
        )
        all_results[plant_id] = results

        total_co2 = sum(r.co2_removed_metric_tons_per_day for r in results)
        avg_co2 = total_co2 / len(results) if results else 0

        print(f"✓ {plant_id}: {len(results)} dates")
        print(f"  Total CO2: {total_co2:.2f} MT")
        print(f"  Avg daily: {avg_co2:.4f} MT/day")

    # Grand total
    grand_total = sum(
        sum(r.co2_removed_metric_tons_per_day for r in results)
        for results in all_results.values()
    )
    print(f"\n=== Grand Total CO2 Removed: {grand_total:.2f} MT ===")
