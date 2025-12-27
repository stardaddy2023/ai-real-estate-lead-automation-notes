import os
import sys
from sqlalchemy import create_engine, text
from app.core.config import settings

# Add backend directory to path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def migrate():
    print("Starting migration...")
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        conn.execution_options(isolation_level="AUTOCOMMIT")
        
        # 1. Create Users Table
        print("Creating users table...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                email VARCHAR NOT NULL UNIQUE,
                external_id VARCHAR NOT NULL UNIQUE,
                role VARCHAR DEFAULT 'user',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE
            );
        """))
        
        # 2. Update Leads Table
        print("Updating leads table...")
        
        # Add user_id column
        try:
            conn.execute(text("ALTER TABLE leads ADD COLUMN user_id UUID REFERENCES users(id);"))
        except Exception as e:
            print(f"Column user_id might already exist: {e}")

        # Add timestamps
        try:
            conn.execute(text("ALTER TABLE leads ADD COLUMN created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();"))
            conn.execute(text("ALTER TABLE leads ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE;"))
        except Exception:
            pass

        # Refine types (This is tricky with data, so we'll do safe casts where possible or just add new columns)
        # For simplicity in this script, we'll assume we can alter types or add if missing.
        # Real production migration would need careful data migration.
        
        # Convert has_pool, has_garage, has_guesthouse to BOOLEAN
        # We'll drop and recreate for this dev environment if data isn't critical, OR try to cast.
        # Let's try to cast 'Yes'/'No' to boolean.
        
        flags = ['has_pool', 'has_garage', 'has_guesthouse']
        for flag in flags:
            try:
                # First, ensure they are nullable
                conn.execute(text(f"ALTER TABLE leads ALTER COLUMN {flag} DROP NOT NULL;"))
                # Then cast. Postgres allows casting string to boolean for 'true'/'false', 'yes'/'no', '1'/'0'
                conn.execute(text(f"ALTER TABLE leads ALTER COLUMN {flag} TYPE BOOLEAN USING ({flag}::boolean);"))
            except Exception as e:
                print(f"Could not convert {flag}: {e}")

        # 3. Create Lead Events Table
        print("Creating lead_events table...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS lead_events (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                lead_id INTEGER REFERENCES leads(id) NOT NULL,
                type VARCHAR NOT NULL,
                payload JSONB DEFAULT '{}',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """))
        
    print("Migration complete.")

if __name__ == "__main__":
    migrate()
