import requests
import json

def check_subdivision_layer():
    print("--- Checking Layer 15 (Subdivisions) Attributes ---")
    url = "https://gisdata.pima.gov/arcgis1/rest/services/GISOpenData/LandRecords/MapServer/15/query"
    params = {
        "where": "OBJECTID < 5",
        "outFields": "*",
        "f": "json"
    }
    try:
        resp = requests.get(url, params=params)
        data = resp.json()
        if "features" in data and len(data["features"]) > 0:
            attr = data["features"][0]["attributes"]
            print("Keys:", list(attr.keys()))
            if "NAME" in attr:
                print(f"Found NAME: {attr['NAME']}")
            if "SUBDIV_NAME" in attr:
                print(f"Found SUBDIV_NAME: {attr['SUBDIV_NAME']}")
        else:
            print("No features found.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_subdivision_layer()
