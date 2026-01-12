import requests
import json
from shapely.geometry import Polygon, Point, shape

def find_nearby_properties():
    # 1. Get Path of Progress Geometry for MONTANAS DEL SOL in State Plane (2868)
    pop_url = "https://gisdata.pima.gov/arcgis1/rest/services/GISOpenData/OverlayDevelopment/MapServer/13/query"
    pop_params = {
        "where": "PROJ_NAME LIKE '%MONTANAS DEL SOL%'",
        "outFields": "PROJ_NAME",
        "returnGeometry": "true",
        "f": "json",
        "outSR": "2868"
    }
    print("Fetching Path of Progress feature (in State Plane Feet)...")
    resp = requests.get(pop_url, params=pop_params)
    data = resp.json()
    if not data.get("features"):
        print("PoP not found!")
        return
        
    pop_feature = data["features"][0]
    pop_geom = pop_feature["geometry"]
    
    if "rings" in pop_geom:
        pop_poly = Polygon(pop_geom["rings"][0])
        centroid = pop_poly.centroid
    else:
        print("PoP has no rings")
        return

    print(f"Project: {pop_feature['attributes']['PROJ_NAME']}")
    print(f"Centroid: {centroid.x}, {centroid.y}")
    
    parcel_url = "https://gisdata.pima.gov/arcgis1/rest/services/GISOpenData/LandRecords/MapServer/12/query"
    
    # Buffer by 1 mile = 5280 feet
    buffer_dist = 5280
    
    # Define the full extent
    start_x = centroid.x - buffer_dist
    start_y = centroid.y - buffer_dist
    end_x = centroid.x + buffer_dist
    end_y = centroid.y + buffer_dist
    
    # Grid search (5x5)
    steps = 5
    step_x = (end_x - start_x) / steps
    step_y = (end_y - start_y) / steps
    
    # Debug ONLY the center cell (2,2)
    i, j = 2, 2
    
    cell_min_x = start_x + i * step_x
    cell_min_y = start_y + j * step_y
    cell_max_x = cell_min_x + step_x
    cell_max_y = cell_min_y + step_y
    
    envelope = {
        "xmin": cell_min_x,
        "ymin": cell_min_y,
        "xmax": cell_max_x,
        "ymax": cell_max_y,
        "spatialReference": {"wkid": 2868}
    }
    
    print(f"Debugging Center Cell Envelope: {envelope}")
    
    params = {
        "geometry": json.dumps(envelope),
        "geometryType": "esriGeometryEnvelope",
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": "PARCEL,ADDRESS_OL,SITUS_ZIP",
        "returnGeometry": "true",
        "where": "1=1",
        "f": "json",
        "outSR": "2868",
        "inSR": "2868",
        "resultRecordCount": 50
    }
    
    print("Request Params:")
    print(json.dumps(params, indent=2))
    
    try:
        resp = requests.get(parcel_url, params=params)
        print(f"Response Status: {resp.status_code}")
        data = resp.json()
        
        if "error" in data:
            print("API Error:", data["error"])
            
        features = data.get("features", [])
        print(f"Features found: {len(features)}")
        
        if features:
            for feat in features:
                print(f" - {feat['attributes']['ADDRESS_OL']}")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    find_nearby_properties()
