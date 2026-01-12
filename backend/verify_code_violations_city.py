import asyncio
import json
from app.services.pipeline.scout import ScoutService

async def verify_city_search(city_name):
    print(f"\nTesting Code Violation Search for City: {city_name}")
    service = ScoutService()
    
    # 1. Fetch Zips for City (to verify mapping)
    zips = await service._fetch_zips_by_city(city_name)
    print(f"Mapped {city_name} to Zips: {zips}")
    
    if not zips:
        print("FAILED: No zips found for city.")
        return

    # 2. Fetch Code Violations with City Filter
    filters = {
        "city": city_name,
        "primary": "Code Violations",
        "limit": 50
    }
    
    # Call fetch_leads to ensure enrichment happens
    print(f"Fetching code violations for {city_name}...")
    leads = await service.fetch_leads(filters)
    
    print(f"Found {len(leads)} violations.")
    
    if len(leads) > 0:
        print("Sample Lead Addresses:")
        for lead in leads[:5]:
            print(f" - {lead.get('address')} (Zip: {lead.get('address_zip')})")
            
        # Verify Zips
        match_count = 0
        for lead in leads:
            if str(lead.get('address_zip')) in zips:
                match_count += 1
        
        print(f"Leads matching city zips: {match_count}/{len(leads)}")
        if match_count > 0:
            print("SUCCESS: Found violations in correct zips.")
        else:
            print("WARNING: Violations found but zips do not match city zips.")
    else:
        print("WARNING: No violations found. This might be valid if there are none, or a bug.")

async def verify_zip_search(zip_code):
    print(f"\nTesting Code Violation Search for Zip: {zip_code}")
    service = ScoutService()
    filters = {"zip_code": zip_code, "primary": "Code Violations", "limit": 10}
    leads = await service.fetch_leads(filters)
    print(f"Found {len(leads)} violations in {zip_code}.")

async def main():
    await verify_city_search("VAIL")
    await verify_city_search("GREEN VALLEY")
    await verify_zip_search("85641") # Vail zip

if __name__ == "__main__":
    asyncio.run(main())
