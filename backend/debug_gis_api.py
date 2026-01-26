import requests
import json

# Base URL for the API
base_url = "https://gisopendata.pima.gov/api/search/v1"

def list_mapserver_layers():
    url = "https://gisdata.pima.gov/arcgis1/rest/services/GISOpenData/LandRecords/MapServer?f=json"
    print(f"\nFetching layers from: {url}")
    try:
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            data = r.json()
            layers = data.get("layers", [])
            print(f"Found {len(layers)} layers:")
            
            for l in layers:
                print(f"  Layer {l['id']}: {l['name']}")
                
        else:
            print(f"Error: {r.status_code}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_mapserver_layers()
