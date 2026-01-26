import requests
import json

url = "https://gisdata.pima.gov/arcgis1/rest/services/GISOpenData/LandRecords/MapServer?f=json"

try:
    print(f"Querying MapServer info: {url}")
    r = requests.get(url, timeout=15)
    
    if r.status_code == 200:
        data = r.json()
        if data.get("layers"):
            print(f"Found {len(data['layers'])} layers:")
            for layer in data["layers"]:
                print(f"  ID: {layer['id']}, Name: {layer['name']}")
        else:
            print("No layers found in response.")
    else:
        print(f"Error: Status {r.status_code}")
except Exception as e:
    print(f"Error: {e}")
