import asyncio
from app.services.pipeline.scout import ScoutService
from app.services.pipeline.cleaner import CleanerService

async def debug_attrition():
    scout = ScoutService()
    cleaner = CleanerService()
    
    # Use the user's exact scenario
    filters = {
        "zip_code": "85713",
        "limit": 500,
        "distress_type": "all", # Implies _fetch_parcels
        "property_types": []
    }
    
    print(f"--- Debugging Attrition for {filters} ---")
    
    # 1. Fetch Raw
    raw_leads = await scout.fetch_leads(filters)
    print(f"Raw Leads Fetched: {len(raw_leads)}")
    
    # 2. Clean
    cleaned_leads = cleaner.clean_leads(raw_leads)
    print(f"Cleaned Leads: {len(cleaned_leads)}")
    
    attrition = len(raw_leads) - len(cleaned_leads)
    print(f"Attrition: {attrition} leads dropped")
    
    if len(cleaned_leads) < 500:
        print("FAIL: Final count is less than requested limit due to cleaning.")
    else:
        print("SUCCESS: Final count meets limit.")

if __name__ == "__main__":
    asyncio.run(debug_attrition())
