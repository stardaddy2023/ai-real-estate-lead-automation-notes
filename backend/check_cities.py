import requests
import json

def check_cities():
    url = "https://gisdata.pima.gov/arcgis1/rest/services/GISOpenData/LandRecords/MapServer/12/query"
    params = {
        "where": "1=1",
        "outFields": "CITY_OL",
        "returnGeometry": "false",
        "returnDistinctValues": "true",
        "f": "json"
    }
    
    try:
        print("Querying distinct CITY_OL values...")
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            features = data.get("features", [])
            values = [f["attributes"]["CITY_OL"] for f in features if f.get("attributes") and f["attributes"].get("CITY_OL")]
            print(f"Found {len(values)} distinct cities:")
            for v in sorted(values):
                print(f"  - '{v}'")
        else:
            print(f"Error: {response.status_code}")
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    check_cities()
