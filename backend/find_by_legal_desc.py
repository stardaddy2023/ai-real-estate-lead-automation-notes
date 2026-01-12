import requests
import json
from shapely.geometry import Polygon, Point, shape

def find_by_legal():
    # 1. List available projects to get names
    pop_url = "https://gisdata.pima.gov/arcgis1/rest/services/GISOpenData/OverlayDevelopment/MapServer/13/query"
    params = {
        "where": "PROJ_NAME <> 'MONTANAS DEL SOL (1-48)'",
        "outFields": "PROJ_NAME",
        "returnGeometry": "true",
        "f": "json",
        "resultRecordCount": 20,
        "outSR": "4326"
    }
    
    print("Fetching available projects...")
    resp = requests.get(pop_url, params=params)
    data = resp.json()
    features = data.get("features", [])
    
    if not features:
        print("No other projects found.")
        return

    print(f"Found {len(features)} projects. Trying to match via Legal Description...")

    parcel_url = "https://gisdata.pima.gov/arcgis1/rest/services/GISOpenData/LandRecords/MapServer/12/query"

    for feature in features:
        proj_name = feature["attributes"]["PROJ_NAME"]
        # Clean project name for search (remove (1-48) etc)
        search_term = proj_name.split('(')[0].strip()
        
        # Skip if too short or generic
        if len(search_term) < 5: 
            continue
            
        print(f"\nChecking Project: {proj_name} (Search: '{search_term}')")
        
        # Search LEGAL1
        where_clause = f"LEGAL1 LIKE '%{search_term}%'"
        
        p_params = {
            "where": where_clause,
            "outFields": "PARCEL,ADDRESS_OL,SITUS_ZIP,LEGAL1",
            "returnGeometry": "true",
            "f": "json",
            "resultRecordCount": 5,
            "outSR": "4326"
        }
        
        try:
            p_resp = requests.get(parcel_url, params=p_params)
            p_data = p_resp.json()
            p_features = p_data.get("features", [])
            
            if p_features:
                print(f"  Found {len(p_features)} candidates by Legal Description.")
                
                # Verify containment
                pop_geom = feature["geometry"]
                if "rings" in pop_geom:
                    pop_poly = Polygon(pop_geom["rings"][0])
                    
                    for p_feat in p_features:
                        p_attr = p_feat["attributes"]
                        p_geom = p_feat.get("geometry")
                        
                        if p_geom and "rings" in p_geom:
                            p_poly = Polygon(p_geom["rings"][0])
                            
                            # Check containment
                            if pop_poly.contains(p_poly.representative_point()):
                                address = p_attr.get("ADDRESS_OL")
                                zip_code = p_attr.get("SITUS_ZIP")
                                
                                if address:
                                    full_address = f"{address}, Tucson, AZ {zip_code}" if zip_code else f"{address}, Tucson, AZ"
                                    print("\nSUCCESS! FOUND PROPERTY:")
                                    print(f"Address: {full_address}")
                                    print(f"Project: {proj_name}")
                                    print(f"Parcel ID: {p_attr.get('PARCEL')}")
                                    print(f"Legal: {p_attr.get('LEGAL1')}")
                                    return
                print("  Candidates found but none inside the project polygon (or no address).")
            else:
                print("  No parcels found matching legal description.")
                
        except Exception as e:
            print(f"  Error searching project: {e}")

if __name__ == "__main__":
    find_by_legal()
