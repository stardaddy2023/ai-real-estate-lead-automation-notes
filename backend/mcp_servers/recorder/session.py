"""
Recorder Session Manager
Uses Playwright for browser automation with manual CAPTCHA solving.
Supports document search, PDF download, and Gemini Vision extraction.

Configuration:
  Environment variables (can be set in .env or system environment):
    - GOOGLE_CLOUD_PROJECT: GCP project ID (default: arela-project)
    - GOOGLE_APPLICATION_CREDENTIALS: Path to GCP service account JSON
    - VERTEX_AI_LOCATION: Vertex AI region (default: us-central1)
  
  File locations:
    - .env file: backend/.env (auto-loaded)
    - credentials.json: backend/credentials.json (auto-detected if env not set)
"""
import asyncio
import os
import base64
from pathlib import Path
from typing import Optional, List, Dict
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import httpx
from dotenv import load_dotenv

# Determine paths relative to this file for portability
SCRIPT_DIR = Path(__file__).parent.resolve()
BACKEND_DIR = SCRIPT_DIR.parent.parent  # backend/mcp_servers/recorder -> backend

# Load .env from backend folder if it exists
env_path = BACKEND_DIR / ".env"
if env_path.exists():
    load_dotenv(env_path)

# Set GCP credentials - ensure absolute path
creds_env = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
if creds_env:
    # If relative path, resolve relative to backend dir
    creds_path = Path(creds_env)
    if not creds_path.is_absolute():
        creds_path = (BACKEND_DIR / creds_env).resolve()
    if creds_path.exists():
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(creds_path)
else:
    # Try common locations for credentials file
    credentials_locations = [
        BACKEND_DIR / "credentials.json",                    # backend/credentials.json
        SCRIPT_DIR / "credentials.json",                     # recorder/credentials.json
        Path.home() / ".config" / "gcloud" / "application_default_credentials.json",  # gcloud default
    ]
    for cred_path in credentials_locations:
        if cred_path.exists():
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(cred_path.resolve())
            break


# Document type mapping: distress filter -> recorder search terms
DOC_TYPE_MAP = {
    "Pre-Foreclosure": ["LIS PENDENS", "NOTICE SALE", "SUBSTITUTION TRUSTEE"],
    "Liens (Federal)": ["FEDERAL LIEN"],
    "Liens (Mechanics)": ["MECHANICS LIEN", "LIEN"],
    "Liens (Notice)": ["NOTICE LIEN"],
    "Judgments": ["JUDGMENT", "ABSTRACT JUDGMENT"],
    "Divorce": ["DISSOLUTION MARRIAGE"],
    "Probate": ["AFFIDAVIT SUCCESSION"],
}

RECORDER_URL = "https://pimacountyaz-web.tylerhost.net/web/search/DOCSEARCH55S10"

# Cookie file location for persistent sessions
COOKIES_FILE = BACKEND_DIR / "cache" / "recorder_cookies.json"
import json


