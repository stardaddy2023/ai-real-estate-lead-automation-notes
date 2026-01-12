import requests
import json

def check_metadata():
    url = "https://gisdata.pima.gov/arcgis1/rest/services/GISOpenData/LandRecords/MapServer/12"
    params = {"f": "json"}
    
    print("Fetching Layer 12 metadata...")
    resp = requests.get(url, params=params)
    data = resp.json()
    
    if "extent" in data:
        print("Extent Spatial Reference:")
        print(json.dumps(data["extent"]["spatialReference"], indent=2))
    
    if "sourceSpatialReference" in data:
        print("Source Spatial Reference:")
        print(json.dumps(data["sourceSpatialReference"], indent=2))

if __name__ == "__main__":
    check_metadata()
