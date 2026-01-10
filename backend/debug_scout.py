import asyncio
import json
import sys
import os

# Add backend to path
sys.path.append(os.getcwd())

from app.services.pipeline.scout import ScoutService

async def debug_enrichment():
    print("--- Debugging ScoutService Enrichment ---")
    scout = ScoutService()
    
    # Search for a specific address that should exist
    filters = {
        "address": "2538 E 3RD ST", 
        "limit": 1
    }
    
    print(f"Fetching leads with filters: {filters}")
    leads = await scout.fetch_leads(filters)
    
    print(f"\nFound {len(leads)} leads.")
    if leads:
        lead = leads[0]
        print("\n--- Enriched Lead Data ---")
        print(f"Address: {lead.get('address_street')}")
        print(f"APN (parcel_id): {lead.get('parcel_id')}")
        print(f"Property Type: {lead.get('property_type')}")
        print(f"Lot Size: {lead.get('lot_size')}")
        print(f"Assessed Value: {lead.get('assessed_value')}")
        print(f"Zoning: {lead.get('zoning')}")
        print(f"Neighborhoods: {lead.get('neighborhoods')}")

if __name__ == "__main__":
    asyncio.run(debug_enrichment())
