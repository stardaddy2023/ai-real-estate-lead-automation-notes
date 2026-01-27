import requests
import json

url = "https://gisdata.pima.gov/arcgis1/rest/services/GISOpenData/LandRecords/MapServer/4?f=json"

print(f"Querying {url}...")
try:
    resp = requests.get(url)
    data = resp.json()
    
    if "fields" in data:
        print("\n=== FIELDS (Layer 4) ===")
        found_sale = False
        for field in data["fields"]:
            if "sale" in field['name'].lower() or "price" in field['name'].lower() or "val" in field['name'].lower():
                print(f"**MATCH**: {field['name']} ({field['alias']})")
                found_sale = True
        
        if not found_sale:
            print("No fields with 'sale', 'price', or 'val' found.")
            # Print first 20 fields just in case
            print([f['name'] for f in data['fields'][:20]])
    else:
        print("No 'fields' key in response.")

except Exception as e:
    print(f"Error: {e}")
