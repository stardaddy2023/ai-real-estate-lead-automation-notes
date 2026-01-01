"""
Test client for Recorder MCP Server.
Tests the scraper directly without MCP wrapper.
"""
import asyncio
import sys
sys.path.insert(0, '.')

# Import the internal components directly
from server import RecorderScraper, DOC_TYPE_MAP


async def test_search():
    """Test the RecorderScraper directly."""
    print("=" * 50)
    print("Testing Recorder MCP Server")
    print("=" * 50)
    
    async with RecorderScraper(headless=False) as scraper:  # headless=False to see what's happening
        print("\n1. Navigating to search page...")
        success = await scraper.navigate_to_search()
        if not success:
            print("   FAILED: Could not navigate to search page")
            return
        print("   SUCCESS: On search page")
        
        # Test 2: Search for NOTICE OF TRUSTEE SALE
        print("\n2. Testing NOTICE OF TRUSTEE SALE search...")
        results = await scraper.search_by_doc_type("NOTICE OF TRUSTEE SALE", limit=5)
        print(f"   Found {len(results)} results")
        for r in results[:3]:
            print(f"   - {r}")
        
        await scraper.clear_search()
        
        # Test 3: Search for MECHANICS LIEN
        print("\n3. Testing MECHANICS LIEN search...")
        results = await scraper.search_by_doc_type("MECHANICS LIEN", limit=5)
        print(f"   Found {len(results)} results")
        for r in results[:3]:
            print(f"   - {r}")
    
    print("\n" + "=" * 50)
    print("Test complete!")


if __name__ == "__main__":
    asyncio.run(test_search())
