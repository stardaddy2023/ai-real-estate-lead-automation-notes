import requests
import json

def inspect_layer():
    url = "https://gis.tucsonaz.gov/arcgis/rest/services/PDSD/pdsdMain_General5/MapServer/94/query"
    params = {
        "where": "1=1",
        "outFields": "*",
        "returnGeometry": "false",
        "resultRecordCount": 1,
        "f": "json"
    }
    
    try:
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if "features" in data and len(data["features"]) > 0:
                attr = data["features"][0]["attributes"]
                print("Fields available in Layer 94:")
                for k, v in attr.items():
                    print(f" - {k}: {v} (Type: {type(v)})")
            else:
                print("No features found.")
        else:
            print(f"Error: {resp.status_code}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    inspect_layer()
