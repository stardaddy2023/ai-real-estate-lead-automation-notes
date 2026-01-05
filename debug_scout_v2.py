import asyncio
import os
import sys

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.services.pipeline.scout import ScoutService

async def test_search():
    print("Initializing ScoutService...")
    service = ScoutService()
    
    filters = {
        "zip_code": "85711",
        "distress_type": ["Code Violations"],
        "property_types": ["Single Family"],
        "limit": 10
    }
    
    print(f"Fetching leads with filters: {filters}")
    try:
        leads = await service.fetch_leads(filters)
        print(f"Successfully fetched {len(leads)} leads")
        if leads:
            print("Sample lead:", leads[0])
    except Exception as e:
        print(f"Error fetching leads: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_search())
