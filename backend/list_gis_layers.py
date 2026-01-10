
import requests
import json

def list_layers():
    url = "https://gisdata.pima.gov/arcgis1/rest/services/GISOpenData/LandRecords/MapServer?f=json"
    print(f"Querying {url}...")
    try:
        resp = requests.get(url, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            print("\n--- Layers ---")
            for layer in data.get("layers", []):
                print(f"{layer['id']}: {layer['name']}")
            
            print("\n--- Tables ---")
            for table in data.get("tables", []):
                print(f"{table['id']}: {table['name']}")
        else:
            print(f"Error: {resp.status_code}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    list_layers()
