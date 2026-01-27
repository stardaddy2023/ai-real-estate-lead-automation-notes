import requests
import json

url = "https://gisdata.pima.gov/arcgis1/rest/services/GISOpenData/LandRecords/MapServer?f=json"

print(f"Querying {url}...")
try:
    resp = requests.get(url)
    data = resp.json()
    
    if "layers" in data:
        print("\n=== LAYERS ===")
        for layer in data["layers"]:
            print(f"{layer['id']}: {layer['name']}")
    else:
        print("No 'layers' key in response.")
        print(json.dumps(data, indent=2))

except Exception as e:
    print(f"Error: {e}")
