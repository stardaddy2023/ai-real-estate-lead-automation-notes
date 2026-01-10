import requests
import json

def check_neighborhood_resolution(term):
    print(f"\n--- Checking Neighborhood Resolution (Layer 15): '{term}' ---")
    url = "https://gisdata.pima.gov/arcgis1/rest/services/GISOpenData/LandRecords/MapServer/15/query"
    where_clause = f"SUB_NAME LIKE '%{term.upper()}%'"
    
    params = {
        "where": where_clause,
        "outFields": "SUB_NAME",
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
    check_neighborhood_resolution("Sam Hughes")
