import requests

# Query Layer 12 (Parcels-Regional) to see all available fields
url = "https://gisdata.pima.gov/arcgis1/rest/services/GISOpenData/LandRecords/MapServer/12?f=json"

print("Fetching Layer 12 (Parcels-Regional) field schema...")
r = requests.get(url, timeout=30)
print(f"Status: {r.status_code}")

if r.status_code == 200:
    d = r.json()
    print(f"\nLayer: {d.get('name')}")
    print(f"Fields ({len(d.get('fields', []))} total):\n")
    
    for f in d.get("fields", []):
        alias = f.get("alias", "")
        name = f.get("name")
        ftype = f.get("type", "").replace("esriFieldType", "")
        
        # Highlight sale/recording related fields
        keywords = ["sale", "sold", "record", "docket", "page", "seq", "deed", "doc", "affidavit"]
        is_relevant = any(k in name.lower() or k in alias.lower() for k in keywords)
        marker = " <<< RELEVANT" if is_relevant else ""
        
        print(f"  {name:40} ({ftype:10}) - {alias}{marker}")
