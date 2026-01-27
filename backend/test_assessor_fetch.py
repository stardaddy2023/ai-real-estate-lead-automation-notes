import asyncio
import sys
import os
import aiohttp

# Add current directory to path
sys.path.append(os.getcwd())

from app.services.pipeline.scout import ScoutService

async def test_fetcher():
    print("Testing _fetch_assessor_data direct call...")
    scout = ScoutService()
    
    parcels = ["106020300", "131121240"]
    
    async with aiohttp.ClientSession() as session:
        for p in parcels:
            print(f"\nFetching {p}...")
            data = await scout._fetch_assessor_data(session, p)
            print(f"Result: {data}")
            
            if p == "106020300" and data and data.get("price") == 74000:
                print(">> PASS: Found 74000")
            elif p == "131121240" and data and data.get("price") == 98900:
                print(">> PASS: Found 98900")
            else:
                print(">> FAIL or Different Data")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(test_fetcher())
