import requests
import json

url = "https://gisdata.pima.gov/arcgis1/rest/services/GISOpenData/LandRecords/MapServer/12/query"

# 106020300 format might be 106-02-0300 in the system? The screenshot shows 106-02-0300 on Pima Assessor, but APN: 106020300 in UI.
# Let's try matching PARCEL='106020300' first.

params = {
    "where": "PARCEL='106020300'",
    "outFields": "*",
    "f": "json"
}

print(f"Querying {url} for PARCEL='106020300'...")
try:
    resp = requests.get(url, params=params)
    data = resp.json()
    
    if data.get("features"):
        print(f"Found {len(data['features'])} feature(s).")
        feat = data['features'][0]
        attrs = feat['attributes']
        print("\n=== ATTRIBUTES ===")
        # Print relevant fields
        relevant = ['PARCEL', 'Sale_Price', 'Sale_Date', 'RECORDDATE', 'SEQ_NUM_S', 'SEQ_NUM_D', 'DOCKET', 'PAGE']
        for k in relevant:
            print(f"{k}: {attrs.get(k)}")
            
        print("\n=== ALL ATTRIBUTES (Keys) ===")
        print(list(attrs.keys()))
        
        # Check if Sale_Price is present but null
        if 'Sale_Price' in attrs:
            print(f"\nSale_Price value: {attrs['Sale_Price']} (Type: {type(attrs['Sale_Price'])})")
        else:
            print("\nSale_Price field NOT in attributes!")
            
    else:
        print("No features found matching PARCEL='106020300'.")
        print("Response:", json.dumps(data, indent=2))

except Exception as e:
    print(f"Error: {e}")
