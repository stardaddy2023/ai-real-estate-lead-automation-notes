
import requests
import json

def check_layer4():
    print("--- Checking Layer 4 (Neighborhood Associations) ---")
    url = "https://gisdata.pima.gov/arcgis1/rest/services/GISOpenData/LandRecords/MapServer/4/query"
    
    where_clause = "NAME LIKE '%HOLLYWOOD%'"
    
    params = {
        "where": where_clause,
        "outFields": "NAME",
        "returnGeometry": "false",
        "returnDistinctValues": "true",
        "f": "json"
    }
    
    try:
        resp = requests.get(url, params=params)
        data = resp.json()
        features = data.get("features", [])
        print(f"Found {len(features)} matching neighborhoods:")
        for f in features:
            print(f"  - {f['attributes']['NAME']}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_layer4()
