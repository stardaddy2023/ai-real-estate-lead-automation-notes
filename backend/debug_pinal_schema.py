import requests
import json

def get_pinal_schema():
    url = "https://rogue.casagrandeaz.gov/arcgis/rest/services/Pinal_County/Pinal_County_Assessor_Info/MapServer/0/query"
    
    # Query for just one record to see the fields
    params = {
        "where": "OBJECTID < 100", # Get a few records
        "outFields": "*",
        "returnGeometry": "false",
        "f": "json",
        "resultRecordCount": 1
    }
    
    try:
        print(f"Querying: {url}")
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if "features" in data and len(data["features"]) > 0:
            attr = data["features"][0]["attributes"]
            print("\n--- Pinal County Record Schema ---")
            for key, value in attr.items():
                print(f"{key}: {value}")
        else:
            print("No features found or error in response.")
            print(json.dumps(data, indent=2))
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    get_pinal_schema()
