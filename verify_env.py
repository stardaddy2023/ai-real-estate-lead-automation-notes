import sys
import asyncio
import os

print(f"Python Executable: {sys.executable}")
print(f"Python Version: {sys.version}")

# 1. Test Event Loop Policy
if sys.platform == "win32":
    print("Setting WindowsProactorEventLoopPolicy...")
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# 2. Test HomeHarvest Import
print("\nTesting HomeHarvest Import...")
try:
    import homeharvest
    print(f"SUCCESS: HomeHarvest imported. Version: {getattr(homeharvest, '__version__', 'unknown')}")
    print(f"Location: {os.path.dirname(homeharvest.__file__)}")
except ImportError as e:
    print(f"FAILURE: Could not import homeharvest: {e}")
except Exception as e:
    print(f"FAILURE: Error importing homeharvest: {e}")

# 3. Test Playwright (Simple Launch)
print("\nTesting Playwright Launch...")
async def test_playwright():
    try:
        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            print("Launching browser...")
            browser = await p.chromium.launch(headless=True)
            print("Browser launched successfully.")
            page = await browser.new_page()
            await page.goto("http://example.com")
            print("Navigated to example.com")
            await browser.close()
            print("SUCCESS: Playwright works.")
    except Exception as e:
        print(f"FAILURE: Playwright error: {e}")

if __name__ == "__main__":
    asyncio.run(test_playwright())
