
import requests
import json

def check_api():
    parcel_id = "117023950"
    
    # Potential API patterns for Pima Assessor
    endpoints = [
        f"https://asr.pima.gov/api/parcel/{parcel_id}",
        f"https://asr.pima.gov/api/v1/parcel/{parcel_id}",
        f"https://asr.pima.gov/api/parcels/{parcel_id}",
        f"https://asr.pima.gov/Parcel/Details/{parcel_id}", # Sometimes it's just a different path
        f"https://asr.pima.gov/api/search/{parcel_id}"
    ]
    
    print("--- Probing Assessor API Endpoints ---")
    for url in endpoints:
        try:
            print(f"Testing: {url}")
            response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
            if response.status_code == 200:
                content_type = response.headers.get("Content-Type", "")
                if "json" in content_type:
                    print(f"SUCCESS! Found JSON at {url}")
                    print(response.json())
                    return
                else:
                    print(f"Status 200 but not JSON ({content_type})")
            else:
                print(f"Status: {response.status_code}")
        except Exception as e:
            print(f"Error: {e}")

    print("\n--- Checking GIS Layer 2 (Parcel Lines with Tax Codes) ---")
    url_l2 = "https://gisdata.pima.gov/arcgis1/rest/services/GISOpenData/LandRecords/MapServer/2/query"
    params = {
        "where": f"PARCEL='{parcel_id}'", # Try PARCEL field
        "outFields": "*",
        "f": "json"
    }
    try:
        response = requests.get(url_l2, params=params)
        data = response.json()
        if "features" in data and len(data["features"]) > 0:
            print("Layer 2 Match Found!")
            for k, v in data["features"][0]["attributes"].items():
                print(f"{k}: {v}")
        else:
            print("No match in Layer 2 with PARCEL field. Trying TAX_CODE...")
            params["where"] = f"TAX_CODE='{parcel_id}'"
            response = requests.get(url_l2, params=params)
            data = response.json()
            if "features" in data and len(data["features"]) > 0:
                print("Layer 2 Match Found (TAX_CODE)!")
                for k, v in data["features"][0]["attributes"].items():
                    print(f"{k}: {v}")
            else:
                print("No match in Layer 2.")
    except Exception as e:
        print(f"Error L2: {e}")

if __name__ == "__main__":
    check_api()
