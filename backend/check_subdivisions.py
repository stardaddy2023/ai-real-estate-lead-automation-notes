
import requests
import json

def check_subdivisions():
    print("--- Checking Subdivisions for 'Barrio' ---")
    url = "https://gisdata.pima.gov/arcgis1/rest/services/GISOpenData/LandRecords/MapServer/15/query"
    
    # Search for anything containing "HOLLYWOOD"
    where_clause = "SUB_NAME LIKE '%HOLLYWOOD%'"
    
    params = {
        "where": where_clause,
        "outFields": "SUB_NAME",
        "returnGeometry": "false",
        "returnDistinctValues": "true",
        "f": "json",
        "orderByFields": "SUB_NAME ASC"
    }
    
    try:
        resp = requests.get(url, params=params)
        data = resp.json()
        features = data.get("features", [])
        print(f"Found {len(features)} matching subdivisions:")
        for f in features:
            print(f"  - {f['attributes']['SUB_NAME']}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_subdivisions()
