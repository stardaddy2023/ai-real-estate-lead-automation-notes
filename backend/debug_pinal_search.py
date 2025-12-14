import asyncio
from app.services.pipeline.scout import ScoutService

async def debug_pinal():
    scout = ScoutService()
    
    print("--- Testing Pinal County Search ---")
    
    # 1. Generic Search
    filters = {
        "county": "Pinal",
        "limit": 5,
        "zip_code": "85122" # Casa Grande Zip
    }
    print(f"\n1. Generic Search: {filters}")
    leads = await scout.fetch_leads(filters)
    print(f"Found {len(leads)} leads")
    if leads:
        print(f"Sample: {leads[0]['address']} ({leads[0]['property_type']})")
        
    # 2. Absentee Search
    filters_abs = {
        "county": "Pinal",
        "limit": 5,
        "distress_type": "absentee_owner",
        "zip_code": "85122"
    }
    print(f"\n2. Absentee Search: {filters_abs}")
    leads_abs = await scout.fetch_leads(filters_abs)
    print(f"Found {len(leads_abs)} absentee leads")
    if leads_abs:
        print(f"Sample: {leads_abs[0]['address']} (Owner: {leads_abs[0]['owner_name']})")
        print(f"  Mailing: {leads_abs[0]['mailing_address']}")

if __name__ == "__main__":
    asyncio.run(debug_pinal())
