import asyncio
import sys
import os
import requests
import json
from shapely.geometry import Polygon

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.services.pipeline.scout import ScoutService

async def debug_property_display():
    apn = "131121240"
    print(f"Debugging Property Display for APN: {apn}...")
    
    # 1. Search by PARCEL in GIS
    url = "https://gisdata.pima.gov/arcgis1/rest/services/GISOpenData/LandRecords/MapServer/12/query"
    params = {
        "where": f"PARCEL='{apn}'",
        "outFields": "*",
        "outSR": "4326",
        "f": "json"
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        if r.status_code == 200:
            data = r.json()
            features = data.get("features", [])
            if features:
                attrs = features[0].get("attributes", {})
                print("\n=== Raw GIS Attributes ===")
                print(json.dumps(attrs, indent=2))
                
                # Get coordinates for Scout test
                geom = features[0].get("geometry")
                if geom and "rings" in geom:
                    poly = Polygon(geom["rings"][0])
                    centroid = poly.centroid
                    print(f"\nCentroid: {centroid.y}, {centroid.x}")
                    
                    # 2. Test ScoutService Enrichment with REAL coordinates
                    scout = ScoutService()
                    leads = [{
                        "address_street": attrs.get("ADDRESS_OL", "Unknown"),
                        "latitude": centroid.y,
                        "longitude": centroid.x,
                        "id": f"debug_lead_{apn}"
                    }]
                    
                    print("\n=== Running ScoutService Enrichment ===")
                    # Force enrichment by mocking the spatial query result if needed
                    # But first try the real method
                    await scout._enrich_violations_with_parcel_data(leads)
                    
                    lead = leads[0]
                    
                    # Manual Mapping Check (if enrichment failed)
                    if not lead.get("_parcel_enriched"):
                        print("\n[WARNING] Enrichment failed (spatial mismatch). Testing mapping logic manually:")
                        use_code = str(attrs.get("PARCEL_USE", "")).strip()
                        print(f"Use Code: '{use_code}'")
                        
                        # Access the internal mapping dict (hacky but needed for debug)
                        # We need to recreate the dict since it's local to the method
                        PROPERTY_USE_CODES = {
                                            "0182": "Single Family Residence",
                                            "0011": "Vacant Residential",
                                            "0013": "Vacant Residential (Rural)",
                                            "0111": "Single Family Residence",
                                            "0113": "Single Family Residence (Rural)",
                                            "0131": "Mobile Home",
                                            "0133": "Mobile Home (Rural)",
                                            "0300": "Multi-Family",
                                            "0311": "Duplex",
                                            "0312": "Triplex",
                                            "0313": "Fourplex",
                                            "0411": "Apartment",
                                            "0210": "Commercial",
                                            "0211": "Commercial Office",
                                            "0212": "Commercial Retail",
                                            "0213": "Commercial Service",
                                            "0131": "Single Family Residence",
                                        }
                        if use_code in PROPERTY_USE_CODES:
                            print(f"Mapped Type: '{PROPERTY_USE_CODES[use_code]}'")
                        else:
                            print("Mapping FAILED - Code not in dictionary")
                    # 3. Test _map_pima_parcel Logic (Direct Search Path)
                    print("\n=== Testing _map_pima_parcel Logic ===")
                    # Construct a mock feature
                    feature = {
                        "attributes": attrs,
                        "geometry": {"x": centroid.x, "y": centroid.y}
                    }
                    mapped_lead = scout._map_pima_parcel(feature)
                    
                    if mapped_lead:
                        print(f"Property Type: '{mapped_lead.get('property_type')}'")
                        print(f"Parcel Use Code: '{mapped_lead.get('parcel_use_code')}'")
                        print(f"Seq Num: '{mapped_lead.get('seq_num')}'")
                        print(f"Recording Seq Num: '{mapped_lead.get('recording_seq_num')}'")
                        print(f"Last Sold Date: '{mapped_lead.get('last_sold_date')}'")
                        print(f"Last Sold Price: '{mapped_lead.get('last_sold_price')}'")
                    else:
                        print("Mapping returned None")
            else:
                print("No features found in GIS for this address.")
    except Exception as e:
        print(f"Error fetching GIS data: {e}")

if __name__ == "__main__":
    asyncio.run(debug_property_display())
