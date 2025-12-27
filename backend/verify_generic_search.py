import requests
import json

BASE_URL = "http://localhost:8000/scout/search"

def test_search(payload, description):
    print(f"\n--- Testing {description} ---")
    print(f"Payload: {payload}")
    try:
        resp = requests.post(BASE_URL, json=payload)
        if resp.status_code == 200:
            data = resp.json()
            print(f"Status: 200 OK")
            print(f"Results: {len(data)}")
            if len(data) > 0:
                print(f"First Result Distress: {data[0].get('distress_signals')}")
        else:
            print(f"Error: {resp.status_code} - {resp.text}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    # Test: Empty distress_type (Should be Generic)
    payload_generic = {
        "zip_code": "85711",
        "property_types": ["Single Family"],
        "distress_type": [], # Empty list
        "limit": 10
    }
    test_search(payload_generic, "Generic Search (Empty Distress)")
