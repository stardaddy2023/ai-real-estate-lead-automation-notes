"""
Verification script to count code violations on vacant land in 85705.
Now with PAGINATION to fetch all violations (not just 1000) and
both BOUNDS and POLYGON filtering.
"""
import requests
import json
from shapely.geometry import Point, Polygon, box

# URLs (same as scout.py)
VIOLATIONS_URL = "https://gis.tucsonaz.gov/arcgis/rest/services/PDSD/pdsdMain_General5/MapServer/94/query"
PARCELS_URL = "https://gisdata.pima.gov/arcgis1/rest/services/GISOpenData/LandRecords/MapServer/12/query"
ZIP_URL = "https://gisdata.pima.gov/arcgis1/rest/services/GISOpenData/Addresses/MapServer/6/query"

def get_zip_metadata(zip_code: str):
    """Get the polygon and bounding box for a zip code."""
    params = {
        "where": f"ZIPCODE = '{zip_code}'",
        "outFields": "*",
        "returnGeometry": "true",
        "outSR": "4326",
        "f": "json"
    }
    resp = requests.get(ZIP_URL, params=params, timeout=15)
    if resp.status_code == 200:
        data = resp.json()
        features = data.get("features", [])
        if features:
            geom = features[0].get("geometry", {})
            if "rings" in geom:
                polygon = Polygon(geom["rings"][0])
                bounds = polygon.bounds  # (minx, miny, maxx, maxy)
                return {
                    "polygon": polygon,
                    "bounds": {
                        "xmin": bounds[0],
                        "ymin": bounds[1],
                        "xmax": bounds[2],
                        "ymax": bounds[3]
                    }
                }
    return None

def fetch_violations_with_pagination(bounds, max_records=5000):
    """Fetch ALL code violations within bounds using pagination."""
    envelope = {
        "xmin": bounds['xmin'],
        "ymin": bounds['ymin'],
        "xmax": bounds['xmax'],
        "ymax": bounds['ymax'],
        "spatialReference": {"wkid": 4326}
    }
    
    base_params = {
        "where": "STATUS_1 NOT IN ('COMPLIAN', 'CLOSED', 'VOID')",
        "outFields": "*",
        "returnGeometry": "true",
        "outSR": "4326",
        "orderByFields": "DT_ENT DESC",
        "geometry": json.dumps(envelope),
        "geometryType": "esriGeometryEnvelope",
        "spatialRel": "esriSpatialRelIntersects",
        "inSR": "4326",
        "f": "json"
    }
    
    all_features = []
    batch_size = 1000
    offset = 0
    
    while len(all_features) < max_records:
        params = base_params.copy()
        params["resultRecordCount"] = batch_size
        params["resultOffset"] = offset
        
        resp = requests.get(VIOLATIONS_URL, params=params, timeout=30)
        if resp.status_code != 200:
            print(f"Error fetching violations: {resp.status_code}")
            break
        
        data = resp.json()
        features = data.get("features", [])
        
        if not features:
            break  # No more data
        
        all_features.extend(features)
        print(f"  Batch {offset//batch_size + 1}: Fetched {len(features)} violations (total: {len(all_features)})")
        
        if len(features) < batch_size:
            break  # Last batch
        
        offset += batch_size
    
    return all_features

def filter_by_bounds(violations, bounds):
    """Filter violations using simple bounding box (rectangle)."""
    bounding_box = box(bounds["xmin"], bounds["ymin"], bounds["xmax"], bounds["ymax"])
    
    filtered = []
    for v in violations:
        geom = v.get("geometry", {})
        if geom and "x" in geom and "y" in geom:
            pt = Point(geom["x"], geom["y"])
            if bounding_box.contains(pt):
                filtered.append(v)
    
    return filtered

def filter_by_polygon(violations, polygon):
    """Filter violations using actual zip code polygon."""
    filtered = []
    for v in violations:
        geom = v.get("geometry", {})
        if geom and "x" in geom and "y" in geom:
            pt = Point(geom["x"], geom["y"])
            if polygon.contains(pt):
                filtered.append(v)
    
    return filtered

def deduplicate_by_address(violations):
    """Deduplicate violations by address."""
    unique = {}
    for v in violations:
        addr = (v["attributes"].get("ADDRESSFULL") or "").upper().strip()
        if addr and addr not in unique:
            unique[addr] = {
                "id": v["attributes"].get("ACT_NUM"),
                "address": v["attributes"].get("ADDRESSFULL"),
                "lon": v["geometry"]["x"],
                "lat": v["geometry"]["y"]
            }
    return list(unique.values())

