"""
Quick test to verify cookies work - runs non-headless to debug.
"""
import asyncio
from server import RecorderScraper


async def test_cookies():
    print("Testing with saved cookies (non-headless)...")
    
    async with RecorderScraper(headless=False) as scraper:
        result = await scraper.navigate_to_search()
        if result:
            print("SUCCESS: Cookies worked! On search page.")
            input("Press Enter to close...")
        else:
            print("FAILED: Cookies didn't work or CAPTCHA appeared again.")
            input("Check browser and press Enter to close...")


if __name__ == "__main__":
    asyncio.run(test_cookies())
