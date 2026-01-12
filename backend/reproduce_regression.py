import asyncio
import json
import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

from app.services.pipeline.scout import ScoutService

async def reproduce_regression():
    service = ScoutService()
    
    # Test Case 1: Tucson Search
    print("\n--- Test Case 1: Tucson Search ---")
    filters_tucson = {
        "city": "Tucson",
        "distress_type": ["Code Violations", "Absentee Owner"],
        "property_type": ["Single Family"],
        "limit": 5
    }
    print(f"Filters: {filters_tucson}")
    try:
        leads_tucson = await service.fetch_leads(filters_tucson)
        print(f"Result Count: {len(leads_tucson)}")
        if leads_tucson:
            print(f"Sample Lead: {leads_tucson[0].get('address_street')}")
            print(f"Distress Signals: {leads_tucson[0].get('distress_signals')}")
    except Exception as e:
        print(f"Error: {e}")

    # Test Case 2: 85711 Search
    print("\n--- Test Case 2: 85711 Search ---")
    filters_zip = {
        "zip_code": "85711",
        "distress_type": ["Code Violations", "Absentee Owner"],
        "property_type": ["Single Family"],
        "limit": 5
    }
    print(f"Filters: {filters_zip}")
    try:
        leads_zip = await service.fetch_leads(filters_zip)
        print(f"Result Count: {len(leads_zip)}")
        if leads_zip:
            print(f"Sample Lead: {leads_zip[0].get('address_street')}")
            print(f"Distress Signals: {leads_zip[0].get('distress_signals')}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(reproduce_regression())
