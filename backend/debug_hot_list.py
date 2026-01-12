"""Debug the full hot list flow to see what's happening"""
import asyncio
from app.services.pipeline.scout import ScoutService

async def test():
    service = ScoutService()
    
    # Simulate what the frontend sends
    filters = {
        "zip_code": "85716",
        "hot_list": ["New Listing"],
        "property_types": ["Single Family"],
        "distress_type": [],
        "limit": 10
    }
    
    print(f"Filters: {filters}")
    print("=" * 60)
    
    # Call fetch_leads which is what the API calls
    results = await service.fetch_leads(filters)
    
    print(f"\nGot {len(results)} results")
    
    if results:
        for i, lead in enumerate(results[:3]):
            print(f"\n--- Result {i+1} ---")
            print(f"  Address: {lead.get('address')}")
            print(f"  Source: {lead.get('source')}")
            print(f"  MLS Source: {lead.get('mls_source')}")
            print(f"  Status: {lead.get('status')}")
            print(f"  Distress: {lead.get('distress_signals')}")
            print(f"  Description: {str(lead.get('listing_description', ''))[:50]}...")

asyncio.run(test())
