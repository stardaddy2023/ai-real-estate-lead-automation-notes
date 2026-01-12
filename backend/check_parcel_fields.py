import requests
import json

def check_fields():
    url = "https://gisdata.pima.gov/arcgis1/rest/services/GISOpenData/LandRecords/MapServer/12/query"
    params = {
        "where": "1=1",
        "outFields": "*",
        "returnGeometry": "false",
        "f": "json",
        "resultRecordCount": 1
    }
    
    print("Fetching one parcel to check fields...")
    resp = requests.get(url, params=params)
    data = resp.json()
    features = data.get("features", [])
    
    if features:
        attr = features[0]["attributes"]
        print("Fields found:")
        for key, value in attr.items():
            print(f"{key}: {value}")
    else:
        print("No features found.")

if __name__ == "__main__":
    check_fields()
