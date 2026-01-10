
import requests
import json

def list_services():
    url = "https://gisdata.pima.gov/arcgis1/rest/services/GISOpenData?f=json"
    print(f"Querying {url}...")
    try:
        resp = requests.get(url, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            print("\n--- Services ---")
            for service in data.get("services", []):
                print(f"{service['name']} ({service['type']})")
            
            print("\n--- Folders ---")
            for folder in data.get("folders", []):
                print(f"{folder}")
        else:
            print(f"Error: {resp.status_code}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    list_services()
