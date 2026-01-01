"""
Initialize browser profile by solving CAPTCHA manually.
Run this once to save cookies for future automated runs.
"""
import asyncio
from server import RecorderScraper


async def init_browser():
    print("=" * 50)
    print("BROWSER INITIALIZATION")
    print("=" * 50)
    print()
    print("A browser window will open.")
    print("1. Solve the reCAPTCHA")
    print("2. Click 'I Accept' to get to the search page")
    print("3. Once on the search page, press Enter in this terminal")
    print()
    
    async with RecorderScraper(headless=False) as scraper:
        # Navigate to the recorder page
        await scraper.page.goto("https://pimacountyaz-web.tylerhost.net/web/search/DOCSEARCH55S10")
        
        print("Browser opened. Solve the CAPTCHA and navigate to search page.")
        print()
        input(">>> Press Enter when you're on the search page: ")
        
        print()
        print("Cookies saved to browser_data/ folder.")
        print("Future runs will skip the CAPTCHA!")


if __name__ == "__main__":
    asyncio.run(init_browser())
