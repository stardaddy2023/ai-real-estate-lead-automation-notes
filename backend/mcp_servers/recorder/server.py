"""
Pima County Recorder MCP Server
Enables AI agents to search for recorded documents (liens, judgments, etc.)
"""
from fastmcp import FastMCP
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
import asyncio
import os
from typing import Optional, List, Dict
from dotenv import load_dotenv

load_dotenv()

# Initialize FastMCP
mcp = FastMCP("recorder")

# Document type mapping: distress filter -> recorder search terms
DOC_TYPE_MAP = {
    "Pre-Foreclosure": ["NOTICE OF TRUSTEE SALE", "SUBSTITUTION OF TRUSTEE"],
    "Liens (HOA)": ["HOA LIEN", "ASSESSMENT LIEN"],
    "Liens (Mechanics)": ["MECHANICS LIEN", "LIEN"],
    "Tax Liens": ["TAX LIEN", "CERTIFICATE OF PURCHASE"],
    "Judgments": ["JUDGMENT", "ABSTRACT JUDGMENT"],
    "Divorce": ["DECREE OF DIVORCE", "DISSOLUTION"],
    "Probate": ["AFFIDAVIT OF SUCCESSION", "PERSONAL REPRESENTATIVE DEED"],
}

# Recorder portal URL
RECORDER_URL = "https://pimacountyaz-web.tylerhost.net/web/search/DOCSEARCH55S10"

# Path for persistent browser data (stores cookies after CAPTCHA solve)
BROWSER_DATA_DIR = os.path.join(os.path.dirname(__file__), "browser_data")


class RecorderScraper:
    """
    Handles browser automation for Pima County Recorder portal.
    Uses persistent browser context to store cookies after manual CAPTCHA solve.
    """
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.browser = None
        self.context = None
        self.page = None
    
    async def __aenter__(self):
        self.playwright = await async_playwright().start()
        
        # Use persistent context to store cookies between sessions
        # First run: user solves CAPTCHA manually
        # Future runs: cookies are reused
        self.context = await self.playwright.chromium.launch_persistent_context(
            BROWSER_DATA_DIR,
            headless=self.headless,
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-first-run",
                "--no-default-browser-check",
            ]
        )
        
        # Use existing page or create new one
        if self.context.pages:
            self.page = self.context.pages[0]
        else:
            self.page = await self.context.new_page()
        
        # Apply stealth to mask Playwright automation fingerprint
        try:
            from playwright_stealth import Stealth
            async with Stealth(self.page):
                pass  # Stealth is applied as context manager
        except ImportError:
            print("Warning: playwright-stealth not installed, bot detection may occur")
        except Exception as e:
            print(f"Stealth setup warning: {e}")
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.context:
            await self.context.close()
        if self.playwright:
            await self.playwright.stop()
    
    async def navigate_to_search(self) -> bool:
        """Navigate to search page and handle disclaimer if present."""
        try:
            await self.page.goto(RECORDER_URL, timeout=30000)
            await self.page.wait_for_load_state("domcontentloaded")
            
            # Check if we're on disclaimer page (URL contains 'disclaimer' or 'user')
            current_url = self.page.url
            if 'disclaimer' in current_url.lower() or '/user' in current_url.lower():
                print("Disclaimer page detected, attempting to accept...")
                
                # First, scroll to the bottom of the page (some sites require this)
                await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await self.page.wait_for_timeout(1000)
                
                # Wait a bit for any JavaScript to enable the button
                await self.page.wait_for_timeout(2000)
                
                # Try to find and click the accept button using JavaScript
                clicked = await self.page.evaluate("""
                    () => {
                        // Look for buttons with "Accept" text
                        const buttons = document.querySelectorAll('button, input[type="submit"]');
                        for (const btn of buttons) {
                            const text = btn.innerText || btn.value || '';
                            if (text.toLowerCase().includes('accept')) {
                                btn.click();
                                return true;
                            }
                        }
                        return false;
                    }
                """)
                
                if clicked:
                    print("Clicked accept button via JavaScript")
                    await self.page.wait_for_load_state("networkidle")
                else:
                    # Fallback: try playwright locators
                    accept_selectors = [
                        "button:has-text('I Accept')",
                        "input[type='submit'][value*='Accept']",
                        "button:has-text('Accept')",
                    ]
                    for selector in accept_selectors:
                        try:
                            btn = self.page.locator(selector)
                            if await btn.count() > 0:
                                await btn.first.click(force=True, timeout=5000)
                                print(f"Clicked accept button: {selector}")
                                await self.page.wait_for_load_state("networkidle")
                                break
                        except Exception:
                            continue
            
            # Wait for the search page to load
            await self.page.wait_for_timeout(2000)
            
            # Verify we're on search page by checking for Document Types input
            doc_types_input = self.page.locator("#field_selfservice_documentTypes")
            await doc_types_input.wait_for(timeout=15000)
            print("Successfully on search page")
            return True
            
        except Exception as e:
            print(f"Navigation error: {e}")
            # Take screenshot for debugging
            try:
                await self.page.screenshot(path="debug_navigation_error.png")
            except:
                pass
            return False
    
    async def search_by_doc_type(self, doc_type: str, limit: int = 50) -> List[Dict]:
        """
        Search for documents by document type.
        Returns list of document records.
        """
        results = []
        
        try:
            # Type document type into the autocomplete field
            doc_input = self.page.locator("#field_selfservice_documentTypes")
            await doc_input.fill(doc_type)
            
            # Wait for autocomplete suggestions
            await self.page.wait_for_timeout(1000)
            
            # Click the first matching suggestion
            suggestion = self.page.locator(f"text='{doc_type}'").first
            try:
                await suggestion.click(timeout=3000)
            except PlaywrightTimeout:
                # Try typing and pressing Enter instead
                await doc_input.press("Enter")
            
            # Click the Search button (use ID selector)
            search_btn = self.page.locator("#searchButton")
            await search_btn.click()
            
            # Wait for results to load
            await self.page.wait_for_load_state("networkidle")
            await self.page.wait_for_timeout(2000)
            
            # Check if results table exists
            results_table = self.page.locator("table.results-table, .search-results table")
            
            try:
                await results_table.wait_for(timeout=10000)
                
                # Parse the results table
                rows = await self.page.locator("table tbody tr").all()
                
                for row in rows[:limit]:
                    try:
                        cells = await row.locator("td").all()
                        if len(cells) >= 4:
                            record = {
                                "doc_number": await cells[0].inner_text(),
                                "doc_type": await cells[1].inner_text() if len(cells) > 1 else doc_type,
                                "record_date": await cells[2].inner_text() if len(cells) > 2 else "",
                                "parties": await cells[3].inner_text() if len(cells) > 3 else "",
                            }
                            results.append(record)
                    except Exception:
                        continue
                        
            except PlaywrightTimeout:
                # No results found
                pass
                
        except Exception as e:
            print(f"Search error: {e}")
        
        return results
    
    async def clear_search(self):
        """Clear the search form."""
        try:
            clear_btn = self.page.locator("#clearSearchButton")
            await clear_btn.click()
            await self.page.wait_for_timeout(500)
        except Exception:
            pass


