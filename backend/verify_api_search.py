import requests
import json

def verify_api():
    url = "http://127.0.0.1:8000/scout/search"
    
    # Test 1: Inclusion - 1788 W MISSION PL (Should be in 85746)
    print("\n--- Test 1: Inclusion (1788 W MISSION PL) ---")
    payload_inc = {
        "state": "AZ",
        "county": "Pima",
        "zip_code": "85746",
        "address": "1788 W MISSION PL",
        "distress_type": "all",
        "property_types": [],
        "limit": 10
    }
    print(f"Sending payload: {payload_inc}")
    try:
        response_inc = requests.post(url, json=payload_inc)
        if response_inc.status_code == 200:
            results = response_inc.json()
            print(f"Found {len(results)} leads.")
            if len(results) > 0:
                print(f"SUCCESS: Found 1788 W MISSION PL. Address: {results[0].get('address')}")
            else:
                print("FAILURE: 1788 W MISSION PL not found in results.")
        else:
            print(f"Error: {response_inc.status_code} - {response_inc.text}")
    except Exception as e:
        print(f"Error Test 1: {e}")

    # Test 2: Exclusion - 1618 W CIRCLE A DR (Should be excluded from 85746)
    print("\n--- Test 2: Exclusion (1618 W CIRCLE A DR) ---")
    payload_exc = {
        "state": "AZ",
        "county": "Pima",
        "zip_code": "85746",
        "address": "1618 W CIRCLE A DR",
        "distress_type": "all",
        "property_types": [],
        "limit": 10
    }
    print(f"Sending payload: {payload_exc}")
    try:
        response_exc = requests.post(url, json=payload_exc)
        if response_exc.status_code == 200:
            results = response_exc.json()
            print(f"Found {len(results)} leads.")
            if len(results) == 0:
                print("SUCCESS: 1618 W CIRCLE A DR was correctly excluded.")
            else:
                print(f"FAILURE: Found excluded address 1618 W CIRCLE A DR. Address: {results[0].get('address')}")
        else:
            print(f"Error: {response_exc.status_code} - {response_exc.text}")
    except Exception as e:
        print(f"Error Test 2: {e}")

    # Test 3: Performance (Fetch 100 leads)
    print("\n--- Test 3: Performance (Fetch 100 leads) ---")
    import time
    t_start = time.time()
    payload_perf = {
        "state": "AZ",
        "county": "Pima",
        "zip_code": "85746",
        "address": "",
        "distress_type": "all",
        "property_types": [],
        "limit": 100
    }
    print(f"Sending payload: {payload_perf}")
    try:
        response_perf = requests.post(url, json=payload_perf)
        if response_perf.status_code == 200:
            leads = response_perf.json()
            duration = time.time() - t_start
            print(f"Found {len(leads)} leads in {duration:.2f} seconds.")
            if len(leads) >= 100 and duration < 8.0:
                print("SUCCESS: Performance looks good (Parallel Fetching working).")
            else:
                print(f"WARNING: Performance might be slow or insufficient leads. Time: {duration:.2f}s, Count: {len(leads)}")
        else:
            print(f"Error: {response_perf.status_code} - {response_perf.text}")
    except Exception as e:
        print(f"Error Test 3: {e}")

if __name__ == "__main__":
    verify_api()
