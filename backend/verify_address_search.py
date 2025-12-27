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
                print(f"First Result Address: {data[0].get('address')}")
        else:
            print(f"Error: {resp.status_code} - {resp.text}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    # Test 1: Address sent as zip_code (Current Frontend Behavior) - Should Fail
    payload_fail = {
        "zip_code": "2932 S ENCHANTED HILLS DR",
        "property_types": ["Single Family"],
        "distress_type": ["Absentee Owner"],
        "limit": 10
    }
    test_search(payload_fail, "Address as ZIP (Expected Failure)")

    # Test 2: Address sent as address (Proposed Fix) - Should Success
    payload_success = {
        "address": "2932 S ENCHANTED HILLS DR",
        "property_types": ["Single Family"],
        "distress_type": ["Absentee Owner"],
        "limit": 10
    }
    test_search(payload_success, "Address as Address (Expected Success)")
