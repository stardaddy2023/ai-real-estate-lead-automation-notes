import asyncio
from app.services.pipeline.scout import ScoutService

async def debug_pagination():
    scout = ScoutService()
    
    # User's scenario
    filters = {
        "distress_type": "absentee_owner",
        "limit": 500,
        "zip_code": "85713",
        "property_types": []
    }
    
    print(f"--- Debugging Pagination for {filters} ---")
    results = await scout.fetch_leads(filters)
    print(f"Requested: {filters['limit']}")
    print(f"Returned: {len(results)}")
    
    if len(results) == 427:
        print("FAIL: Still returning 427 leads (Old behavior reproduced)")
    elif len(results) >= 500:
        print("SUCCESS: Returned requested amount")
    else:
        print(f"PARTIAL: Returned {len(results)} leads")

if __name__ == "__main__":
    asyncio.run(debug_pagination())
