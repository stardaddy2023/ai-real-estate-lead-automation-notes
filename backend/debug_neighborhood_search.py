
import asyncio
import sys
import os

# Add backend directory to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.services.pipeline.scout import ScoutService

async def debug_neighborhood():
    scout = ScoutService()
    neighborhood_name = "Barrio Hollywood"
    
    print(f"--- Debugging Neighborhood: {neighborhood_name} ---")
    
    # 1. Resolve Bounds
    bounds = await scout._resolve_neighborhood_to_bounds(neighborhood_name)
    print(f"Resolved Bounds: {bounds}")
    
    if not bounds:
        print("Could not resolve bounds.")
        return

    # 2. Search Code Violations in Bounds
    print("\n--- Searching Code Violations in Bounds ---")
    # Manually constructing the query similar to scout.py
    # We need to see what raw results we get before enrichment
    
    # Actually, let's just use the public method but with debug prints in scout.py if needed.
    # But calling the internal methods is better for isolation.
    
    # We can't easily call _fetch_code_violations directly with just bounds if it expects a filter object
    # Let's try to simulate what search_leads does.
    
    from app.main import SearchFilters
    filters = SearchFilters(
        neighborhood=neighborhood_name,
        limit=5
    )
    
    # We can call fetch_leads directly
    results = await scout.fetch_leads(filters)
    
    print(f"\n--- Found {len(results)} Leads ---")
    for i, lead in enumerate(results):
        print(f"[{i+1}] {lead.get('address')}")
        print(f"    Neighborhood: {lead.get('neighborhoods')}")
        print(f"    APN: {lead.get('parcel_id')}")
        print(f"    Zip: {lead.get('address_zip')}")
        print(f"    Source: {lead.get('source')}")

if __name__ == "__main__":
    asyncio.run(debug_neighborhood())
