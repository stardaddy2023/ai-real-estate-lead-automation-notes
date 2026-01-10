
import requests
import json

def inspect_layers():
    # Layer 4: City of Tucson Real Property Inventory
    url_l4 = "https://gisdata.pima.gov/arcgis1/rest/services/GISOpenData/LandRecords/MapServer/4/query"
    # Layer 15: Subdivisions
    url_l15 = "https://gisdata.pima.gov/arcgis1/rest/services/GISOpenData/LandRecords/MapServer/15/query"
    
    # Common params
    params = {
        "where": "1=1", # We'll use spatial query or address if possible, but for now let's try address match if fields exist
        "outFields": "*",
        "f": "json",
        "returnGeometry": "false"
    }
    
    print("--- Inspecting Layer 4 (City of Tucson Real Property Inventory) ---")
    # Try to match by address or parcel if possible. 
    # Since we don't know the exact field names, let's try a broad LIKE query on common address fields if they exist, 
    # or better, use the geometry from the previous Layer 12 result if we had it.
    # For simplicity, let's try to query by PARCEL_ID if it exists, or just grab one feature to see schema.
    
    # Let's try to find the property by address in Layer 4
    params["where"] = "ADDRESS LIKE '%927 N PERRY%'" # Guessing field name 'ADDRESS'
    try:
        response = requests.get(url_l4, params=params)
        data = response.json()
        if "error" in data:
            # If ADDRESS field doesn't exist, try getting one feature to see fields
            print(f"Query failed: {data['error']['message']}")
            print("Fetching schema...")
            params["where"] = "1=1"
            params["resultRecordCount"] = 1
            response = requests.get(url_l4, params=params)
            data = response.json()
            
        if "features" in data and len(data["features"]) > 0:
            print("Attributes found:")
            for k, v in data["features"][0]["attributes"].items():
                print(f"{k}: {v}")
        else:
            print("No features found.")
    except Exception as e:
        print(f"Error L4: {e}")

    print("\n--- Inspecting Layer 15 (Subdivisions) ---")
    # For subdivisions, we usually query by geometry, but let's see if we can find by name or just check schema
    # We'll try to find a subdivision that might match the area.
    # Or better, let's just get the schema to see if 'SUB_NAME' is there.
    params["where"] = "1=1"
    params["resultRecordCount"] = 1
    try:
        response = requests.get(url_l15, params=params)
        data = response.json()
        if "features" in data and len(data["features"]) > 0:
            print("Schema/Attributes sample:")
            for k, v in data["features"][0]["attributes"].items():
                print(f"{k}: {v}")
    except Exception as e:
        print(f"Error L15: {e}")

if __name__ == "__main__":
    inspect_layers()
