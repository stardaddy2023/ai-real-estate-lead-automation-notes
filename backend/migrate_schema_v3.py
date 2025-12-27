import os
import sys
from sqlalchemy import create_engine, text
from app.core.config import settings

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def migrate():
    print("Starting migration v3 (UUID Enforcement)...")
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        conn.execution_options(isolation_level="AUTOCOMMIT")
        
        # WARNING: We are dropping tables to enforce UUID change cleanly for this phase.
        # In a production system with data, we would create a new table and copy data.
        print("Dropping existing tables to enforce UUID schema...")
        conn.execute(text("DROP TABLE IF EXISTS lead_events CASCADE;"))
        conn.execute(text("DROP TABLE IF EXISTS offers CASCADE;"))
        conn.execute(text("DROP TABLE IF EXISTS leads CASCADE;"))
        conn.execute(text("DROP TABLE IF EXISTS users CASCADE;"))
        
        # 1. Create Users Table
        print("Creating users table...")
        conn.execute(text("""
            CREATE TABLE users (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                email VARCHAR NOT NULL UNIQUE,
                external_id VARCHAR NOT NULL UNIQUE,
                role VARCHAR DEFAULT 'user',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE
            );
        """))
        
        # 2. Create Leads Table (UUID)
        print("Creating leads table...")
        conn.execute(text("""
            CREATE TABLE leads (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID REFERENCES users(id),
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
                social_ids JSONB DEFAULT '{}',
                
                bedrooms INTEGER,
                bathrooms FLOAT,
                sqft INTEGER,
                lot_size FLOAT,
                year_built INTEGER,
                zoning VARCHAR,
                property_type VARCHAR,
                parcel_id VARCHAR,
                
                has_pool BOOLEAN DEFAULT FALSE,
                has_garage BOOLEAN DEFAULT FALSE,
                has_guesthouse BOOLEAN DEFAULT FALSE,
                
                last_sale_date DATE,
                last_sale_price INTEGER,
                offer_amount INTEGER,
                mortgage_amount INTEGER,
                
                tags JSONB DEFAULT '[]',
                strategy VARCHAR,
                source VARCHAR,
                
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE
            );
        """))
        
        # 3. Create Offers Table
        print("Creating offers table...")
        conn.execute(text("""
            CREATE TABLE offers (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                lead_id UUID REFERENCES leads(id) NOT NULL,
                offer_amount NUMERIC(12, 2),
                lex_approval_status BOOLEAN DEFAULT FALSE,
                contract_pdf_url VARCHAR,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """))

        # 4. Create Lead Events Table
        print("Creating lead_events table...")
        conn.execute(text("""
            CREATE TABLE lead_events (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                lead_id UUID REFERENCES leads(id) NOT NULL,
                type VARCHAR NOT NULL,
                payload JSONB DEFAULT '{}',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """))
        
    print("Migration v3 complete. Schema aligned with Build Docs.")

if __name__ == "__main__":
    migrate()
