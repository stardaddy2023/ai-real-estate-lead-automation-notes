
import asyncio
from playwright.async_api import async_playwright

async def scrape_assessor():
    parcel_id = "121-01-2560"
    url = f"https://asr.pima.gov/parcel-details?parcel={parcel_id}"
    print(f"Navigating to {url}...")
    
    async with async_playwright() as p:
        # Use a real user agent to avoid 403
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        try:
            await page.goto(url, timeout=60000)
            
            # Wait for text that indicates data loaded
            # "2177" is the value we are looking for.
            # Let's look for "Square Feet" or similar labels.
            # Inspecting the page visually (mental model), it usually has a table.
            
            # Wait for body to be populated
            await page.wait_for_selector("body", timeout=30000)
            
            # Get full text
            content = await page.content()
            text = await page.inner_text("body")
            
            print("\n--- Page Text Sample ---")
            print(text[:500])
            
            # Search for 2177
            if "2177" in text:
                print("\nSUCCESS: Found '2177' in page text!")
            else:
                print("\nFAILURE: '2177' not found in page text.")
                
            # Try to find specific label for SqFt
            # Common labels: "Living Area", "Square Feet", "S.F."
            # We can try to find the element containing 2177 and print its context
            if "2177" in text:
                # Simple check
                pass
                
        except Exception as e:
            print(f"Error: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(scrape_assessor())
