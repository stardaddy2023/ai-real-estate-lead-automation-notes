import requests
import json
from shapely.geometry import Polygon, Point, shape

def find_property_in_other_subdivision():
    # 1. List available projects
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

    print(f"Found {len(features)} projects. Trying to find a property...")

    for feature in features:
        proj_name = feature["attributes"]["PROJ_NAME"]
        print(f"\nChecking Project: {proj_name}")
        
        geom = feature["geometry"]
        if "rings" not in geom:
            continue
            
        try:
            poly = Polygon(geom["rings"][0])
            min_x, min_y, max_x, max_y = poly.bounds
            centroid = poly.centroid
            
            # Points to test: Centroid + small grid around it
            points_to_test = [centroid]
            step = 0.0005 # Approx 50 meters
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx == 0 and dy == 0: continue
                    points_to_test.append(Point(centroid.x + dx * step, centroid.y + dy * step))
            
            for pt in points_to_test:
                if not poly.contains(pt):
                    continue
                    
                # Query Layer 12 (Parcels) using Point
                parcel_url = "https://gisdata.pima.gov/arcgis1/rest/services/GISOpenData/LandRecords/MapServer/12/query"
                
                # Use a tiny envelope around the point for intersection
                buffer = 0.00001
                envelope = {
                    "xmin": pt.x - buffer,
                    "ymin": pt.y - buffer,
                    "xmax": pt.x + buffer,
                    "ymax": pt.y + buffer,
                    "spatialReference": {"wkid": 4326}
                }
                
                parcel_params = {
                    "geometry": json.dumps(envelope),
                    "geometryType": "esriGeometryEnvelope",
                    "spatialRel": "esriSpatialRelIntersects",
                    "outFields": "PARCEL,ADDRESS_OL,SITUS_ZIP",
                    "returnGeometry": "false",
                    "where": "1=1",
                    "f": "json",
                    "outSR": "4326",
                    "inSR": "4326"
                }
                
                p_resp = requests.get(parcel_url, params=parcel_params)
                p_data = p_resp.json()
                p_features = p_data.get("features", [])
                
                if p_features:
                    p_attr = p_features[0]["attributes"]
                    address = p_attr.get("ADDRESS_OL")
                    zip_code = p_attr.get("SITUS_ZIP")
                    
                    if address:
                        full_address = f"{address}, Tucson, AZ {zip_code}" if zip_code else f"{address}, Tucson, AZ"
                        print("\nSUCCESS! FOUND PROPERTY:")
                        print(f"Address: {full_address}")
                        print(f"Project: {proj_name}")
                        print(f"Parcel ID: {p_attr.get('PARCEL')}")
                        return
            
            print("  No parcels found via point sampling.")
                
        except Exception as e:
            print(f"  Error processing project: {e}")

if __name__ == "__main__":
    find_property_in_other_subdivision()
