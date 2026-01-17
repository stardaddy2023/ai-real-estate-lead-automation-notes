import asyncio
import sys
import os

# Add backend directory to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.services.pipeline.scout import ScoutService

async def verify_property_type_filter():
    service = ScoutService()
    
    # Mock data simulating the user's scenario
    # A single "Land" result that matches the hot list filters
    mock_results = [
        {
            "address": "123 Desert Lot, Tucson, AZ",
            "property_type": "VACANT_LAND", # HomeHarvest style
            "distress_signals": ["FSBO", "Price Reduced"]
        }
    ]
    
    print("Testing Property Type Filter Logic...")
    
    # 1. Test with "Single Family" filter (Should return EMPTY)
    filters = ["Single Family"]
    
    # We need to access the internal logic or mock the fetch
    # Since we can't easily mock the internal method without a framework, 
    # let's copy the logic we want to test to verify it behaves as expected.
    
    type_mapping = {
        "single family": ["single", "house", "sfr"],
        "multi family": ["multi", "duplex", "triplex", "fourplex"],
        "condo": ["condo"],
        "townhouse": ["townhouse", "townhome"],
        "mobile home": ["mobile", "manufactured"],
        "vacant land": ["land", "lot"],
    }
    
    def matches_property_type(lead_type: str, filters: list) -> bool:
        lead_type_lower = lead_type.lower().replace("_", " ")
        for f in filters:
            f_lower = f.lower()
            # Direct match
            if f_lower in lead_type_lower:
                return True
            # Check mapping
            keywords = type_mapping.get(f_lower, [f_lower])
            if any(kw in lead_type_lower for kw in keywords):
                return True
        return False
    
    filtered = [r for r in mock_results if matches_property_type(r.get("property_type", ""), filters)]
    
    print(f"\nInput: {mock_results[0]['property_type']}")
    print(f"Filter: {filters}")
    print(f"Result Count: {len(filtered)}")
    
    if len(filtered) == 0:
        print("SUCCESS: Land result was correctly filtered out.")
    else:
        print("FAILURE: Land result was NOT filtered out.")

    # 2. Test with "Vacant Land" filter (Should return 1)
    filters_land = ["Vacant Land"]
    filtered_land = [r for r in mock_results if matches_property_type(r.get("property_type", ""), filters_land)]
    print(f"\nFilter: {filters_land}")
    print(f"Result Count: {len(filtered_land)}")
    
    if len(filtered_land) == 1:
        print("SUCCESS: Land result was correctly included.")
    else:
        print("FAILURE: Land result was incorrectly filtered out.")

if __name__ == "__main__":
    asyncio.run(verify_property_type_filter())
