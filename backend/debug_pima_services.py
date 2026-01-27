import requests
import json

url = "https://gisdata.pima.gov/arcgis1/rest/services/GISOpenData?f=json"

print(f"Querying {url}...")
try:
    resp = requests.get(url)
    data = resp.json()
    
    if "services" in data:
        print("\n=== SERVICES ===")
        for service in data["services"]:
            print(f"{service['name']} (Type: {service['type']})")
    
    if "folders" in data:
        print("\n=== FOLDERS ===")
        for folder in data["folders"]:
            print(folder)
            
except Exception as e:
    print(f"Error: {e}")
