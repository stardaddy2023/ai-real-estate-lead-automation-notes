import requests
import json

url = "https://gisdata.pima.gov/arcgis1/rest/services/GISOpenData/Addresses/MapServer/3/query"
params = {
    "where": "ADDRESS LIKE '%2749%FAIR%'", # Guessing field name 'ADDRESS' or 'FULL_ADDRESS'
    "outFields": "*",
    "f": "json",
    "returnGeometry": "false",
    "resultRecordCount": 5
}

print(f"Querying {url} with params: {params}")
try:
    resp = requests.get(url, params=params, timeout=30)
    if resp.status_code == 200:
        data = resp.json()
        if "error" in data:
             print(f"API Error: {data['error']}")
             # Try getting fields first to know the column name
             print("Fetching fields...")
             params = {"f": "json"}
             resp = requests.get(url.replace("/query", ""), params=params)
             layer_info = resp.json()
             if "fields" in layer_info:
                 print("Fields:", [f["name"] for f in layer_info["fields"]])
        else:
            features = data.get("features", [])
            print(f"Found {len(features)} features:")
            if features:
                print(json.dumps(features[0]["attributes"], indent=2))
            else:
                # Try getting fields if no results, maybe wrong field name
                print("No results. Fetching fields to check column names...")
                params = {"f": "json"}
                resp = requests.get(url.replace("/query", ""), params=params)
                layer_info = resp.json()
                if "fields" in layer_info:
                    print("Fields:", [f["name"] for f in layer_info["fields"]])

    else:
        print(f"Error: {resp.status_code} - {resp.text}")
except Exception as e:
    print(f"Exception: {e}")
