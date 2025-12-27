import os
import sys
from sqlalchemy import create_engine, text
from app.core.config import settings

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def migrate():
    print("Starting migration v4 (SQLite Compatibility)...")
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        conn.execution_options(isolation_level="AUTOCOMMIT")
        
        print("Dropping existing tables...")
        # SQLite doesn't support CASCADE, so we drop in order of dependency
        conn.execute(text("DROP TABLE IF EXISTS lead_events;"))
        conn.execute(text("DROP TABLE IF EXISTS offers;"))
        conn.execute(text("DROP TABLE IF EXISTS leads;"))
        conn.execute(text("DROP TABLE IF EXISTS users;"))
        
        # 1. Create Users Table
        print("Creating users table...")
        conn.execute(text("""
            CREATE TABLE users (
                id VARCHAR PRIMARY KEY,
                email VARCHAR NOT NULL UNIQUE,
                external_id VARCHAR NOT NULL UNIQUE,
                role VARCHAR DEFAULT 'user',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP
            );
        """))
        
        # 2. Create Leads Table
        print("Creating leads table...")
        conn.execute(text("""
            CREATE TABLE leads (
                id VARCHAR PRIMARY KEY,
                user_id VARCHAR REFERENCES users(id),
                address_street VARCHAR NOT NULL,
                address_zip VARCHAR(10),
                owner_name VARCHAR,
                status VARCHAR DEFAULT 'New',
                distress_score INTEGER DEFAULT 0,
                equity_percent FLOAT DEFAULT 0.0,
                
                latitude FLOAT,
                longitude FLOAT,
                
                phone VARCHAR,
                email VARCHAR,
                mailing_address VARCHAR,
                social_ids JSON DEFAULT '{}',
                
                bedrooms INTEGER,
                bathrooms FLOAT,
                sqft INTEGER,
                lot_size FLOAT,
                year_built INTEGER,
                zoning VARCHAR,
                property_type VARCHAR,
                parcel_id VARCHAR,
                
                has_pool BOOLEAN DEFAULT 0,
                has_garage BOOLEAN DEFAULT 0,
                has_guesthouse BOOLEAN DEFAULT 0,
                
                last_sale_date DATE,
                last_sale_price INTEGER,
                offer_amount INTEGER,
                mortgage_amount INTEGER,
                
                tags JSON DEFAULT '[]',
                strategy VARCHAR,
                source VARCHAR,
                
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP
            );
        """))
        
        # 3. Create Offers Table
        print("Creating offers table...")
        conn.execute(text("""
            CREATE TABLE offers (
                id VARCHAR PRIMARY KEY,
                lead_id VARCHAR REFERENCES leads(id) NOT NULL,
                offer_amount NUMERIC(12, 2),
                lex_approval_status BOOLEAN DEFAULT 0,
                contract_pdf_url VARCHAR,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))

        # 4. Create Lead Events Table
        print("Creating lead_events table...")
        conn.execute(text("""
            CREATE TABLE lead_events (
                id VARCHAR PRIMARY KEY,
                lead_id VARCHAR REFERENCES leads(id) NOT NULL,
                type VARCHAR NOT NULL,
                payload JSON DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))
        
    print("Migration v4 complete. Schema aligned with Build Docs (SQLite variant).")

if __name__ == "__main__":
    migrate()
