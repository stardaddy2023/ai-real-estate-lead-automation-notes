import asyncio
import pandas as pd
from homeharvest import scrape_property

async def test_homeharvest():
    address = "2538 E 3RD ST, TUCSON, AZ 85716"
    print(f"Testing HomeHarvest for: {address}")
    
    providers = ["realtor.com", "redfin", "zillow"]
    
    for site in providers:
        print(f"\n--- Testing {site} ---")
        try:
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(
                None, 
                lambda: scrape_property(
                    location=address,
                    listing_type="sold", # Try sold first as it's most common for details
                    past_days=3650 # Go back far enough
                )
            )
            
            if not df.empty:
                print(f"SUCCESS: Found {len(df)} records.")
                data = df.iloc[0].to_dict()
                print(f"Beds: {data.get('beds')}, Baths: {data.get('full_baths')}, Sqft: {data.get('sqft')}")
                print(f"Year Built: {data.get('year_built')}")
            else:
                print("FAILURE: No records found.")
                
        except Exception as e:
            print(f"ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(test_homeharvest())
