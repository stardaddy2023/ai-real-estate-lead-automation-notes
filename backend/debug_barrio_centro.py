
import asyncio
import sys
import os

# Add backend directory to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.services.pipeline.scout import ScoutService
from app.main import SearchFilters

async def debug_barrio_centro():
    scout = ScoutService()
    neighborhood_name = "Barrio Centro"
    
    print(f"--- Debugging Neighborhood: {neighborhood_name} ---")
    
    # 1. Resolve Bounds
    bounds = await scout._resolve_neighborhood_to_bounds(neighborhood_name)
    print(f"Resolved Bounds: {bounds}")
    
    if not bounds:
        print("Could not resolve bounds.")
        return

    # 2. Search Code Violations in Bounds
    print("\n--- Searching Code Violations in Bounds ---")
    filters = SearchFilters(
        neighborhood=neighborhood_name,
        distress_type=["Code Violations"],
        limit=10
    )
    
    results = await scout.fetch_leads(filters.dict())
    
    print(f"\n--- Found {len(results)} Leads ---")
    for i, lead in enumerate(results):
        print(f"[{i+1}] {lead.get('address')}")
        print(f"    Neighborhood: {lead.get('neighborhoods')}")
        print(f"    APN: {lead.get('parcel_id')}")
        print(f"    Coords: {lead.get('latitude')}, {lead.get('longitude')}")

if __name__ == "__main__":
    asyncio.run(debug_barrio_centro())
