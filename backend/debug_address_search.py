
import asyncio
import sys
import os
import json

# Add backend directory to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.services.pipeline.scout import ScoutService
from app.main import SearchFilters

async def debug_address_search():
    scout = ScoutService()
    # Use an address that likely triggered the issue (based on user report)
    # The user specified "927 N Perry"
    address = "927 N Perry"
    
    
    print(f"--- Debugging Address Search: {address} ---")
    
    filters = SearchFilters(
        address=address,
        limit=1
    )
    
    try:
        results = await scout.fetch_leads(filters.dict())
        print(f"\n--- Found {len(results)} Leads ---")
        
        if results:
            print("First Lead JSON:")
            print(json.dumps(results[0], indent=2, default=str))
        
        # Try to serialize to ensure no NaN values
        print("Serialization check:", json.dumps(results, default=str)[:100] + "...")
        
    except Exception as e:
        print(f"Search Failed: {e}")

if __name__ == "__main__":
    asyncio.run(debug_address_search())
