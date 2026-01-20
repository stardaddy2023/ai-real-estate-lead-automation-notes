import requests

# Get all layers in LandRecords MapServer
url = "https://gisdata.pima.gov/arcgis1/rest/services/GISOpenData/LandRecords/MapServer"
params = {"f": "json"}

print("Fetching all layers in LandRecords MapServer...")
r = requests.get(url, params=params, timeout=30)
print(f"Status: {r.status_code}")

if r.status_code == 200:
    d = r.json()
    print(f"\nService: {d.get('documentInfo', {}).get('Title', 'Unknown')}")
    print(f"\nLayers ({len(d.get('layers', []))} total):")
    for layer in d.get("layers", []):
        print(f"  {layer['id']:3} - {layer['name']}")
