import requests
import json
from shapely.geometry import Polygon, Point, shape

def find_sycamore_canyon_property():
    # 1. Get Path of Progress Geometry for SYCAMORE CANYON
    pop_url = "https://gisdata.pima.gov/arcgis1/rest/services/GISOpenData/OverlayDevelopment/MapServer/13/query"
    pop_params = {
        "where": "PROJ_NAME LIKE '%SYCAMORE CANYON%'",
        "outFields": "PROJ_NAME",
        "returnGeometry": "true",
        "f": "json",
        "outSR": "4326"
    }
    print("Fetching Path of Progress feature...")
    resp = requests.get(pop_url, params=pop_params)
    data = resp.json()
    if not data.get("features"):
        print("PoP not found!")
        return
        
    pop_feature = data["features"][0]
    pop_geom = pop_feature["geometry"]
    if "rings" in pop_geom:
        pop_poly = Polygon(pop_geom["rings"][0])
    else:
        print("PoP has no rings")
        return

    parcel_url = "https://gisdata.pima.gov/arcgis1/rest/services/GISOpenData/LandRecords/MapServer/12/query"
    
    street_names = [
        "CRIMSON SNOWBERRY",
        "MOONTEAR",
        "DESERT BARBERRY",
        "SWEET FERN",
        "TANZANITE ROCK"
    ]
    
    for street in street_names:
        print(f"\nSearching for properties on {street}...")
        params = {
            "where": f"ADDRESS_OL LIKE '%{street}%'",
            "outFields": "PARCEL,ADDRESS_OL,SITUS_ZIP",
            "returnGeometry": "true",
            "f": "json",
            "outSR": "4326"
        }
        
        try:
            resp = requests.get(parcel_url, params=params)
            data = resp.json()
            features = data.get("features", [])
            
            if features:
                print(f"Found {len(features)} candidates.")
                for feat in features:
                    attr = feat["attributes"]
                    geom = feat.get("geometry")
                    
                    if geom and "rings" in geom:
                        poly = Polygon(geom["rings"][0])
                        if pop_poly.contains(poly.representative_point()):
                            address = attr.get("ADDRESS_OL")
                            zip_code = attr.get("SITUS_ZIP")
                            
                            if address:
                                full_address = f"{address}, Tucson, AZ {zip_code}" if zip_code else f"{address}, Tucson, AZ"
                                print("\nSUCCESS! FOUND PROPERTY:")
                                print(f"Address: {full_address}")
                                print(f"Project: {pop_feature['attributes']['PROJ_NAME']}")
                                print(f"Parcel ID: {attr.get('PARCEL')}")
                                return
            else:
                print("No properties found.")
        except Exception as e:
            print(f"Error: {e}")

    print("No properties found inside the project matching these streets.")

if __name__ == "__main__":
    find_sycamore_canyon_property()
