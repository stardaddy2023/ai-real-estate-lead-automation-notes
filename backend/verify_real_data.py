import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_heatmap():
    print("\n--- Testing Heatmap Endpoint (GET /api/v1/scout/heatmap) ---")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/scout/heatmap?county_fips=04019")
        if response.status_code == 200:
            data = response.json()
            print(f"SUCCESS: Received {len(data)} heatmap points.")
            if len(data) > 0:
                print(f"Sample Point: {data[0]}")
        else:
            print(f"FAILED: Status {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"ERROR: {e}")

def test_market_analysis():
    print("\n--- Testing Market Analysis Endpoint (POST /scout/market) ---")
    payload = {
        "state_fips": "04",
        "county_fips": "019",
        "market_name": "Pima County Test"
    }
    try:
        response = requests.post(f"{BASE_URL}/scout/market", json=payload)
        if response.status_code == 200:
            data = response.json()
            print(f"SUCCESS: Analysis for {data['market_name']}")
            print(f"Score: {data['score']}")
            print(f"Verdict: {data['verdict']}")
            print("Metrics:", json.dumps(data['metrics'], indent=2))
        else:
            print(f"FAILED: Status {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    test_heatmap()
    test_market_analysis()
