import requests
import json

def inspect_feature():
    url = "https://gisdata.pima.gov/arcgis1/rest/services/GISOpenData/LandRecords/MapServer/12/query"
    params = {
        "where": "OBJECTID=1000", # Pick an arbitrary ID
        "outFields": "*",
        "returnGeometry": "false",
        "f": "json"
    }
    
    try:
        print("Querying single feature attributes...")
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            features = data.get("features", [])
            if features:
                attrs = features[0]["attributes"]
                print("Attributes found:")
                for k, v in attrs.items():
                    print(f"  {k}: {v}")
            else:
                print("No feature found with OBJECTID=1000")
        else:
            print(f"Error: {response.status_code}")
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    inspect_feature()
