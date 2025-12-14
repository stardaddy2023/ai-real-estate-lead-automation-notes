import asyncio
import requests
from app.services.pipeline.scout import ScoutService

async def test_scout():
    scout = ScoutService()
    
    print("--- Testing Tucson Code Violations ---")
    filters_violations = {
        "distress_type": "code_violations",
        "limit": 5,
        "zip_code": "85719" # Test with a known zip
    }
    results = await scout.fetch_leads(filters_violations)
    print(f"Found {len(results)} violation leads")
    if results:
        print(f"Sample: {results[0]}")

    print("\n--- Testing Pima Parcels (Basic Connectivity) ---")
    # Test fetching ANY records to verify API works
    filters_basic = {
        "limit": 5
    }
    results = await scout.fetch_leads(filters_basic)
    print(f"Found {len(results)} basic leads")
    if results:
        print(f"Sample: {results[0]}")

    print("\n--- Testing Pima Parcels (Absentee with ZIP) ---")
    filters_absentee = {
        "distress_type": "absentee_owner",
        "limit": 5,
        "zip_code": "85719"
    }
    results = await scout.fetch_leads(filters_absentee)
    print(f"Found {len(results)} absentee leads")
    if results:
        print(f"Sample: {results[0]}")
    print("\n--- Finding Rich Tucson Lead (Sqft + Sale) ---")
    url_l4 = "https://gisdata.pima.gov/arcgis1/rest/services/GISOpenData/LandRecords/MapServer/4/query"
    params_l4 = {
        "where": "SQ_FT > 1000 AND SALE_DATE IS NOT NULL",
        "outFields": "TAX_CODE,SQ_FT,SALE_DATE,SALE_PRICE",
        "returnGeometry": "false",
        "resultRecordCount": 1,
        "f": "json"
    }
    resp_l4 = requests.get(url_l4, params=params_l4)
    data_l4 = resp_l4.json()
    
    if "features" in data_l4 and data_l4["features"]:
        valid_pid = data_l4["features"][0]["attributes"]["TAX_CODE"]
        print(f"Found Rich PID: {valid_pid}")
        print(f"Raw Attributes: {data_l4['features'][0]['attributes']}")
        
        lead_mock = {
            "parcel_id": valid_pid,
            "property_type": "OldCode",
            "sqft": None
        }
        print(f"Before enrichment: {lead_mock}")
        await scout._enrich_with_tucson_data([lead_mock])
        print(f"After enrichment: {lead_mock}")
    else:
        print("Could not find a rich lead.")

if __name__ == "__main__":
    asyncio.run(test_scout())
