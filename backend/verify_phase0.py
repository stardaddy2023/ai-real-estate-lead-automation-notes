import os
import sys
from fastapi.testclient import TestClient
from dotenv import load_dotenv

# Add the backend directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load .env from backend directory
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
load_dotenv(env_path)

from app.main import app

client = TestClient(app)

def verify_market_scout():
    print("--- Verifying Market Scout Service (Phase 0) ---")
    
    # 1. Test Endpoint
    response = client.get("/api/v1/scout/heatmap")
    
    if response.status_code == 200:
        points = response.json()
        print(f"✅ Endpoint returned 200 OK")
        print(f"✅ Found {len(points)} heatmap points")
        
        # Verify content structure
        if len(points) > 0:
            point = points[0]
            if "lat" in point and "lng" in point and "weight" in point:
                print(f"✅ Data structure valid: lat={point['lat']}, lng={point['lng']}, weight={point['weight']}")
            else:
                print(f"❌ Invalid data structure: {point}")
                
            # Check for Pima County zip codes
            zips = set(p["zip_code"] for p in points)
            print(f"📍 Zip Codes Found: {', '.join(sorted(list(zips))[:5])}...")
            
            if "85701" in zips:
                print("✅ Found expected zip code 85701")
            else:
                print("⚠️ Missing expected zip code 85701")
        else:
            print("⚠️ No points found (Check logic)")
    else:
        print(f"❌ Endpoint failed: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    verify_market_scout()
