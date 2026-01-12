"""Test Hot List fetch with mls_source"""
import asyncio
from app.services.pipeline.scout import ScoutService

async def test():
    service = ScoutService()
    results = await service.fetch_hot_leads("85716", ["New Listing"], 10)
    print(f"Found {len(results)} hot leads")
    if results:
        lead = results[0]
        print(f"Sample lead: {lead.get('address')}")
        print(f"MLS Source: {lead.get('mls_source')}")
        print(f"Distress signals: {lead.get('distress_signals')}")
    else:
        print("No results - check if homeharvest is returning data")

asyncio.run(test())
