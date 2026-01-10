import requests
import json

def list_layers():
    print("--- Listing Layers ---")
    url = "https://gisdata.pima.gov/arcgis1/rest/services/GISOpenData/LandRecords/MapServer"
    params = {"f": "json"}
    try:
        resp = requests.get(url, params=params)
        data = resp.json()
        if "layers" in data:
            for layer in data["layers"]:
                print(f"Layer {layer['id']}: {layer['name']}")
        else:
            print("No layers found.")
    except Exception as e:
        print(f"Error: {e}")

def check_subdivision_layer(layer_id):
    print(f"\n--- Checking Layer {layer_id} Attributes ---")
    url = f"https://gisdata.pima.gov/arcgis1/rest/services/GISOpenData/LandRecords/MapServer/{layer_id}/query"
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
            if "SUBDIV_NAME" in attr:
                print("SUBDIV_NAME found!")
        else:
            print("No features found.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_layers()