def check_parcel_types(violations):
    """Check PARCEL_USE for each violation location."""
    # Vacant Land codes: 00-X (00-1=Res, 00-2=Comm, etc.)
    vacant_land_prefixes = ["00"]
    
    if not violations:
        print("No violations to check")
        return 0, []
    
    # Build multipoint
    points = [[v["lon"], v["lat"]] for v in violations]
    multipoint = {
        "points": points,
        "spatialReference": {"wkid": 4326}
    }
    
    params = {
        "geometry": json.dumps(multipoint),
        "geometryType": "esriGeometryMultipoint",
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": "PARCEL_USE",
        "returnGeometry": "true",
        "outSR": "4326",
        "f": "json"
    }
    
    resp = requests.post(PARCELS_URL, data=params, timeout=60)
    if resp.status_code != 200:
        print(f"Error fetching parcels: {resp.status_code}")
        return 0, []
    
    data = resp.json()
    features = data.get("features", [])
    print(f"  Found {len(features)} parcel features")
    
    # Map parcels to violations
    parcels = []
    for f in features:
        attr = f.get("attributes", {})
        geom = f.get("geometry", {})
        if geom and "rings" in geom:
            try:
                poly = Polygon(geom["rings"][0])
                parcels.append((poly, str(attr.get("PARCEL_USE", ""))))
            except:
                pass
    
    # Check each violation
    vacant_list = []
    for v in violations:
        pt = Point(v["lon"], v["lat"])
        for poly, use_code in parcels:
            if poly.contains(pt):
                if any(use_code.startswith(prefix) for prefix in vacant_land_prefixes):
                    vacant_list.append({"address": v["address"], "code": use_code})
                break
    
    return len(vacant_list), vacant_list

def main():
    import sys
    # Accept zip code as command line argument, default to 85711
    zip_code = sys.argv[1] if len(sys.argv) > 1 else "85711"
    
    print("=" * 70)
    print(f"VERIFICATION: Code Violations on Vacant Land in {zip_code}")
    print("=" * 70)
    
    print("\n1. Getting zip code metadata (polygon + bounds)...")
    zip_meta = get_zip_metadata(zip_code)
    if not zip_meta:
        print("ERROR: Could not get zip metadata")
        return
    print(f"   Bounds: {zip_meta['bounds']}")
    print("   OK")
    
    print("\n2. Fetching ALL code violations with pagination...")
    all_violations = fetch_violations_with_pagination(zip_meta["bounds"], max_records=5000)
    print(f"   Total raw violations fetched: {len(all_violations)}")
    
    print("\n3. Comparing filtering methods...")
    
    # Bounds filtering (rectangle)
    bounds_filtered = filter_by_bounds(all_violations, zip_meta["bounds"])
    bounds_unique = deduplicate_by_address(bounds_filtered)
    print(f"   BOUNDS (rectangle): {len(bounds_filtered)} violations → {len(bounds_unique)} unique")
    
    # Polygon filtering (actual zip boundary)
    polygon_filtered = filter_by_polygon(all_violations, zip_meta["polygon"])
    polygon_unique = deduplicate_by_address(polygon_filtered)
    print(f"   POLYGON (actual):   {len(polygon_filtered)} violations → {len(polygon_unique)} unique")
    
    print(f"\n   Difference: {len(bounds_unique) - len(polygon_unique)} extra in bounds (outside actual zip polygon)")
    
    print("\n4. Checking property types for BOUNDS-filtered violations...")
    bounds_vacant_count, bounds_vacant_list = check_parcel_types(bounds_unique)
    
    print("\n5. Checking property types for POLYGON-filtered violations...")
    polygon_vacant_count, polygon_vacant_list = check_parcel_types(polygon_unique)
    
    print("\n" + "=" * 70)
    print("RESULTS COMPARISON")
    print("=" * 70)
    print(f"\nBOUNDS-based (rectangle):   {bounds_vacant_count} vacant land properties")
    print(f"POLYGON-based (actual zip): {polygon_vacant_count} vacant land properties")
    print(f"\nDifference: {bounds_vacant_count - polygon_vacant_count}")
    
    print("\n" + "-" * 70)
    print("BOUNDS-based vacant land addresses:")
    for v in bounds_vacant_list[:30]:
        print(f"  {v['address']} (code: {v['code']})")
    if len(bounds_vacant_list) > 30:
        print(f"  ... and {len(bounds_vacant_list) - 30} more")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    main()
