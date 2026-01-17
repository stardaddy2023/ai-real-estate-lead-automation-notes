import asyncio
import sys
import os

# Add backend directory to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.services.pipeline.scout import ScoutService

async def debug_price_reduced():
    service = ScoutService()
    location = "Tucson, AZ"
    
    print(f"Fetching Price Reduced leads for {location}...")
    print(f"Fetching Price Reduced leads for {location}...")
    leads = await service.fetch_hot_leads(location, ["Price Reduced"], limit=20)
    
    print(f"\nFound {len(leads)} leads.")
    
    for i, lead in enumerate(leads):
        print(f"\n--- Lead {i+1} ---")
        print(f"Address: {lead.get('address')}")
        print(f"Price: {lead.get('list_price')}")
        print(f"Status: {lead.get('status')}")
        print(f"MLS Source: {lead.get('mls_source')}")
        print(f"Distress: {lead.get('distress_signals')}")
        print(f"Description: {lead.get('listing_description')[:100]}..." if lead.get('listing_description') else "No description")
        
        # Check for missing critical data
        if not lead.get('address') or lead.get('address') == "None, None, AZ ":
            print("WARNING: Invalid Address!")

if __name__ == "__main__":
    asyncio.run(debug_price_reduced())
