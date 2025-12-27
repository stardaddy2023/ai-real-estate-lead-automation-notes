import asyncio
import sys
import os
from unittest.mock import MagicMock, AsyncMock

# Add the backend directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from dotenv import load_dotenv

# Load .env from backend directory
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
load_dotenv(env_path)

from app.main import app
from app.core.database import get_db
from app.models.orm import LeadModel
from app.models.offer import OfferModel

# Mock Data
MOCK_LEAD = LeadModel(
    id="test-lead-1",
    address_street="1234 Desert Palm Dr, Tucson, AZ 85746",
    distress_score=85,
    status="Contracted"
)

MOCK_OFFER = OfferModel(
    id="offer-1",
    lead_id="test-lead-1",
    offer_amount=250000.00
)

# Mock DB Session
class MockResult:
    def __init__(self, data):
        self._data = data
    
    def scalars(self):
        return self
        
    def first(self):
        return self._data

    def all(self):
        return [self._data] if self._data else []

async def mock_get_db():
    mock_session = AsyncMock()
    
    async def execute(stmt):
        # Simple logic to return Lead or Offer based on the statement
        # This is a bit hacky but works for this specific endpoint verification
        str_stmt = str(stmt)
        if "leads" in str_stmt:
            return MockResult(MOCK_LEAD)
        elif "offers" in str_stmt:
            return MockResult(MOCK_OFFER)
        return MockResult(None)
        
    mock_session.execute = execute
    yield mock_session

# Override Dependency
app.dependency_overrides[get_db] = mock_get_db

client = TestClient(app)

def verify_matchmaker():
    print("--- Verifying Matchmaker Service (Phase 4) ---")
    
    # 1. Test Endpoint
    response = client.get("/api/v1/dispositions/matches?lead_id=test-lead-1")
    
    if response.status_code == 200:
        matches = response.json()
        print(f"✅ Endpoint returned 200 OK")
        print(f"✅ Found {len(matches)} matches")
        
        # Verify content
        if len(matches) > 0:
            top_match = matches[0]
            print(f"🏆 Top Match: {top_match['buyer_name']} (Score: {top_match['match_score']})")
            print(f"📝 Reason: {top_match['match_reason']}")
            
            # Check for expected mock data
            expected_buyers = ["Opendoor", "Offerpad", "Tucson Flippers LLC"]
            if top_match['buyer_name'] in expected_buyers:
                print("✅ Data matches expected mock buyers")
            else:
                print(f"⚠️ Unexpected buyer name: {top_match['buyer_name']}")
        else:
            print("⚠️ No matches found (Check logic)")
    else:
        print(f"❌ Endpoint failed: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    verify_matchmaker()
