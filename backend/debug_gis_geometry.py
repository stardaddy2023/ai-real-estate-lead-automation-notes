import requests
import json

url = "https://gisdata.pima.gov/arcgis1/rest/services/GISOpenData/LandRecords/MapServer/12/query"

params = {
    "where": "ZIP = '85705' AND OBJECTID < 5",
    "outFields": "PARCEL",
    "returnGeometry": "true",
    "outSR": "4326", # Request WGS84
    "f": "json"
}

try:
    print(f"Querying: {url}")
    response = requests.get(url, params=params)
    data = response.json()
    
    if "features" in data:
        for f in data["features"]:
            print(f"Parcel: {f['attributes']['PARCEL']}")
            print(f"Geometry: {f.get('geometry')}")
    else:
        print("No features found or error:", data)

except Exception as e:
    print(f"Error: {e}")