@mcp.tool()
async def search_documents(
    doc_type: str = None,
    distress_filter: str = None,
    limit: int = 50
) -> list:
    """
    Search for documents in Pima County Recorder.
    
    Args:
        doc_type: Specific document type (e.g., "NOTICE OF TRUSTEE SALE", "MECHANICS LIEN")
        distress_filter: Friendly filter name (e.g., "Pre-Foreclosure", "Liens (HOA)")
        limit: Maximum results to return (default 50)
    
    Returns:
        List of document records with doc_number, doc_type, record_date, parties
    """
    all_results = []
    
    # Determine which document types to search
    search_types = []
    if doc_type:
        search_types = [doc_type]
    elif distress_filter and distress_filter in DOC_TYPE_MAP:
        search_types = DOC_TYPE_MAP[distress_filter]
    else:
        return [{"error": "Must specify doc_type or valid distress_filter"}]
    
    async with RecorderScraper(headless=True) as scraper:
        if not await scraper.navigate_to_search():
            return [{"error": "Failed to navigate to search page"}]
        
        for doc_type_search in search_types:
            results = await scraper.search_by_doc_type(doc_type_search, limit)
            all_results.extend(results)
            await scraper.clear_search()
            
            if len(all_results) >= limit:
                break
    
    return all_results[:limit]


@mcp.tool()
async def get_document_details(doc_number: str) -> dict:
    """
    Get detailed information for a specific document.
    
    Args:
        doc_number: The document number (e.g., "2024-1234567")
    
    Returns:
        Document details including amount, legal description, parties
    """
    async with RecorderScraper(headless=True) as scraper:
        if not await scraper.navigate_to_search():
            return {"error": "Failed to navigate to search page"}
        
        try:
            # Search by document number
            doc_input = scraper.page.locator("#field_selfservice_documentNumber")
            await doc_input.fill(doc_number)
            
            search_btn = scraper.page.locator("button:has-text('Search')")
            await search_btn.click()
            
            await scraper.page.wait_for_load_state("networkidle")
            await scraper.page.wait_for_timeout(2000)
            
            # Click on the result to get details
            result_link = scraper.page.locator(f"a:has-text('{doc_number}')").first
            await result_link.click()
            
            await scraper.page.wait_for_load_state("networkidle")
            
            # Parse detail page
            details = {
                "doc_number": doc_number,
                "amount": None,
                "legal_description": None,
                "grantor": None,
                "grantee": None,
            }
            
            # Try to extract common fields
            try:
                amount_el = scraper.page.locator("text=Amount").locator("xpath=following-sibling::*")
                details["amount"] = await amount_el.inner_text()
            except Exception:
                pass
            
            try:
                legal_el = scraper.page.locator("text='Legal'").locator("xpath=following-sibling::*")
                details["legal_description"] = await legal_el.inner_text()
            except Exception:
                pass
            
            return details
            
        except Exception as e:
            return {"error": str(e), "doc_number": doc_number}


if __name__ == "__main__":
    mcp.run()
