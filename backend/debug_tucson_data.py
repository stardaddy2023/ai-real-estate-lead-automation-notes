import requests
import json

# Pima GIS - Layer 4 - City of Tucson Real Property Inventory
url = "https://gisdata.pima.gov/arcgis1/rest/services/GISOpenData/LandRecords/MapServer/4/query"

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
        print(f"PARCEL: {attrs.get('PARCEL')}")
        print(f"SALE_PRICE: {attrs.get('SALE_PRICE')}")
        print(f"SALE_DATE: {attrs.get('SALE_DATE')}")
        print(f"PUR_PRICE: {attrs.get('PUR_PRICE')}")
        print(f"TOT_PRICE: {attrs.get('TOT_PRICE')}")
    else:
        print("No features found matching PARCEL='106020300'.")
        
except Exception as e:
    print(f"Error: {e}")
