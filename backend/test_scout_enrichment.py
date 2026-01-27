import asyncio
import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

from app.services.pipeline.scout import ScoutService

async def test_enrichment():
    print("Initializing ScoutService...")
    scout = ScoutService()
    
    # Create a dummy lead that needs enrichment
    # We use the parcel 106020300 which we know is missing sales price in GIS
    # and 131121240 which has sales price
    
    leads = [
        {
            "id": "test_lead_1",
            "address_street": "141 W ROGER RD",
            "latitude": 32.28186, # coords for 106020300
            "longitude": -110.97545,
            # Pre-fill parcel ID so it doesn't need to do spatial lookup if possible, 
            # but _enrich_violations_with_parcel_data does spatial lookup to find parcel attributes first.
            # So we need correct coords. 
            # Let's hope these coords are close enough for the spatial match.
            # actually _enrich_violations_with_parcel_data takes leads with lat/lon.
        },
        {
             "id": "test_lead_2",
             "address_street": "6242 E CALLE AURORA",
             "latitude": 32.19777, # coords for 131121240
             "longitude": -110.85857
        }
    ]
    
    print("\nRunning _enrich_violations_with_parcel_data...")
    # This will:
    # 1. Query GIS Layer 12 (Parcel) by lat/lon
    # 2. Populate attributes
    # 3. IF sales price missing, CALL our new _fetch_assessor_data (hidden API)
    
    await scout._enrich_violations_with_parcel_data(leads)
    
    print("\n--- RESULTS ---")
    for lead in leads:
        print(f"\nLead: {lead['address_street']}")
        print(f"Parcel ID: {lead.get('parcel_id')}")
        print(f"Owner: {lead.get('owner_name')}")
        print(f"Last Sale Price: {lead.get('last_sold_price')}")
        print(f"Last Sale Date: {lead.get('last_sold_date')}")
        
        # Verify
        if lead.get('parcel_id') == "106020300" and lead.get('last_sold_price') == 74000:
            print(">> VERIFIED: 106020300 found hidden price $74,000!")
        elif lead.get('parcel_id') == "131121240" and lead.get('last_sold_price') == 98900:
             print(">> VERIFIED: 131121240 found hidden price $98,900!")
        else:
             print(">> FAILED to find expected hidden price.")

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(test_enrichment())
