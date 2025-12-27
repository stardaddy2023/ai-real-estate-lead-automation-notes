from fastapi.testclient import TestClient
from app.main import app
import uuid

client = TestClient(app)

def verify_api():
    print("Verifying API Endpoints...")
    
    # 1. Sync User
    print("Testing POST /api/v1/users/sync...")
    user_data = {
        "email": f"api_test_{uuid.uuid4().hex[:8]}@example.com",
        "external_id": f"oauth_{uuid.uuid4().hex[:8]}"
    }
    response = client.post("/api/v1/users/sync", json=user_data)
    assert response.status_code == 200
    user = response.json()
    print(f"User Created: {user['id']}")
    
    # 2. Create Lead
    print("Testing POST /api/v1/leads...")
    lead_data = {
        "address_street": "456 API Blvd",
        "address_zip": "90210",
        "status": "New",
        "user_id": user['id']
    }
    response = client.post("/api/v1/leads", json=lead_data)
    assert response.status_code == 200
    lead = response.json()
    print(f"Lead Created: {lead['id']}")
    
    # 3. Create Offer
    print("Testing POST /api/v1/offers...")
    offer_data = {
        "lead_id": lead['id'],
        "offer_amount": 250000.00
    }
    response = client.post("/api/v1/offers", json=offer_data)
    assert response.status_code == 200
    offer = response.json()
    print(f"Offer Created: {offer['id']} for amount {offer['offer_amount']}")
    
    print("API Verification SUCCESS.")

if __name__ == "__main__":
    verify_api()
