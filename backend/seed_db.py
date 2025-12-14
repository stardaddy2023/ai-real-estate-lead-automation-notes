from app.core.database import SessionLocal, engine, Base
from app.models.orm import LeadModel
import sys

from app.core.config import settings
from sqlalchemy import inspect, text

# Ensure tables exist
print(f"Connecting to database: {settings.DATABASE_URL}")
Base.metadata.create_all(bind=engine)

def seed():
    inspector = inspect(engine)
    if inspector.has_table("leads"):
        columns = [c["name"] for c in inspector.get_columns("leads")]
        print(f"Existing columns in 'leads' table: {columns}")
        
        with engine.connect() as conn:
            if "latitude" not in columns:
                print("Adding missing column: latitude")
                conn.execute(text("ALTER TABLE leads ADD COLUMN latitude FLOAT"))
            if "longitude" not in columns:
                print("Adding missing column: longitude")
                conn.execute(text("ALTER TABLE leads ADD COLUMN longitude FLOAT"))
            if "strategy" not in columns:
                print("Adding missing column: strategy")
                conn.execute(text("ALTER TABLE leads ADD COLUMN strategy VARCHAR"))
            if "phone" not in columns:
                print("Adding missing column: phone")
                conn.execute(text("ALTER TABLE leads ADD COLUMN phone VARCHAR"))
            if "email" not in columns:
                print("Adding missing column: email")
                conn.execute(text("ALTER TABLE leads ADD COLUMN email VARCHAR"))
            if "mailing_address" not in columns:
                print("Adding missing column: mailing_address")
                conn.execute(text("ALTER TABLE leads ADD COLUMN mailing_address VARCHAR"))
            if "social_ids" not in columns:
                print("Adding missing column: social_ids")
                # SQLite supports JSON as TEXT
                conn.execute(text("ALTER TABLE leads ADD COLUMN social_ids JSON"))
            
            # New Property Data Columns
            new_columns = {
                "bedrooms": "INTEGER",
                "bathrooms": "FLOAT",
                "sqft": "INTEGER",
                "lot_size": "FLOAT",
                "year_built": "INTEGER",
                "has_pool": "VARCHAR",
                "has_garage": "VARCHAR",
                "has_guesthouse": "VARCHAR",
                "last_sale_date": "VARCHAR",
                "last_sale_price": "INTEGER"
            }
            
            for col_name, col_type in new_columns.items():
                if col_name not in columns:
                    print(f"Adding missing column: {col_name}")
                    conn.execute(text(f"ALTER TABLE leads ADD COLUMN {col_name} {col_type}"))
            
            if "offer_amount" not in columns:
                print("Adding missing column: offer_amount")
                conn.execute(text("ALTER TABLE leads ADD COLUMN offer_amount INTEGER"))

            conn.commit()

    db = SessionLocal()
    
    # Force seed
    print("Seeding database with mock leads...")
    
    mock_leads = [
        {
            "address": "1234 E Speedway Blvd, Tucson, AZ 85719",
            "distress_score": 85,
            "status": "New",
            "strategy": "Wholesale",
            "latitude": 32.2362,
            "longitude": -110.9525,
            "bedrooms": 3,
            "bathrooms": 2.0,
            "sqft": 1850,
            "lot_size": 0.25,
            "year_built": 1978,
            "has_pool": "Yes",
            "has_garage": "Yes",
            "has_guesthouse": "No",
            "last_sale_date": "2015-06-12",
            "last_sale_price": 245000
        },
        {
            "address": "5678 N Oracle Rd, Tucson, AZ 85704",
            "distress_score": 92,
            "status": "Analyzing",
            "strategy": "Fix and Flip",
            "latitude": 32.3095,
            "longitude": -110.9778,
            "bedrooms": 4,
            "bathrooms": 3.0,
            "sqft": 2400,
            "lot_size": 0.5,
            "year_built": 1995,
            "has_pool": "Yes",
            "has_garage": "Yes",
            "has_guesthouse": "Yes",
            "last_sale_date": "2018-03-22",
            "last_sale_price": 450000
        },
        {
            "address": "901 S 6th Ave, Tucson, AZ 85701",
            "distress_score": 45,
            "status": "Archived",
            "strategy": "Buy and Hold",
            "latitude": 32.2125,
            "longitude": -110.9695,
            "bedrooms": 2,
            "bathrooms": 1.0,
            "sqft": 950,
            "lot_size": 0.15,
            "year_built": 1945,
            "has_pool": "No",
            "has_garage": "No",
            "has_guesthouse": "No",
            "last_sale_date": "2020-01-10",
            "last_sale_price": 180000
        },
        {
            "address": "2200 W Anklam Rd, Tucson, AZ 85745",
            "distress_score": 78,
            "status": "New",
            "strategy": "Wholesale",
            "latitude": 32.2215,
            "longitude": -111.0150,
            "bedrooms": 3,
            "bathrooms": 2.0,
            "sqft": 1600,
            "lot_size": 0.33,
            "year_built": 1982,
            "has_pool": "No",
            "has_garage": "Yes",
            "has_guesthouse": "No",
            "last_sale_date": "2010-11-05",
            "last_sale_price": 210000
        },
        {
            "address": "3450 E Sunrise Dr, Tucson, AZ 85718",
            "distress_score": 15,
            "status": "Archived",
            "strategy": "None",
            "latitude": 32.3050,
            "longitude": -110.9150,
            "bedrooms": 5,
            "bathrooms": 4.0,
            "sqft": 3500,
            "lot_size": 1.2,
            "year_built": 2005,
            "has_pool": "Yes",
            "has_garage": "Yes",
            "has_guesthouse": "Yes",
            "last_sale_date": "2022-08-15",
            "last_sale_price": 1200000
        }
    ]

    # Update specific mock leads
    for lead_data in mock_leads:
        # Check if lead exists to avoid duplicates if re-running
        existing = db.query(LeadModel).filter(LeadModel.address == lead_data["address"]).first()
        if not existing:
            lead = LeadModel(**lead_data)
            db.add(lead)
        else:
            # Update existing lead with new data
            for key, value in lead_data.items():
                if key not in ["address", "status", "distress_score", "strategy", "latitude", "longitude"]: # Preserve some existing fields if needed, or just overwrite
                     setattr(existing, key, value)
            # Also ensure lat/long are set if missing
            if not existing.latitude:
                existing.latitude = lead_data["latitude"]
            if not existing.longitude:
                existing.longitude = lead_data["longitude"]
    
    db.commit()

    # Now, backfill ANY lead that still has missing property data
    print("Backfilling missing property data for other leads...")
    all_leads = db.query(LeadModel).all()
    import random
    
    for lead in all_leads:
        if not lead.sqft:
            lead.bedrooms = random.randint(2, 5)
            lead.bathrooms = random.randint(1, 4)
            lead.sqft = random.randint(1000, 3500)
            lead.lot_size = round(random.uniform(0.1, 1.0), 2)
            lead.year_built = random.randint(1950, 2020)
            lead.has_pool = random.choice(["Yes", "No"])
            lead.has_garage = random.choice(["Yes", "No"])
            lead.has_guesthouse = random.choice(["Yes", "No"])
            lead.last_sale_date = f"{random.randint(2010, 2023)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}"
            lead.last_sale_price = random.randint(150000, 800000)
            print(f"Updated lead {lead.id} with mock property data.")

    db.commit()
    print(f"Successfully seeded/updated leads.")
    db.close()

if __name__ == "__main__":
    seed()
