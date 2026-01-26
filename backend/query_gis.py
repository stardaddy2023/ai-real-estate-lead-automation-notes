import requests

# Parcel ID (no dashes)
parcel_id = "13112041B"

# Check Layer 4 as suggested by user
layers = [
    ("Layer 4", "https://gisdata.pima.gov/arcgis1/rest/services/GISOpenData/LandRecords/MapServer/4/query"),
    ("Layer 12 (Parcels)", "https://gisdata.pima.gov/arcgis1/rest/services/GISOpenData/LandRecords/MapServer/12/query"),
]

for layer_name, url in layers:
    params = {
        "where": f"PARCEL='{parcel_id}'",
        "outFields": "*",
        "returnGeometry": "false",
        "f": "json"
    }
    
    try:
        print(f"\n{layer_name}:")
        r = requests.get(url, params=params, timeout=15)
        print(f"  Status: {r.status_code}, Length: {len(r.text)}")
        
        if r.status_code == 200 and r.text.strip() and not r.text.startswith("<!"):
            data = r.json()
            if data.get("features"):
                attrs = data["features"][0].get("attributes", {})
                # For Layer 4, print ALL fields to see what's available
                if "Layer 4" in layer_name:
                    print(f"  Found {len(attrs)} fields (ALL):")
                    for k, v in sorted(attrs.items()):
                        print(f"    {k}: {v}")
                print(f"  Found {len(attrs)} fields (ALL):")
                for k, v in sorted(attrs.items()):
                    print(f"    {k}: {v}")
            else:
                error = data.get("error", {})
                if error:
                    print(f"  Error: {error.get('message', 'Unknown')}")
                else:
                    print("  No features found")
    except Exception as e:
        print(f"  Error: {e}")
