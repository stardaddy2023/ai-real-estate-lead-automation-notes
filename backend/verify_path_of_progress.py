import asyncio
import requests
import json
from app.services.pipeline.scout import ScoutService

async def verify_path_of_progress():
    print("Verifying Path of Progress Logic...")
    
    # Check MapServer Info first
    root_url = "https://gisdata.pima.gov/arcgis1/rest/services/GISOpenData/OverlayDevelopment/MapServer?f=json"
    print(f"Checking MapServer Info: {root_url}")
    try:
        resp = requests.get(root_url, timeout=10)
        if resp.status_code == 200:
            info = resp.json()
            layers = info.get("layers", [])
            print("Available Layers:")
            for l in layers:
                print(f"  ID: {l['id']}, Name: {l['name']}")
        else:
            print(f"Error fetching MapServer info: {resp.status_code}")
    except Exception as e:
        print(f"Error: {e}")

    # Check Layer 13 Metadata
    layer_url = "https://gisdata.pima.gov/arcgis1/rest/services/GISOpenData/OverlayDevelopment/MapServer/13?f=json"
    print(f"Checking Layer 13 Metadata: {layer_url}")
    try:
        resp = requests.get(layer_url, timeout=10)
        if resp.status_code == 200:
            info = resp.json()
            fields = info.get("fields", [])
            print("Layer Fields:")
            for f in fields:
                print(f"  {f['name']} ({f['type']})")
            
            # Check maxRecordCount
            print(f"Max Record Count: {info.get('maxRecordCount')}")
    except Exception as e:
        print(f"Error: {e}")

    # 1. Query the GIS Layer directly to find ALL features (simulate fetchAll)
    url = "https://gisdata.pima.gov/arcgis1/rest/services/GISOpenData/OverlayDevelopment/MapServer/13/query"
    params = {
        "where": "1=1",
        "outFields": "*", # Try * to be safe
        "returnGeometry": "true",
        "outSR": "4326",
        "f": "json",
        "resultRecordCount": 10 # Try with limit first
    }
    
    print(f"Querying {url} for ALL features...")
    
    try:
        resp = requests.get(url, params=params, timeout=30)
        if resp.status_code != 200:
            print(f"Error: GIS API returned {resp.status_code}")
            return
        
        content_size = len(resp.content) / 1024 / 1024 # MB
        print(f"Response Size: {content_size:.2f} MB")
        
        data = resp.json()
        features = data.get("features", [])
        print(f"Found {len(features)} features.")
        
        if content_size > 5:
            print("WARNING: Layer is too large for fetchAll.")
        else:
            print("Layer size is acceptable for fetchAll.")
            
        if not features:
            print("No features found.")
            return

        # Pick the first feature
        sample = features[0]
        attr = sample.get("attributes", {})
        geom = sample.get("geometry", {})
        
        if not features:
            print("No features found in Path of Progress layer (Layer 13).")
            # Try querying other layers if found
            return
        
        print(f"Found {len(features)} sample features in Path of Progress layer.")
        
        # Pick the first feature
        sample = features[0]
        attr = sample.get("attributes", {})
        geom = sample.get("geometry", {})
        
        print(f"Sample Feature: {attr}")
        
        # Get a point inside this feature (Centroid)
        lat, lon = None, None
        if "rings" in geom:
            # Calculate simple centroid of the first ring
            ring = geom["rings"][0]
            sum_x = sum(p[0] for p in ring)
            sum_y = sum(p[1] for p in ring)
            count = len(ring)
            lon = sum_x / count
            lat = sum_y / count
            print(f"Sample Coordinate (Centroid): Lat={lat}, Lon={lon}")
        else:
            print("No geometry rings found.")
            return

        # 3. Test simplified spatial query (Point)
        print("\nTesting simplified spatial query (Point)...")
        point_geom = {
            "x": lon,
            "y": lat,
            "spatialReference": {"wkid": 4326}
        }
        params_spatial = {
            "geometry": json.dumps(point_geom),
            "geometryType": "esriGeometryPoint",
            "spatialRel": "esriSpatialRelIntersects",
            "inSR": "4326",
            "outFields": "PLAT_NAME,STATUS",
            "returnGeometry": "false",
            "f": "json"
        }
        
        try:
            resp = requests.get(url, params=params_spatial, timeout=10)
            print(f"Spatial Query Status: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
                if "error" in data:
                    print(f"Spatial Query Error: {data['error']}")
                else:
                    feats = data.get("features", [])
                    print(f"Spatial Query Found: {len(feats)} features")
                    if feats:
                        print(f"Sample: {feats[0]['attributes']}")
            else:
                print(f"Spatial Query Failed: {resp.text}")
        except Exception as e:
            print(f"Spatial Query Exception: {e}")

        # 2. Test ScoutService Enrichment with this coordinate
        service = ScoutService()
        
        # Create a mock lead at this location
        mock_lead = {
            "address": "TEST LOCATION",
            "latitude": lat,
            "longitude": lon,
            "parcel_id": "TEST-123"
        }
        
        print("\nTesting ScoutService._enrich_with_gis_layers with mock lead...")
        # We need to bypass the cache check in needs_gis, so we ensure _cache_enriched is False
        mock_lead["_cache_enriched"] = False
        
        # Call the private method (for testing purposes)
        await service._enrich_with_gis_layers([mock_lead])
        
        print("\nEnrichment Result:")
        print(f"Nearby Development: {mock_lead.get('nearby_development')}")
        print(f"Development Status: {mock_lead.get('development_status')}")
        
        expected_name = attr.get("PROJ_NAME")
        if mock_lead.get("nearby_development") == expected_name:
            print(f"SUCCESS: Logic correctly identified the Path of Progress: {expected_name}")
        else:
            print(f"FAILURE: Logic failed to identify the Path of Progress. Expected {expected_name}, got {mock_lead.get('nearby_development')}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(verify_path_of_progress())
