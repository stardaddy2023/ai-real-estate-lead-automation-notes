import requests
import json

def test_spatial_query():
    url = "https://gis.tucsonaz.gov/arcgis/rest/services/PDSD/pdsdMain_General5/MapServer/94/query"
    
    # Envelope for Green Valley (approx)
    envelope = {
        "xmin": 933332.149934385,
        "ymin": 273540.4163385853,
        "xmax": 1011463.1870078743,
        "ymax": 468146.64271653444,
        "spatialReference": {"wkid": 2868}
    }
    
    # Test 1: Standard JSON Geometry
    print("Test 1: Standard JSON Geometry (inSR=2868)")
    params = {
        "where": "1=1",
        "geometry": json.dumps(envelope),
        "geometryType": "esriGeometryEnvelope",
        "spatialRel": "esriSpatialRelIntersects",
        "inSR": "2868",
        "outFields": "OBJECTID,ADDRESSFULL",
        "returnGeometry": "true",
        "f": "json",
        "resultRecordCount": 5
    }
    run_query(url, params)

    # Test 2: Bbox String
    print("\nTest 2: Bbox String (inSR=2868)")
    bbox = f"{envelope['xmin']},{envelope['ymin']},{envelope['xmax']},{envelope['ymax']}"
    params["geometry"] = bbox
    run_query(url, params)

    # Test 3: No inSR (Defaults to Map SR)
    print("\nTest 3: No inSR (Defaults to Map SR)")
    params["geometry"] = json.dumps(envelope)
    if "inSR" in params: del params["inSR"]
    run_query(url, params)

    # Test 4: CONTROL - No Geometry
    print("\nTest 4: CONTROL - No Geometry")
    params_control = {
        "where": "1=1",
        "outFields": "OBJECTID,ADDRESSFULL",
        "returnGeometry": "true",
        "f": "json",
        "resultRecordCount": 5
    }
    run_query(url, params_control)

def run_query(url, params):
    try:
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            features = data.get("features", [])
            print(f"Found {len(features)} features.")
            for f in features:
                geom = f.get("geometry", {})
                print(f" - {f['attributes']['ADDRESSFULL']} (X: {geom.get('x')}, Y: {geom.get('y')})")
        else:
            print(f"Error: {resp.status_code}")
            print(resp.text)
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_spatial_query()
