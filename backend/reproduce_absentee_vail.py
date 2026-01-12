import asyncio
from app.services.pipeline.scout import ScoutService

async def reproduce_absentee():
    service = ScoutService()
    
    # Test 1: Vail (Absentee Owner)
    print("\n--- Testing Vail Absentee Owner ---")
    filters_vail = {
        "city": "Vail",
        "primary": "Absentee Owner",
        "limit": 20
    }
    # fetch_leads calls _fetch_absentee_owners -> _fetch_pima_parcels
    leads_vail = await service.fetch_leads(filters_vail)
    print(f"Found {len(leads_vail)} leads for Vail.")
    for lead in leads_vail[:10]:
        print(f"  - {lead.get('address')} (Zip: {lead.get('address_zip')})")

    # Test 2: Green Valley (Absentee Owner)
    print("\n--- Testing Green Valley Absentee Owner ---")
    filters_gv = {
        "city": "Green Valley",
        "primary": "Absentee Owner",
        "limit": 20
    }
    leads_gv = await service.fetch_leads(filters_gv)
    print(f"Found {len(leads_gv)} leads for Green Valley.")
    for lead in leads_gv[:10]:
        print(f"  - {lead.get('address')} (Zip: {lead.get('address_zip')})")

if __name__ == "__main__":
    asyncio.run(reproduce_absentee())
