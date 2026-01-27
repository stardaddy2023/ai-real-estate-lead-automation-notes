import requests
import json

base_url = "https://gisdata.pima.gov/arcgis1/rest/services/GISOpenData/LandRecords/MapServer"

layers = [12, 2]

for layer_id in layers:
    url = f"{base_url}/{layer_id}?f=json"
    print(f"\nQuerying Layer {layer_id} metadata...")
    try:
        resp = requests.get(url)
        data = resp.json()
        
        if "fields" in data:
            print(f"=== FIELDS (Layer {layer_id}) ===")
            for field in data["fields"]:
                if "sale" in field['name'].lower() or "price" in field['name'].lower() or "amount" in field['name'].lower():
                    print(f"**MATCH**: {field['name']} ({field['alias']})")
                else:
                    # Print all just in case
                    pass
            # Print full list if short
            print([f['name'] for f in data['fields']])
        else:
            print(f"No fields found for Layer {layer_id}")
            
    except Exception as e:
        print(f"Error: {e}")
