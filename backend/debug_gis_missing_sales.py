import asyncio
import sys
import os
import requests
import json
from shapely.geometry import Polygon, Point

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.services.pipeline.scout import ScoutService

def get_parcel_centroid(apn):
    url = "https://gisdata.pima.gov/arcgis1/rest/services/GISOpenData/LandRecords/MapServer/12/query"
    params = {
        "where": f"PARCEL='{apn}'",
        "returnGeometry": "true",
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
                geom = features[0].get("geometry")
                if geom and "rings" in geom:
                    poly = Polygon(geom["rings"][0])
                    centroid = poly.centroid
                    print(f"Fetched centroid for {apn}: {centroid.y}, {centroid.x}")
                    return centroid.y, centroid.x
    except Exception as e:
        print(f"Error fetching centroid: {e}")
    return None, None

def inspect_attributes(apn):
    print(f"Inspecting attributes for {apn}...")
    url = "https://gisdata.pima.gov/arcgis1/rest/services/GISOpenData/LandRecords/MapServer/12/query"
    params = {
        "where": f"PARCEL='{apn}'",
        "outFields": "*",
        "f": "json"
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        if r.status_code == 200:
            data = r.json()
            features = data.get("features", [])
            if features:
                attrs = features[0].get("attributes", {})
                print(f"Full Attributes: {json.dumps(attrs, indent=2)}")
            else:
                print("No features found for inspection.")
    except Exception as e:
        print(f"Error inspecting attributes: {e}")

async def test_enrichment():
    # Test Case 1: Missing Sales Data (APN 126110420)
    print("\n=== TEST CASE 1: Missing Sales Data (APN 126110420) ===")
    await run_test("126110420", "Docket: 6686, Page: 550", "1981-12-29")

    # Test Case 2: Normal Sales Data (APN 131020870)
    print("\n=== TEST CASE 2: Normal Sales Data (APN 131020870) ===")
    await run_test("131020870", "20150280362", "2015-01-28")

    # Test Case 3: User Reported Issue (APN 126172760)
    print("\n=== TEST CASE 3: User Reported Issue (APN 126172760) ===")
    # Expecting Sale Date 6/2021, Price $360,000 (from screenshot)
    # Current behavior suspect: Showing Recording Date 5/15/2022
    await run_test("126172760", None, "2021-06-01") # Approximate date expectation

async def run_test(apn, expected_seq, expected_date):
    # Inspect raw attributes first
    inspect_attributes(apn)

    # Get real coordinates first
    lat, lon = get_parcel_centroid(apn)
    
    if not lat:
        print("Could not fetch parcel coordinates. Using fallback.")
        lat, lon = 32.196, -110.866
        
    scout = ScoutService()
    
    leads = [{
        "address_street": "Test St",
        "latitude": lat, 
        "longitude": lon,
        "id": f"test_lead_{apn}",
        # Simulate HomeHarvest data if we are testing preservation
        "last_sold_date": "2021-06-01" if apn == "126172760" else None
    }]
    
    print(f"Testing ScoutService enrichment for APN {apn} at {lat}, {lon}...")
    await scout._enrich_violations_with_parcel_data(leads)
    
    lead = leads[0]
    print("\nEnrichment Results:")
    print("-" * 40)
    print(f"Parcel ID: {lead.get('parcel_id')}")
    print(f"Owner: {lead.get('owner_name')}")
    print(f"Seq Num: {lead.get('seq_num')}")
    print(f"Docket: {lead.get('docket')}")
    print(f"Page: {lead.get('page')}")
    print(f"Record Date: {lead.get('record_date')}")
    print(f"Last Sold Date: {lead.get('last_sold_date')}")
    
    # Verification
    if expected_seq:
        if lead.get("seq_num") == expected_seq:
            print(f"\nSUCCESS: Seq Num matched '{expected_seq}'")
        else:
            print(f"\nFAILURE: Expected '{expected_seq}', got '{lead.get('seq_num')}'")
    
    if expected_date:
        if lead.get("last_sold_date") == expected_date:
             print(f"SUCCESS: Date matched '{expected_date}'")
        else:
             print(f"FAILURE: Expected '{expected_date}', got '{lead.get('last_sold_date')}'")

if __name__ == "__main__":
    asyncio.run(test_enrichment())
