import requests
import json

def check_85711():
    try:
        # Check Layer 12
        print("--- Checking Layer 12 (Parcels) ---")
        url_12 = "https://gisdata.pima.gov/arcgis1/rest/services/GISOpenData/LandRecords/MapServer/12/query"
        params_12 = {
            "where": "ADDRESS_OL LIKE '4414 E 2ND%'",
            "outFields": "*",
            "f": "json"
        }
        resp = requests.post(url_12, data=params_12).json()
        print(f"Layer 12 Found: {len(resp.get('features', []))}")
        if resp.get('features'):
            print(f"Sample L12: {resp['features'][0]['attributes']}")

        # Check Layer 4
        print("\n--- Checking Layer 4 (Tax Parcels) ---")
        url_4 = "https://gisdata.pima.gov/arcgis1/rest/services/GISOpenData/LandRecords/MapServer/4/query"
        params_4 = {
            "where": "OBJECTID < 10", # Get any records
            "outFields": "*",
            "f": "json"
        }
        resp = requests.post(url_4, data=params_4).json()
        print(f"Layer 4 Found: {len(resp.get('features', []))}")
        if resp.get('features'):
            print(f"Sample L4: {resp['features'][0]['attributes']}")

    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    check_85711()
