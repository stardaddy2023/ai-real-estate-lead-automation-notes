import os
import sys
import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.user import UserModel
from app.models.orm import LeadModel

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def verify():
    print("Verifying schema v4...")
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # 1. Create User
        user_id = str(uuid.uuid4())
        user = UserModel(
            id=user_id,
            email=f"test_{user_id[:8]}@example.com",
            external_id=f"oauth_{user_id[:8]}"
        )
        db.add(user)
        db.commit()
        print(f"Created User: {user.id}")
        
        # 2. Create Lead
        lead = LeadModel(
            user_id=user.id,
            address_street="123 Test St",
            address_zip="12345",
            status="New"
        )
        db.add(lead)
        db.commit()
        print(f"Created Lead: {lead.id} linked to User {lead.user_id}")
        
        # 3. Query
        fetched_lead = db.query(LeadModel).filter(LeadModel.id == lead.id).first()
        if fetched_lead and fetched_lead.address_street == "123 Test St":
            print("Verification SUCCESS: Lead retrieved correctly.")
        else:
            print("Verification FAILED: Lead not found or data mismatch.")
            
    except Exception as e:
        print(f"Verification ERROR: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    verify()
