
import requests
import json

def inspect_layer2():
    # Pima County GIS Layer 2 (Parcel Lines with Tax Codes)
    url = "https://gisdata.pima.gov/arcgis1/rest/services/GISOpenData/LandRecords/MapServer/2/query"
    
    params = {
        "where": "PARCEL='117023950'",
        "outFields": "*",
        "f": "json",
        "returnGeometry": "false"
    }
    
    print(f"Querying {url}...")
    try:
        resp = requests.get(url, params=params, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            features = data.get("features", [])
            if features:
                attr = features[0].get("attributes", {})
                print("\n--- Raw Attributes for Parcel 117023950 (Layer 2) ---")
                for k, v in sorted(attr.items()):
                    print(f"{k}: {v}")
                
                # Check specifically for 2177
                print("\n--- Searching for '2177' ---")
                found = False
                for k, v in attr.items():
                    if str(v) == "2177" or str(v) == "2177.0":
                        print(f"FOUND 2177 in field: {k}")
                        found = True
                if not found:
                    print("Value 2177 NOT FOUND in Layer 2 attributes.")
            else:
                print("No features found for this parcel in Layer 2.")
        else:
            print(f"Error: {resp.status_code}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    inspect_layer2()
