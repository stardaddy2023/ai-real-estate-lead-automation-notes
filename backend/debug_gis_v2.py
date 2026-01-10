import requests
import json

def check_parcel_attributes():
    print("--- Checking Parcel Attributes ---")
    url = "https://gisdata.pima.gov/arcgis1/rest/services/GISOpenData/LandRecords/MapServer/12/query"
    params = {
        "where": "OBJECTID < 10", 
        "outFields": "*",
        "f": "json"
    }
    try:
        resp = requests.get(url, params=params)
        data = resp.json()
        if "features" in data and len(data["features"]) > 0:
            attr = data["features"][0]["attributes"]
            print("All Keys:", list(attr.keys()))
            # Check specific fields
            print(f"PARCEL: {attr.get('PARCEL')}")
            print(f"GISAREA: {attr.get('GISAREA')}") # Check if this exists
            print(f"LANDMEAS: {attr.get('LANDMEAS')}")
            print(f"LANDUNIT: {attr.get('LANDUNIT')}")
            print(f"SUBDIV_NAME: {attr.get('SUBDIV_NAME')}")
        else:
            print("No features found.")
    except Exception as e:
        print(f"Error: {e}")

def check_neighborhood_search(term):
    print(f"\n--- Checking Neighborhood Search: '{term}' ---")
    url = "https://gisdata.pima.gov/arcgis1/rest/services/GISOpenData/LandRecords/MapServer/12/query"
    where_clause = f"SUBDIV_NAME LIKE '%{term.upper()}%'"
    
    # Minimal params for extent only
    params = {
        "where": where_clause,
        "returnExtentOnly": "true",
        "f": "json"
    }
    try:
        resp = requests.get(url, params=params)
        print(f"Response Status: {resp.status_code}")
        print(f"Response Body: {resp.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_parcel_attributes()
    check_neighborhood_search("Sam Hughes")