class RecorderSession:
    """
    Manages a single recorder browser session with cookie persistence.
    - First tries to use saved cookies (headless, instant)
    - Falls back to manual CAPTCHA if cookies expired
    - Saves cookies after successful authentication
    """
    
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.page = None
        self.context = None
        self.initialized = False
        self._headless_mode = False  # Track if we're in headless mode
    
    def _load_cookies(self) -> list:
        """Load cookies from file if they exist."""
        if COOKIES_FILE.exists():
            try:
                with open(COOKIES_FILE, "r") as f:
                    cookies = json.load(f)
                print(f"Loaded {len(cookies)} cookies from cache", flush=True)
                return cookies
            except Exception as e:
                print(f"Failed to load cookies: {e}", flush=True)
        return []
    
    def _save_cookies(self, cookies: list):
        """Save cookies to file for future sessions."""
        try:
            COOKIES_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(COOKIES_FILE, "w") as f:
                json.dump(cookies, f, indent=2)
            print(f"Saved {len(cookies)} cookies to cache", flush=True)
        except Exception as e:
            print(f"Failed to save cookies: {e}", flush=True)
    
    def get_cookies_status(self) -> dict:
        """Get status of saved cookies."""
        if not COOKIES_FILE.exists():
            return {"exists": False, "age_hours": None, "count": 0}
        
        import time
        try:
            mtime = COOKIES_FILE.stat().st_mtime
            age_hours = (time.time() - mtime) / 3600
            with open(COOKIES_FILE, "r") as f:
                cookies = json.load(f)
            return {
                "exists": True,
                "age_hours": round(age_hours, 1),
                "count": len(cookies),
                "file_path": str(COOKIES_FILE)
            }
        except Exception as e:
            return {"exists": False, "error": str(e)}
    
    async def validate_session(self) -> bool:
        """Check if the browser session is still valid."""
        if not self.initialized:
            return False
            
        if not self.page or not self.browser:
            self.initialized = False
            return False
            
        try:
            # Check if page is still open and connected
            if self.page.is_closed():
                print("Session validation failed: Page is closed")
                self.initialized = False
                return False
                
            # Optional: Check if browser is connected
            if not self.browser.is_connected():
                print("Session validation failed: Browser is disconnected")
                self.initialized = False
                return False
                
            # ACTIVE CHECK: Try to evaluate simple JS to ensure page is responsive
            # This catches cases where the page is technically "open" but crashed or disconnected
            await self.page.evaluate("1")
                
            return True
        except Exception as e:
            print(f"Session validation error: {e}")
            self.initialized = False
            return False
    
    async def _create_browser_context(self, headless: bool = True):
        """Create browser and context with stealth settings."""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-first-run",
                "--no-default-browser-check",
            ]
        )
        
        # Create context with realistic settings
        self.context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="en-US",
            timezone_id="America/Phoenix",
        )
        
        self.page = await self.context.new_page()
        
        # Apply playwright-stealth to hide automation markers (v2.0.0 API)
        stealth = Stealth()
        await stealth.apply_stealth_async(self.page)
        
        # Additional JavaScript evasion patches
        await self.page.add_init_script("""
            // Override webdriver property
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            // Override plugins to look more realistic
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            
            // Override languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
            
            // Override chrome property
            window.chrome = {
                runtime: {}
            };
        """)
        
        self._headless_mode = headless
    
    async def _verify_search_page(self, timeout: int = 5000) -> bool:
        """Check if we're on the search page (past CAPTCHA)."""
        try:
            doc_input = self.page.locator("#field_selfservice_documentTypes")
            await doc_input.wait_for(timeout=timeout)
            return True
        except:
            return False
    
    async def initialize(self, force_manual: bool = False):
        """
        Initialize the recorder session.
        
        Flow:
        1. If not forcing manual, try headless with saved cookies
        2. If cookies work -> instant session (no browser window)
        3. If cookies fail -> open browser for manual CAPTCHA
        4. After manual CAPTCHA -> save cookies for next time
        """
        if self.initialized:
            print("Session already initialized")
            return True
        
        saved_cookies = self._load_cookies()
        
        # Try headless with cookies first (unless forcing manual)
        if saved_cookies and not force_manual:
            print("=" * 50)
            print("RECORDER SESSION - TRYING CACHED COOKIES")
            print("=" * 50)
            
            await self._create_browser_context(headless=True)
            
            # Inject saved cookies
            await self.context.add_cookies(saved_cookies)
            
            # Navigate and check if we bypass CAPTCHA
            print(f"Navigating to {RECORDER_URL}...", flush=True)
            await self.page.goto(RECORDER_URL)
            
            # Give it a moment, then check if we're on search page
            await self.page.wait_for_timeout(2000)
            
            if await self._verify_search_page(timeout=5000):
                self.initialized = True
                print("✓ Cookies valid! Session ready (headless mode).", flush=True)
                return True
            else:
                print("✗ Cookies expired or invalid. Closing headless browser...", flush=True)
                await self.close()
        
        # Manual CAPTCHA flow
        print("=" * 50)
        print("RECORDER SESSION - MANUAL CAPTCHA REQUIRED")
        print("=" * 50)
        print()
        print("Opening browser for CAPTCHA solving...")
        
        await self._create_browser_context(headless=False)
        
        # Navigate to recorder page
        print(f"Navigating to {RECORDER_URL}...", flush=True)
        await self.page.goto(RECORDER_URL)
        
        print("Browser opened. Please:", flush=True)
        print("  1. Solve the reCAPTCHA checkbox", flush=True)
        print("  2. Click 'I Accept' to get to the search page", flush=True)
        
        print("Waiting for user to solve CAPTCHA and reach search page...", flush=True)
        
        # Wait for user to complete CAPTCHA (up to 120 seconds)
        if await self._verify_search_page(timeout=120000):
            # Save cookies for next time!
            cookies = await self.context.cookies()
            self._save_cookies(cookies)
            
            self.initialized = True
            print("✓ Session initialized! Cookies saved for future sessions.", flush=True)
            return True
        else:
            print("✗ Could not verify search page. CAPTCHA may not have been solved.", flush=True)
            return False
    
    async def refresh_cookies(self):
        """Force a manual CAPTCHA flow to get fresh cookies."""
        print("Forcing cookie refresh...", flush=True)
        await self.close()
        return await self.initialize(force_manual=True)
    
    async def search_by_doc_type(self, doc_type: str, days_back: int = 30, limit: int = 50) -> List[Dict]:
        """Search for documents by document type with date range."""
        if not self.initialized or not await self.validate_session():
            return [{"error": "Session not initialized or browser closed. Please re-initialize."}]
        
        results = []
        
        # Calculate date range (past N days)
        from datetime import datetime, timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        start_str = start_date.strftime("%m/%d/%Y")
        end_str = end_date.strftime("%m/%d/%Y")
        
        import sys  # Import sys for flush
        
        try:
            # Check if there are existing document type selections that need clearing
            # Tyler Tech stores selections as li.cblist-input-list.transition-background
            has_existing_selection = await self.page.evaluate("""(() => {
                const holder = document.querySelector('#field_selfservice_documentTypes-holder');
                if (holder) {
                    return holder.querySelectorAll('li.cblist-input-list.transition-background').length > 0;
                }
                return false;
            })()""")
            
            if has_existing_selection:
                # Use the native Clear Selections button which properly resets form state
                # This triggers an AJAX call and page reload
                print("    Previous selection found, clearing via native button...", flush=True)
                clear_btn = self.page.locator("#clearSearchButton")
                if await clear_btn.is_visible(timeout=2000):
                    await clear_btn.click()
                    # Wait for the page to reload (the button triggers location.reload())
                    await self.page.wait_for_load_state("networkidle")
                    await self.page.wait_for_timeout(1000)
                    print("    Form cleared via native button", flush=True)
            
            # Fill Recording Date Start using the specific ID
            try:
                start_input = self.page.locator("#field_RecordingDateID_DOT_StartDate")
                await start_input.fill(start_str)
                print(f"    Filled start date: {start_str}", flush=True)
            except Exception as e:
                print(f"    ERROR filling start date: {e}", flush=True)
            
            # Fill Recording Date End
            try:
                end_input = self.page.locator("#field_RecordingDateID_DOT_EndDate")
                await end_input.fill(end_str)
                print(f"    Filled end date: {end_str}", flush=True)
            except Exception as e:
                print(f"    ERROR filling end date: {e}", flush=True)
            
            await self.page.wait_for_timeout(500)
            
            # Type document type into autocomplete
            try:
                doc_input = self.page.locator("#field_selfservice_documentTypes")
                await doc_input.click()
                # Clear any existing text first
                await doc_input.fill("")
                await self.page.wait_for_timeout(300)
                # Type the document type slowly (like a human)
                await doc_input.type(doc_type, delay=50)
                print(f"    Typed doc type: {doc_type}", flush=True)
                await self.page.wait_for_timeout(2000)  # Wait for autocomplete to populate
            except Exception as e:
                print(f"    ERROR typing doc type: {e}", flush=True)
            
            # Select autocomplete item - try clicking on visible dropdown option
            try:
                # Look for the autocomplete dropdown list
                # Tyler Tech uses ul.ui-autocomplete or div with autocomplete items
                autocomplete_item = self.page.locator(f"ul.ui-autocomplete li:has-text('{doc_type}'), .cb-dropdown-list li:has-text('{doc_type}')")
                
                if await autocomplete_item.count() > 0:
                    # Click the matching autocomplete item
                    await autocomplete_item.first.click()
                    print(f"    Clicked autocomplete item: {doc_type}", flush=True)
                else:
                    # Fallback: try keyboard navigation
                    print(f"    No autocomplete dropdown found, trying keyboard...", flush=True)
                    await doc_input.press("ArrowDown")
                    await self.page.wait_for_timeout(200)
                    await doc_input.press("Enter")
                    print(f"    Selected via keyboard: {doc_type}", flush=True)
            except Exception as e:
                print(f"    Could not select autocomplete item: {e}", flush=True)
            
            await self.page.wait_for_timeout(1000)
            
            # Verify selection was added (look for tag/pill in the holder)
            selection_count = await self.page.evaluate("""() => {
                const holder = document.querySelector('#field_selfservice_documentTypes-holder');
                if (holder) {
                    return holder.querySelectorAll('li.cblist-input-list.transition-background').length;
                }
                return 0;
            }""")
            
            if selection_count == 0:
                print(f"    Warning: Doc type '{doc_type}' may not have been selected properly", flush=True)
            else:
                print(f"    Selection confirmed ({selection_count} doc type(s) selected)", flush=True)
            
            await self.page.wait_for_timeout(500)
            
            # Click Search button using JavaScript (more reliable for SPA pages)
            print("    Clicking Search...", flush=True)
            await self.page.evaluate("document.querySelector('#searchButton').click()")
            
            # Wait for navigation or results to load (with timeout fallback)
            try:
                await self.page.wait_for_load_state("networkidle", timeout=15000)
            except Exception:
                # networkidle can fail if page has ongoing activity
                pass
            
            # Wait for results to appear - use the actual result row selector
            try:
                await self.page.wait_for_selector("li.ss-search-row", timeout=10000)
            except:
                # No results yet, wait a bit more for async content
                await self.page.wait_for_timeout(2000)
            
            # Tyler Tech uses li.ss-search-row for result rows
            rows = await self.page.locator("li.ss-search-row").all()
            
            if rows:
                print(f"    Found {len(rows)} result rows", flush=True)
            else:
                print(f"    No results found for '{doc_type}'", flush=True)
                return []
            
            # Parse Tyler Tech result rows using JavaScript for speed
            # This avoids the slow Playwright locator calls with 30s default timeout
            for row in rows[:limit]:
                try:
                    # Extract data from row using fast JavaScript evaluation
                    row_data = await row.evaluate("""(row) => {
                        const doc_id = row.getAttribute('data-documentid') || '';
                        
                        // Get h1 text for doc number and type
                        const h1 = row.querySelector('h1');
                        let doc_number = '';
                        let doc_type = '';
                        if (h1) {
                            const h1Text = h1.innerText || '';
                            const parts = h1Text.split('•').map(s => s.trim());
                            doc_number = parts[0] || '';
                            doc_type = parts[1] || '';
                        }
                        
                        // Get column data
                        let record_date = '';
                        let grantor = '';
                        let grantee = '';
                        
                        const columns = row.querySelectorAll('.searchResultThreeColumn');
                        for (const col of columns) {
                            const colText = col.innerText || '';
                            const boldEl = col.querySelector('b');
                            const value = boldEl ? boldEl.innerText.trim() : '';
                            
                            if (colText.includes('Recording Date')) {
                                record_date = value;
                            } else if (colText.includes('Grantor')) {
                                grantor = value;
                            } else if (colText.includes('Grantee')) {
                                grantee = value;
                            }
                        }
                        
                        return { doc_id, doc_number, doc_type, record_date, grantor, grantee };
                    }""")
                    
                    if row_data and row_data.get("doc_id"):
                        results.append(row_data)
                except Exception as e:
                    print(f"    Error parsing row: {e}", flush=True)
                    continue
                    
        except Exception as e:
            print(f"Search error: {e}")
        
        return results
    
    async def search_by_sequence(self, seq_num: str) -> List[Dict]:
        """Search for a document by its sequence number."""
        if not self.initialized or not await self.validate_session():
            return [{"error": "Session not initialized or browser closed. Please re-initialize."}]
        
        print(f"Searching by sequence number: {seq_num}...", flush=True)
        results = []
        
        try:
            # Clear previous selections
            has_existing_selection = await self.page.evaluate("""(() => {
                const holder = document.querySelector('#field_selfservice_documentTypes-holder');
                if (holder) {
                    return holder.querySelectorAll('li.cblist-input-list.transition-background').length > 0;
                }
                return false;
            })()""")
            
            if has_existing_selection:
                print("    Clearing previous doc type selections...", flush=True)
                clear_btn = self.page.locator("#clearSearchButton")
                if await clear_btn.is_visible(timeout=2000):
                    await clear_btn.click()
                    await self.page.wait_for_load_state("networkidle")
                    await self.page.wait_for_timeout(1000)
            
            # Find Sequence Number input - Try multiple common selectors for Tyler Tech
            seq_input = None
            selectors = [
                "#field_RecordingDateID_SequenceNumber",
                "input[name='SequenceNumber']", 
                "input[aria-label='Sequence Number']",
                "input[placeholder='Sequence Number']"
            ]
            
            for selector in selectors:
                if await self.page.locator(selector).count() > 0:
                    seq_input = self.page.locator(selector).first
                    print(f"    Found sequence input via: {selector}", flush=True)
                    break
            
            if not seq_input:
                # Fallback: Find by label text
                print("    Trying to find sequence input by label...", flush=True)
                try:
                    # Find label with text "Sequence" and get associated input
                    seq_input = self.page.locator("label:has-text('Sequence')").locator("..").locator("input").first
                    if await seq_input.count() == 0:
                         print("    Could not find sequence input", flush=True)
                         return [{"error": "Sequence number input field not found"}]
                except:
                    return [{"error": "Sequence number input field not found"}]

            # Clear and fill sequence number
            await seq_input.fill("")
            await seq_input.type(seq_num, delay=50)
            print(f"    Filled sequence number: {seq_num}", flush=True)
            
            # Clear date fields to ensure we find the exact doc regardless of date
            try:
                await self.page.locator("#field_RecordingDateID_DOT_StartDate").fill("")
                await self.page.locator("#field_RecordingDateID_DOT_EndDate").fill("")
                print("    Cleared date range filters", flush=True)
            except:
                pass
                
            await self.page.wait_for_timeout(500)
            
            # Click Search
            print("    Clicking Search...", flush=True)
            await self.page.evaluate("document.querySelector('#searchButton').click()")
            
            try:
                await self.page.wait_for_load_state("networkidle", timeout=15000)
            except:
                pass
            
            # Wait for results
            try:
                await self.page.wait_for_selector("li.ss-search-row", timeout=10000)
            except:
                await self.page.wait_for_timeout(2000)
            
            rows = await self.page.locator("li.ss-search-row").all()
            
            if rows:
                print(f"    Found {len(rows)} result rows", flush=True)
                
                # Parse results (same logic as search_by_doc_type)
                for row in rows:
                    try:
                        row_data = await row.evaluate("""(row) => {
                            const doc_id = row.getAttribute('data-documentid') || '';
                            const h1 = row.querySelector('h1');
                            let doc_number = '';
                            let doc_type = '';
                            if (h1) {
                                const h1Text = h1.innerText || '';
                                const parts = h1Text.split('•').map(s => s.trim());
                                doc_number = parts[0] || '';
                                doc_type = parts[1] || '';
                            }
                            
                            let record_date = '';
                            const columns = row.querySelectorAll('.searchResultThreeColumn');
                            for (const col of columns) {
                                const colText = col.innerText || '';
                                const boldEl = col.querySelector('b');
                                const value = boldEl ? boldEl.innerText.trim() : '';
                                if (colText.includes('Recording Date')) record_date = value;
                            }
                            
                            return { doc_id, doc_number, doc_type, record_date };
                        }""")
                        
                        if row_data and row_data.get("doc_id"):
                            results.append(row_data)
                    except Exception as e:
                        print(f"    Error parsing row: {e}", flush=True)
            else:
                print(f"    No results found for sequence {seq_num}", flush=True)

        except Exception as e:
            print(f"Sequence search error: {e}")
            return [{"error": str(e)}]
            
        return results
    
    async def search_by_name(self, name: str, search_type: str = "grantor", deed_types_only: bool = True, limit: int = 20) -> List[Dict]:
        """
        Search for documents by Grantor or Grantee name.
        
        Args:
            name: The name to search for (e.g., owner name from GIS)
            search_type: "grantor", "grantee", or "both" 
            deed_types_only: If True, filter for deed-related document types
            limit: Maximum number of results to return
            
        Returns:
            List of documents found, sorted by recording date (newest first)
        """
        if not self.initialized or not await self.validate_session():
            return [{"error": "Session not initialized or browser closed. Please re-initialize."}]
        
        print(f"Searching by {search_type}: {name}...", flush=True)
        results = []
        
        try:
            # ALWAYS click Clear button at start of every search to reset form
            print("    Clicking Clear Search to reset form...", flush=True)
            clear_btn = self.page.locator("#clearSearchButton")
            if await clear_btn.is_visible(timeout=3000):
                await clear_btn.click()
                await self.page.wait_for_load_state("networkidle")
                await self.page.wait_for_timeout(1000)
                print("    Form cleared successfully", flush=True)
            else:
                print("    Clear button not found, continuing...", flush=True)
            
            # Also manually clear the name fields as backup
            for field_id in ["#field_GrantorName", "#field_GranteeName", "input[name='GrantorName']", "input[name='GranteeName']"]:
                try:
                    field = self.page.locator(field_id).first
                    if await field.count() > 0:
                        await field.fill("")
                except:
                    pass
            
            # Helper to find input
            async def find_input(label_text, possible_ids):
                # 1. Try specific IDs
                for selector in possible_ids:
                    if await self.page.locator(selector).count() > 0:
                        print(f"    Found {label_text} input via: {selector}", flush=True)
                        return self.page.locator(selector).first
                
                # 2. Try by Label Text
                try:
                    # Find label with exact text or containing text
                    label = self.page.locator(f"label:has-text('{label_text}')").first
                    if await label.count() > 0:
                        # Check 'for' attribute
                        for_id = await label.get_attribute("for")
                        if for_id:
                            print(f"    Found {label_text} input via label 'for' attribute: #{for_id}", flush=True)
                            return self.page.locator(f"#{for_id}")
                        
                        # Check if input is nested
                        if await label.locator("input").count() > 0:
                            print(f"    Found {label_text} input nested in label", flush=True)
                            return label.locator("input").first
                            
                        # Check parent's input (common in form groups)
                        # label -> parent -> input
                        parent_input = label.locator("..").locator("input").first
                        if await parent_input.count() > 0:
                            print(f"    Found {label_text} input via parent traversal", flush=True)
                            return parent_input
                except Exception as e:
                    print(f"    Error finding input by label '{label_text}': {e}", flush=True)
                    
                return None

            # Fill Grantor field
            if search_type in ["grantor", "both"]:
                grantor_input = await find_input("Grantor", [
                    "#field_GrantorName", 
                    "#field_Grantor",
                    "input[name='GrantorName']",
                    "input[aria-label*='Grantor']", 
                    "input[placeholder*='Grantor']"
                ])
                
                if grantor_input:
                    await grantor_input.fill("")
                    await grantor_input.type(name, delay=30)
                    print(f"    Filled Grantor: {name}", flush=True)
                else:
                    print("    ERROR: Could not find Grantor input field", flush=True)
            
            # Fill Grantee field - use GranteeID (that's the actual field name on the site)
            if search_type in ["grantee", "both"]:
                grantee_input = await find_input("Grantee", [
                    "#field_GranteeID",   # This is the actual field name on the site
                    "#field_GranteeName", 
                    "input[name='GranteeID']",
                    "input[name='GranteeName']",
                ])
                
                if grantee_input:
                    await grantee_input.fill("")
                    await grantee_input.type(name, delay=30)
                    print(f"    Filled Grantee: {name}", flush=True)
                else:
                    print("    ERROR: Could not find Grantee input field", flush=True)
            
            # Clear date fields to search all time
            try:
                await self.page.locator("#field_RecordingDateID_DOT_StartDate").fill("")
                await self.page.locator("#field_RecordingDateID_DOT_EndDate").fill("")
            except:
                pass
            
            await self.page.wait_for_timeout(500)
            
            # Click Search
            print("    Clicking Search...", flush=True)
            await self.page.evaluate("document.querySelector('#searchButton').click()")
            
            try:
                await self.page.wait_for_load_state("networkidle", timeout=15000)
            except:
                pass
            
            # Wait for results
            try:
                await self.page.wait_for_selector("li.ss-search-row", timeout=10000)
            except:
                await self.page.wait_for_timeout(2000)
            
            rows = await self.page.locator("li.ss-search-row").all()
            
            if rows:
                print(f"    Found {len(rows)} result rows", flush=True)
                
                # Deed-related document types to filter for
                deed_keywords = ["DEED", "WARRANTY", "QUITCLAIM", "QCD", "GRANT", "TRANSFER", "CONVEY", "SALE"]
                
                for row in rows[:limit * 2]:  # Get extra to filter
                    try:
                        # DEBUG: Print first row HTML to understand structure
                        if results == []:
                            html = await row.inner_html()
                            print(f"    DEBUG: First row HTML (truncated): {html[:500]}...", flush=True)

                        row_data = await row.evaluate("""(row) => {
                            try {
                                const doc_id = row.getAttribute('data-documentid') || '';
                                
                                // Try finding the header text (Doc Number + Type)
                                // It might be in an h1, or just a div with specific class
                                let h1Text = '';
                                const h1 = row.querySelector('h1');
                                if (h1) {
                                    h1Text = h1.innerText;
                                } else {
                                    // Fallback: try finding text that looks like a doc number
                                    const headerLink = row.querySelector('a.doc-link');
                                    if (headerLink) h1Text = headerLink.innerText;
                                }
                                
                                let doc_number = '';
                                let doc_type = '';
                                if (h1Text) {
                                    const parts = h1Text.split('•').map(s => s.trim());
                                    doc_number = parts[0] || '';
                                    doc_type = parts[parts.length - 1] || ''; // Type is usually last
                                }
                                
                                let record_date = '';
                                let grantor = '';
                                let grantee = '';
                                
                                // Try finding columns
                                const columns = row.querySelectorAll('.searchResultThreeColumn, .col-md-4');
                                for (const col of columns) {
                                    const colText = col.innerText || '';
                                    const boldEl = col.querySelector('b, strong, span.value');
                                    const value = boldEl ? boldEl.innerText.trim() : '';
                                    
                                    if (colText.includes('Recording Date')) record_date = value;
                                    if (colText.includes('Grantor')) grantor = value;
                                    if (colText.includes('Grantee')) grantee = value;
                                }
                                
                                // Parse Book/Page
                                let book_page = '';
                                const headerText = row.innerText;
                                const bpMatch = headerText.match(/B:\s*(\d+)\s*P:\s*(\d+)/);
                                if (bpMatch) {
                                    book_page = `B: ${bpMatch[1]} P: ${bpMatch[2]}`;
                                }

                                // Parse Related Documents
                                let related_docs = [];
                                // Look for the Related Documents section
                                // It's usually in a div or ul with specific classes or text
                                // Based on screenshot, it looks like rows inside the main row
                                const relatedRows = row.querySelectorAll('li.ss-search-row-related, .related-document-row, tr.related-doc'); 
                                // If specific class not found, try searching by text content in nested divs
                                if (relatedRows.length === 0) {
                                    const allDivs = row.querySelectorAll('div');
                                    for (const div of allDivs) {
                                        if (div.innerText && div.innerText.includes('Related Documents')) {
                                            // Found the header, now look for siblings or children that look like docs
                                            // This is tricky without seeing HTML. Let's try a generic approach:
                                            // Look for text patterns like "Document Number" followed by values
                                        }
                                    }
                                }

                                // Robust approach for Related Docs based on typical Tyler structure:
                                // They are often in a separate UL or Table nested in the row
                                const relatedSection = Array.from(row.querySelectorAll('div, ul, table')).find(el => el.innerText && el.innerText.includes('Related Documents'));
                                if (relatedSection) {
                                    // Try to find lines that look like docs
                                    // Pattern: DocNumber Type Date Book/Page
                                    const lines = relatedSection.innerText.split('\n');
                                    for (const line of lines) {
                                        // Skip the header line
                                        if (line.includes('Related Documents')) continue;
                                        
                                        // Simple heuristic: if line has a date and some text, it might be a doc
                                        // Better: look for the document number pattern (usually starts with year like 2012...)
                                        const docNumMatch = line.match(/(\d{8,})/); // 8+ digits
                                        if (docNumMatch) {
                                            related_docs.push({
                                                doc_number: docNumMatch[0],
                                                full_text: line.trim()
                                            });
                                        }
                                    }
                                }

                                return { doc_id, doc_number, doc_type, record_date, grantor, grantee, h1Text, book_page, related_docs };
                            } catch (e) {
                                return { error: e.toString() };
                            }
                        }""")
                        
                        if row_data.get("error"):
                            print(f"    JS Parsing Error: {row_data['error']}", flush=True)
                            continue
                            
                        # print(f"    DEBUG: Parsed row data: {row_data}", flush=True)
                        
                        if row_data and row_data.get("doc_id"):
                            # Filter for deeds if requested
                            is_deed = False
                            if deed_types_only:
                                doc_type_upper = row_data.get("doc_type", "").upper()
                                # Expanded list of relevant document types
                                relevant_keywords = [
                                    # Deeds
                                    "DEED", "WARRANTY", "QUITCLAIM", "QCD", "GRANT", "TRANSFER", "CONVEY",
                                    # Trust & Mortgage docs
                                    "TRUST", "DEED OF TRUST", "MORTGAGE", "RECONVEYANCE", "SUBSTITUTION",
                                    # Liens & Encumbrances
                                    "LIEN", "MECHANICS LIEN", "FEDERAL", "TAX LIEN", "RELEASE", "SATISFACTION",
                                    # Notices & Court
                                    "NOTICE", "LIS PENDENS", "NOTICE OF DEFAULT", "NOTICE SALE",
                                    "JUDGMENT", "ABSTRACT JUDGMENT",
                                    # Other relevant
                                    "SALE", "AGREEMENT", "EASEMENT", "AFFIDAVIT", "ASSIGNMENT", "ASSUMPTION"
                                ]
                                if any(k in doc_type_upper for k in relevant_keywords):
                                    is_deed = True
                            else:
                                is_deed = True
                                
                            if is_deed:
                                results.append(row_data)
                    except Exception as e:
                        print(f"    Error parsing row: {e}", flush=True)
                        continue
                        
                        if row_data and row_data.get("doc_id"):
                            # Filter for deed types if requested
                            if deed_types_only:
                                doc_type_upper = row_data.get("doc_type", "").upper()
                                if any(kw in doc_type_upper for kw in deed_keywords):
                                    results.append(row_data)
                            else:
                                results.append(row_data)
                                
                            if len(results) >= limit:
                                break
                    except Exception as e:
                        print(f"    Error parsing row: {e}", flush=True)
                
                # Sort by recording date (newest first)
                from datetime import datetime
                def parse_date(d):
                    try:
                        return datetime.strptime(d.get("record_date", ""), "%m/%d/%Y")
                    except:
                        return datetime.min
                results.sort(key=parse_date, reverse=True)
                
            else:
                print(f"    No results found for name: {name}", flush=True)
        
        except Exception as e:
            print(f"Name search error: {e}")
            return [{"error": str(e)}]
        
        return results
    
        """Search for documents using active session."""
        if not self.initialized:
            return [{"error": "Session not initialized. Call initialize() first."}]
        
        search_types = []
        if doc_type:
            search_types = [doc_type]
        elif distress_filter and distress_filter in DOC_TYPE_MAP:
            search_types = DOC_TYPE_MAP[distress_filter]
        else:
            return [{"error": "Must specify doc_type or distress_filter"}]
        
        all_results = []
        for doc_type_search in search_types:
            print(f"  Searching: {doc_type_search}...")
            results = await self.search_by_doc_type(doc_type_search, limit=limit)
            all_results.extend(results)
            
            if len(all_results) >= limit:
                break
        
        return all_results[:limit]
    
    async def close(self):
        """Close the recorder session."""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        self.initialized = False
        print("Recorder session closed.")
    
    async def view_document(self, doc_id: str) -> bool:
        """
        Navigate directly to the document viewer page.
        Uses direct URL navigation - works regardless of current page state.
        """
        if not self.initialized:
            print("Session not initialized")
            return False
        
        try:
            # Navigate directly to document page using known URL pattern
            # This works regardless of current search results on page
            doc_url = f"https://pimacountyaz-web.tylerhost.net/web/document/{doc_id}?search=DOCSEARCH55S10"
            
            print(f"  Opening document: {doc_id}", flush=True)
            await self.page.goto(doc_url)
            
            # Wait for page to load
            try:
                await self.page.wait_for_load_state("networkidle", timeout=15000)
            except:
                await self.page.wait_for_load_state("domcontentloaded", timeout=5000)
            
            # Check for CAPTCHA challenge
            await self.page.wait_for_timeout(2000)
            if await self._check_and_handle_captcha():
                # User solved CAPTCHA, wait for actual content to load
                await self.page.wait_for_timeout(3000)
            
            # Wait for viewer to fully load
            await self.page.wait_for_timeout(1000)
            
            return True
            
        except Exception as e:
            print(f"  Error viewing document: {e}", flush=True)
            return False
    
    async def _check_and_handle_captcha(self) -> bool:
        """
        Check if a CAPTCHA challenge is present and wait for user to solve it.
        Returns True if CAPTCHA was detected and solved, False if no CAPTCHA.
        """
        try:
            # Check for common CAPTCHA indicators in page content
            page_content = await self.page.content()
            captcha_indicators = [
                "confirm you are human",
                "security check",
                "not a robot",
                "captcha",
                "human verification",
            ]
            
            is_captcha = any(indicator in page_content.lower() for indicator in captcha_indicators)
            
            if is_captcha:
                print("", flush=True)
                print("  CAPTCHA DETECTED!", flush=True)
                print("  Please solve the CAPTCHA in the browser window.", flush=True)
                input("  >>> Press Enter when you've completed the verification: ")
                
                # Wait for page to reload after CAPTCHA solution
                try:
                    await self.page.wait_for_load_state("networkidle", timeout=15000)
                except:
                    pass
                print("  CAPTCHA solved, continuing...", flush=True)
                return True
            
            return False
            
        except Exception as e:
            print(f"  CAPTCHA check error: {e}", flush=True)
            return False
    
    async def download_document(self, doc_id: str, download_dir: str = None) -> Optional[str]:
        """
        Download PDF for a document, return file path.
        Must be called from the search results page after a search.
        
        Args:
            doc_id: Document ID from search results (from data-documentid attribute)
            download_dir: Directory to save PDFs (defaults to ./downloads)
        
        Returns:
            Path to downloaded PDF file, or None if failed
        """
        if not self.initialized:
            print("Session not initialized")
            return None
        
        # Setup download directory
        if download_dir is None:
            download_dir = Path(__file__).parent / "downloads"
        else:
            download_dir = Path(download_dir)
        download_dir.mkdir(parents=True, exist_ok=True)
        
        max_retries = 3
        
        for attempt in range(1, max_retries + 1):
            try:
                # First view the document - this opens the viewer
                if not await self.view_document(doc_id):
                    print(f"  Attempt {attempt}/{max_retries}: Failed to open document viewer", flush=True)
                    if attempt < max_retries:
                        await self.page.wait_for_timeout(2000)
                        continue
                    else:
                        return None
                
                print("  Looking for PDF viewer and download button...", flush=True)
                await self.page.wait_for_timeout(2000)
                
                # The PDF viewer might be in an iframe - search all frames
                pdf_frame = None
                for frame in self.page.frames:
                    try:
                        download_btn = frame.locator("#download")
                        if await download_btn.count() > 0:
                            pdf_frame = frame
                            print(f"  Found PDF viewer in frame", flush=True)
                            break
                    except:
                        continue
                
                if not pdf_frame:
                    # Try main page
                    pdf_frame = self.page
                
                # Setup download handler before clicking
                async with self.page.expect_download(timeout=30000) as download_info:
                    download_btn = pdf_frame.locator("#download")
                    if await download_btn.count() > 0:
                        await download_btn.click()
                        print("  Clicked download button", flush=True)
                    else:
                        # Try other download buttons
                        alt_btns = pdf_frame.locator("button:has-text('Download'), a:has-text('Download')")
                        if await alt_btns.count() > 0:
                            await alt_btns.first.click()
                            print("  Clicked alternative download button", flush=True)
                        else:
                            raise Exception("No download button found")
                
                download = await download_info.value
                
                # Save to downloads folder
                pdf_path = download_dir / f"{doc_id}.pdf"
                await download.save_as(str(pdf_path))
                print(f"  PDF downloaded: {pdf_path}", flush=True)
                
                return str(pdf_path)
                
            except Exception as e:
                print(f"  Attempt {attempt}/{max_retries} failed: {e}", flush=True)
                if attempt < max_retries:
                    print(f"  Retrying...", flush=True)
                    await self.page.wait_for_timeout(2000)
                else:
                    print(f"  All {max_retries} attempts failed", flush=True)
                    return None
    
    async def _capture_viewer_pages(self, doc_id: str, download_dir: Path) -> Optional[str]:
        """Fallback: Capture viewer pages as images if download fails."""
        try:
            images_dir = download_dir / f"{doc_id}_images"
            images_dir.mkdir(parents=True, exist_ok=True)
            
            # Get total page count from viewer
            page_info = self.page.locator(".page-count, #page-count")
            page_count = 1
            try:
                page_text = await page_info.inner_text()
                # Parse "1 of 23" format
                if "of" in page_text:
                    page_count = int(page_text.split("of")[1].strip())
            except:
                pass
            
            print(f"  Capturing {page_count} pages...", flush=True)
            
            for i in range(page_count):
                # Screenshot current page
                await self.page.screenshot(path=str(images_dir / f"page_{i+1}.png"))
                
                # Go to next page if not last
                if i < page_count - 1:
                    next_btn = self.page.locator("#next, button:has-text('Next')")
                    if await next_btn.is_visible():
                        await next_btn.click()
                        await self.page.wait_for_timeout(1000)
            
            print(f"  Saved {page_count} page images to {images_dir}", flush=True)
            return str(images_dir)
            
        except Exception as e:
            print(f"  Capture error: {e}", flush=True)
            return None
    
    async def extract_with_vertex_ai(self, file_path: str) -> Dict:
        """
        Extract structured data from document using Vertex AI (Gemini).
        Uses the same GCP credentials as other services in the backend.
        
        Args:
            file_path: Path to PDF file or directory of images
        
        Returns:
            Dict with extracted fields: property_address, lien_amount, debtor, creditor, etc.
        """
        import json
        
        file_path = Path(file_path)
        
        # Collect image files
        image_files = []
        if file_path.is_dir():
            # Directory of images
            image_files = sorted(file_path.glob("*.png"))
        elif file_path.suffix.lower() == ".pdf":
            # Convert PDF pages to images using PyMuPDF (no external dependencies)
            try:
                import fitz  # PyMuPDF
                doc = fitz.open(str(file_path))
                temp_dir = file_path.parent / f"{file_path.stem}_temp"
                temp_dir.mkdir(exist_ok=True)
                
                for i, page in enumerate(doc):
                    if i >= 5:  # First 5 pages only
                        break
                    # Render page to image (2x resolution for better OCR)
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                    img_path = temp_dir / f"page_{i+1}.png"
                    pix.save(str(img_path))
                    image_files.append(img_path)
                doc.close()
            except ImportError:
                return {"error": "PyMuPDF not installed. Run: pip install pymupdf"}
        else:
            # Single image
            image_files = [file_path]
        
        if not image_files:
            return {"error": "No images found"}
        
        print(f"  Sending {len(image_files)} page(s) to Vertex AI...", flush=True)
        
        try:
            # Initialize Vertex AI
            import vertexai
            from vertexai.generative_models import GenerativeModel, Part
            from google.oauth2 import service_account
            
            # Use env var or default matching backend/app/core/config.py
            project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "arela-project")
            location = os.environ.get("VERTEX_AI_LOCATION", "us-central1")
            
            # Get credentials path
            creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
            if not creds_path:
                # Try to find credentials file
                creds_path = str(BACKEND_DIR / "credentials.json")
            
            if not Path(creds_path).exists():
                return {"error": f"Credentials file not found: {creds_path}"}
            
            # Load credentials explicitly
            credentials = service_account.Credentials.from_service_account_file(creds_path)
            
            vertexai.init(project=project_id, location=location, credentials=credentials)
            model = GenerativeModel("gemini-2.0-flash")
            
            # Prepare image parts
            image_parts = []
            for img_path in image_files[:5]:  # Limit to 5 pages
                with open(img_path, "rb") as f:
                    image_data = f.read()
                    image_parts.append(Part.from_data(image_data, mime_type="image/png"))
            
            # Build prompt - emphasize property address extraction
            prompt = """Analyze this legal document image and extract the following information as JSON.

IMPORTANT: Property addresses are often found in:
- The legal description section (look for street addresses near lot/block references)
- "Property Address" or "Property Location" labels
- "Commonly known as" followed by an address
- References to real property located at or in [address]
- APN/Parcel numbers often have associated street addresses nearby

{
    "document_type": "type of document (e.g., Lis Pendens, Notice of Trustee Sale, Mechanics Lien, Judgment, Dissolution of Marriage, etc.)",
    "property_address": "CRITICAL: Full street address of any real property mentioned (e.g., '123 Main St, Tucson, AZ 85701'). Look carefully in legal descriptions.",
    "parcel_number": "APN/parcel number if mentioned (e.g., '123-45-6789')",
    "legal_description": "Legal property description if found (lot, block, subdivision, etc.)",
    "debtor_name": "name of debtor/defendant/property owner/respondent",
    "creditor_name": "name of creditor/plaintiff/lien holder/petitioner",
    "amount": "dollar amount of lien/judgment/debt if mentioned",
    "recording_date": "date document was recorded",
    "case_number": "court case number if applicable",
    "trustee_sale_date": "if this is a Notice of Sale, the scheduled auction/sale date",
    "summary": "brief 1-2 sentence summary focusing on the property and parties involved"
}

If a field is not found in the document, use null. Return ONLY valid JSON."""

            # Call Vertex AI
            response = model.generate_content([prompt, *image_parts])
            text = response.text
            
            # Extract JSON from response
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
            
            extracted = json.loads(text.strip())
            print(f"  Extracted data successfully", flush=True)
            return extracted
                
        except Exception as e:
            print(f"  Vertex AI error: {e}", flush=True)
            return {"error": str(e)}


