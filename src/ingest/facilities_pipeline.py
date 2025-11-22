from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.models.schemas import WastewaterPlants
import os

if __name__ == "__main__":
    DATABASE_URL = os.getenv("DATABASE_URL")
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    # WastewaterPlants.__table__.drop(engine)
    WastewaterPlants.__table__.create(engine)
    # Create facilities
    plant_a = WastewaterPlants(
        plant_id="PLANT_A",
        operator="Connecticut Water Authority",
        city="New Haven",
        state="CT",
        country="USA",
        active=True,
    )

    plant_b = WastewaterPlants(
        plant_id="PLANT_B",
        operator="New York City DEP",
        city="New York",
        state="NY",
        country="USA",
        active=False,
    )

    # Add and commit
    session.add(plant_a)
    session.add(plant_b)
    session.commit()

    print("✓ Inserted 2 facilities")
    print(f"  - {plant_a.plant_id} in {plant_a.city}, {plant_a.state}")
    print(f"  - {plant_b.plant_id} in {plant_b.city}, {plant_b.state}")
