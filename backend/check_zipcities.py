import requests
import json

def check_zipcities():
    url = "https://gisdata.pima.gov/arcgis1/rest/services/GISOpenData/Addresses/MapServer/3/query"
    params = {
        "where": "1=1",
        "outFields": "ZIPCITY",
        "returnGeometry": "false",
        "returnDistinctValues": "true",
        "f": "json"
    }
    
    try:
        print("Querying distinct ZIPCITY values from Layer 3...")
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            features = data.get("features", [])
            values = [f["attributes"]["ZIPCITY"] for f in features if f.get("attributes") and f["attributes"].get("ZIPCITY")]
            print(f"Found {len(values)} distinct zip cities:")
            for v in sorted(values):
                print(f"  - '{v}'")
        else:
            print(f"Error: {response.status_code}")
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    check_zipcities()