async def interactive_session():
    """Run an interactive recorder session."""
    session = RecorderSession()
    
    # Store last search results for download
    last_results = []
    
    print()
    print("=" * 50)
    print("PIMA COUNTY RECORDER - DOCUMENT TOOL")
    print("=" * 50)
    print()
    print("Commands:")
    print("  lis      - Search LIS PENDENS")
    print("  nots     - Search NOTICE SALE")
    print("  sub      - Search SUBSTITUTION TRUSTEE")
    print("  federal  - Search Federal Liens")
    print("  city     - Search City Liens")
    print("  lien     - Search General Liens")
    print("  mechanic - Search Mechanics Liens")
    print("  notice   - Search Notice Liens")
    print("  judgment - Search Judgments")
    print("  absjudge - Search Abstract Judgments")
    print("  divorce  - Search Divorce")
    print("  probate  - Search Probate")
    print("  download <n> | <start>-<end> | <i>,<j>,<k>  - Download PDFs")
    print("  extract <doc_id> - Extract data from PDF with Vertex AI")
    print("  quit     - Exit session")
    print()
    print("Note: Browser will open when you run your first search command.")
    print()
    
    # Search commands that require browser initialization
    search_commands = {"lis", "nots", "sub", "federal", "city", "lien", "mechanic", "notice", "judgment", "absjudge", "divorce", "probate"}
    
    while True:
        cmd = input(">>> ").strip()
        parts = cmd.lower().split()
        
        if not parts:
            continue
        
        action = parts[0]
        
        if action == "help":
            print()
            print("=" * 50)
            print("AVAILABLE COMMANDS")
            print("=" * 50)
            print()
            print("SEARCH COMMANDS (opens browser on first use):")
            print("  lis      - Search LIS PENDENS (pre-foreclosure notices)")
            print("  nots     - Search NOTICE SALE (foreclosure sales)")
            print("  sub      - Search SUBSTITUTION TRUSTEE")
            print("  federal  - Search FEDERAL LIEN (IRS tax liens)")
            print("  city     - Search CITY LIEN (municipal liens)")
            print("  lien     - Search LIEN (general liens)")
            print("  mechanic - Search MECHANICS LIEN (contractor liens)")
            print("  notice   - Search NOTICE LIEN")
            print("  judgment - Search JUDGMENT (court judgments)")
            print("  absjudge - Search ABSTRACT JUDGMENT")
            print("  divorce  - Search DISSOLUTION OF MARRIAGE")
            print("  probate  - Search AFFIDAVIT OF SUCCESSION")
            print()
            print("DOWNLOAD COMMANDS:")
            print("  download <n>         - Download single document (e.g., download 1)")
            print("  download <start>-<end> - Download range (e.g., download 1-5)")
            print("  download <i>,<j>,<k> - Download specific docs (e.g., download 1,3,5)")
            print()
            print("EXTRACTION COMMANDS:")
            print("  extract <doc_id>     - Extract data from PDF using Vertex AI")
            print("                         (e.g., extract DOC415S311)")
            print()
            print("OTHER:")
            print("  help     - Show this help message")
            print("  quit     - Exit the session")
            print()
        elif action == "quit":
            break
        elif action == "extract":
            # Extract doesn't need browser - works directly with local files
            if len(parts) < 2:
                print("Usage: extract <doc_id>  (e.g., 'extract DOC413S329')")
                continue
            doc_id = parts[1].upper()
            pdf_path = f"downloads/{doc_id}.pdf"
            if not os.path.exists(pdf_path):
                # Try images folder
                pdf_path = f"downloads/{doc_id}_images"
            if not os.path.exists(pdf_path):
                print(f"File not found: {pdf_path}")
                print()
                continue
            print(f"Extracting data from {pdf_path}...")
            data = await session.extract_with_vertex_ai(pdf_path)
            print("Extracted data:")
            import json
            print(json.dumps(data, indent=2))
        elif action == "download":
            if not session.initialized:
                print("No search results. Run a search command first (e.g., 'pre', 'federal').")
                print()
                continue
            if len(parts) < 2:
                print("Usage: download <index> or download <start>-<end> or download <i>,<j>,<k>")
                print("  Examples: download 1  |  download 1-5  |  download 1,3,5")
                continue
            
            # Parse indices - support: "1", "1-5", "1,2,3"
            indices = []
            arg = parts[1]
            
            if "-" in arg and "," not in arg:
                # Range format: "1-5"
                try:
                    start, end = arg.split("-")
                    start_idx = int(start) - 1
                    end_idx = int(end) - 1
                    if start_idx <= end_idx:
                        indices = list(range(start_idx, end_idx + 1))
                    else:
                        print("Invalid range. Start must be <= end.")
                        continue
                except ValueError:
                    print("Invalid range format. Use: download 1-5")
                    continue
            elif "," in arg:
                # Comma-separated: "1,2,3"
                try:
                    indices = [int(x.strip()) - 1 for x in arg.split(",")]
                except ValueError:
                    print("Invalid indices. Use: download 1,3,5")
                    continue
            else:
                # Single index: "1"
                try:
                    indices = [int(arg) - 1]
                except ValueError:
                    print("Invalid index. Must be a number.")
                    continue
            
            # Validate indices
            valid_indices = [i for i in indices if 0 <= i < len(last_results)]
            if not valid_indices:
                print(f"No valid indices. Must be 1-{len(last_results)}")
                continue
            
            # Download each document
            success_count = 0
            fail_count = 0
            for idx in valid_indices:
                doc_id = last_results[idx].get("doc_id")
                print(f"[{idx+1}/{len(valid_indices)}] Downloading {doc_id}...")
                pdf_path = await session.download_document(doc_id)
                if pdf_path:
                    print(f"  {pdf_path}")
                    success_count += 1
                else:
                    print(f"  Failed")
                    fail_count += 1
            
            # Summary
            if len(valid_indices) > 1:
                print(f"\nBatch complete: {success_count} succeeded, {fail_count} failed")
        elif action in search_commands:
            # Lazy initialization - only open browser when first search is run
            if not session.initialized:
                print("Initializing browser (first time only)...")
                if not await session.initialize():
                    print("Failed to initialize browser. Please try again.")
                    print()
                    continue
            
            # Run the search
            if action == "lis":
                print("Searching LIS PENDENS...")
                last_results = await session.search_by_doc_type("LIS PENDENS", limit=100)
            elif action == "nots":
                print("Searching NOTICE SALE...")
                last_results = await session.search_by_doc_type("NOTICE SALE", limit=100)
            elif action == "sub":
                print("Searching SUBSTITUTION TRUSTEE...")
                last_results = await session.search_by_doc_type("SUBSTITUTION TRUSTEE", limit=100)
            elif action == "federal":
                print("Searching Federal Liens...")
                last_results = await session.search_by_doc_type("FEDERAL LIEN", limit=100)
            elif action == "city":
                print("Searching City Liens...")
                last_results = await session.search_by_doc_type("CITY LIEN", limit=100)
            elif action == "mechanic":
                print("Searching Mechanics Liens...")
                last_results = await session.search_by_doc_type("MECHANICS LIEN", limit=100)
            elif action == "lien":
                print("Searching General Liens...")
                last_results = await session.search_by_doc_type("LIEN", limit=100)
            elif action == "notice":
                print("Searching Notice Liens...")
                last_results = await session.search_by_doc_type("NOTICE LIEN", limit=100)
            elif action == "judgment":
                print("Searching Judgments...")
                last_results = await session.search_by_doc_type("JUDGMENT", limit=100)
            elif action == "absjudge":
                print("Searching Abstract Judgments...")
                last_results = await session.search_by_doc_type("ABSTRACT JUDGMENT", limit=100)
            elif action == "divorce":
                print("Searching Divorce...")
                last_results = await session.search_by_doc_type("DISSOLUTION MARRIAGE", limit=100)
            elif action == "probate":
                print("Searching Probate...")
                last_results = await session.search_by_doc_type("AFFIDAVIT SUCCESSION", limit=100)
            
            print(f"Found {len(last_results)} results:")
            for i, r in enumerate(last_results[:10], 1):
                print(f"  {i}. {r.get('doc_number')} - {r.get('doc_type')} ({r.get('record_date')})")
            if len(last_results) > 10:
                print(f"  ... and {len(last_results) - 10} more. Use download 1-{len(last_results)} for batch.")
        else:
            print("Unknown command. Type 'help' for available commands.")
        print()
    
    await session.close()


if __name__ == "__main__":
    asyncio.run(interactive_session())
