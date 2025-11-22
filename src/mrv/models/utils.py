from sqlalchemy.orm import Session
from chempy import Formula
from datetime import date


def calculate_co2_removal(
    session: Session,
    ops_id: int,
    plant_id: int,
    calc_date: date,
    ca_upstream: float,
    ca_downstream: float,
    flow_mgd: float,
    quality_flag: str = None
) -> CO2RemovalCalculation:
    """Calculate and store CO2 removal"""
    
    # Calculate intermediate values
    ca_delta = ca_downstream - ca_upstream
    flow_m3_day = flow_mgd * 3785.41
    flow_l_day = flow_m3_day * 1000
    
    # Molecular weight ratios
    ca_to_caco3 = Formula('CaCO3').mass / Formula('Ca').mass
    co2_to_caco3 = Formula('CO2').mass / Formula('CaCO3').mass
    
    # Mass calculations
    caco3_mg = ca_delta * flow_l_day * ca_to_caco3
    co2_mg = caco3_mg * co2_to_caco3
    co2_mt_day = co2_mg / 1_000_000_000
    
    # Store calculation
    calc = CO2RemovalCalculation(
        ops_id=ops_id,
        plant_id=plant_id,
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


# Usage
if __name__ == "__main__":
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    engine = create_engine('postgresql://user:password@localhost:5432/wastewater_db')
    Base.metadata.create_all(engine)
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Insert ops data
    ops = WasteWaterPlantOps(
        plant_id=1,
        date=date(2025, 11, 21),
        actual_eff_flow_mgd=12.5,
        ca_upstream_mg_per_l=50.0,
        ca_downstream_mg_per_l=45.0,
        source_file='data_2025-11-21.csv'
    )
    session.add(ops)
    session.commit()
    
    # Calculate CO2 removal
    result = calculate_co2_removal(
        session=session,
        ops_id=ops.id,
        plant_id=ops.plant_id,
        calc_date=ops.date,
        ca_upstream=ops.ca_upstream_mg_per_l,
        ca_downstream=ops.ca_downstream_mg_per_l,
        flow_mgd=ops.actual_eff_flow_mgd,
        quality_flag='VALID'
    )
    
    print(f"CO2 removed: {result.co2_removed_metric_tons_per_day:.6f} MT/day")
