"""
Pima County Assessor Website Scraper
Fetches Recording Information table for a parcel using Playwright.

The Assessor website (asr.pima.gov) is an Angular SPA that requires
browser automation to extract data. This scraper navigates to the
parcel details page and extracts the Recording Information table.
"""

import asyncio
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path
import re

try:
    from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
except ImportError:
    async_playwright = None


class AssessorScraper:
    """
    Scrapes the Pima County Assessor website for Recording Information.
    
    Usage:
        scraper = AssessorScraper()
        await scraper.initialize()
        recordings = await scraper.get_recording_info("127-03-036A")
        await scraper.close()
    """
    
    ASSESSOR_BASE_URL = "https://asr.pima.gov"
    
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self._initialized = False
    
    async def initialize(self, headless: bool = True):
        """Initialize the browser for scraping."""
        if async_playwright is None:
            raise ImportError("Playwright is required. Install with: pip install playwright && playwright install chromium")
        
        if self._initialized:
            return
        
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=headless)
        self.context = await self.browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        self.page = await self.context.new_page()
        self._initialized = True
        print("[AssessorScraper] Browser initialized")
    
    async def close(self):
        """Close the browser."""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        self._initialized = False
        print("[AssessorScraper] Browser closed")
    
    async def get_recording_info(self, parcel_id: str) -> List[Dict]:
        """
        Fetch Recording Information for a parcel from the Assessor website.
        
        Args:
            parcel_id: The parcel ID (e.g., "127-03-036A")
            
        Returns:
            List of recording records, sorted by date descending (most recent first).
            Each record: {seq_num, docket, page, record_date, deed_type}
        """
        if not self._initialized:
            await self.initialize()
        
        url = f"{self.ASSESSOR_BASE_URL}/parcel-details?_parcel={parcel_id}"
        print(f"[AssessorScraper] Fetching recording info for parcel: {parcel_id}")
        
        try:
            # Navigate to parcel details page
            await self.page.goto(url, wait_until="networkidle", timeout=30000)
            
            # Wait for Angular app to load and render
            await self.page.wait_for_timeout(2000)
            
            # Look for Recording Information section
            # The Assessor site has an accordion/expansion panel for "Recording Information"
            recordings = await self._extract_recording_table()
            
            if recordings:
                # Sort by record_date descending (most recent first)
                recordings.sort(key=lambda x: x.get("record_date_parsed", datetime.min), reverse=True)
                print(f"[AssessorScraper] Found {len(recordings)} recording records")
            else:
                print(f"[AssessorScraper] No recording records found for {parcel_id}")
            
            return recordings
            
        except PlaywrightTimeout:
            print(f"[AssessorScraper] Timeout loading parcel {parcel_id}")
            return []
        except Exception as e:
            print(f"[AssessorScraper] Error fetching {parcel_id}: {e}")
            return []
    
    async def _extract_recording_table(self) -> List[Dict]:
        """Extract the Recording Information table from the current page."""
        records = []
        
        try:
            # Try to find and expand the Recording Information section
            # The site uses Material/Angular expansion panels
            recording_panel = self.page.locator("text=Recording Information").first
            if await recording_panel.count() > 0:
                # Click to expand if collapsed
                try:
                    await recording_panel.click(timeout=3000)
                    await self.page.wait_for_timeout(500)
                except:
                    pass  # Already expanded or no click needed
            
            # Look for the recording table - multiple possible selectors
            table_selectors = [
                "table:has-text('Sequence')",  # Table with Sequence header
                ".recording-info table",
                "mat-expansion-panel:has-text('Recording') table",
                "[id*='recording'] table",
                "table:has(th:text-is('Seq #'))",
            ]
            
            table = None
            for selector in table_selectors:
                try:
                    locator = self.page.locator(selector).first
                    if await locator.count() > 0:
                        table = locator
                        break
                except:
                    continue
            
            if table is None or await table.count() == 0:
                # Fallback: get all tables and find the one with recording headers
                all_tables = await self.page.locator("table").all()
                for t in all_tables:
                    html = await t.inner_html()
                    if "Seq" in html and ("Docket" in html or "Page" in html):
                        table = t
                        break
            
            if table is None:
                print("[AssessorScraper] Recording table not found")
                return []
            
            # Extract rows from the table
            rows = await table.locator("tr").all()
            
            # Find header row to determine column indices
            header_map = {}
            if rows:
                header_cells = await rows[0].locator("th, td").all()
                for i, cell in enumerate(header_cells):
                    text = (await cell.inner_text()).strip().lower()
                    if "seq" in text:
                        header_map["seq_num"] = i
                    elif "docket" in text:
                        header_map["docket"] = i
                    elif "page" in text:
                        header_map["page"] = i
                    elif "date" in text or "record" in text:
                        header_map["record_date"] = i
                    elif "type" in text or "deed" in text:
                        header_map["deed_type"] = i
            
            # Extract data rows
            for row in rows[1:]:  # Skip header
                cells = await row.locator("td").all()
                if not cells:
                    continue
                
                record = {}
                for field, idx in header_map.items():
                    if idx < len(cells):
                        record[field] = (await cells[idx].inner_text()).strip()
                
                # Parse date for sorting
                if "record_date" in record:
                    record["record_date_parsed"] = self._parse_date(record["record_date"])
                else:
                    record["record_date_parsed"] = datetime.min
                
                if record:
                    records.append(record)
            
        except Exception as e:
            print(f"[AssessorScraper] Error extracting table: {e}")
        
        return records
    
    def _parse_date(self, date_str: str) -> datetime:
        """Parse date string to datetime for sorting."""
        if not date_str:
            return datetime.min
        
        formats = [
            "%m/%d/%Y",
            "%Y-%m-%d",
            "%m-%d-%Y",
            "%d/%m/%Y",
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue
        
        return datetime.min
    
    def get_most_recent(self, recordings: List[Dict]) -> Optional[Dict]:
        """Get the most recent recording from a list."""
        if not recordings:
            return None
        
        # Already sorted by date descending in get_recording_info
        return recordings[0] if recordings else None
    
    def get_by_deed_type(self, recordings: List[Dict], deed_types: List[str]) -> List[Dict]:
        """Filter recordings by deed type."""
        if not recordings:
            return []
        
        deed_types_lower = [dt.lower() for dt in deed_types]
        return [
            r for r in recordings 
            if r.get("deed_type", "").lower() in deed_types_lower
        ]


# Convenience function for one-off lookups
async def fetch_recording_info(parcel_id: str) -> List[Dict]:
    """
    Convenience function to fetch recording info for a single parcel.
    Opens and closes browser automatically.
    """
    scraper = AssessorScraper()
    try:
        await scraper.initialize()
        return await scraper.get_recording_info(parcel_id)
    finally:
        await scraper.close()


if __name__ == "__main__":
    # Test the scraper
    async def main():
        parcel_id = "127-03-036A"  # Test parcel
        print(f"Testing AssessorScraper with parcel: {parcel_id}")
        
        recordings = await fetch_recording_info(parcel_id)
        
        if recordings:
            print(f"\nFound {len(recordings)} recording records:")
            for i, rec in enumerate(recordings):
                print(f"  {i+1}. {rec.get('deed_type', 'N/A')} - {rec.get('record_date', 'N/A')} "
                      f"(Seq: {rec.get('seq_num', 'N/A')}, Docket: {rec.get('docket', 'N/A')}/{rec.get('page', 'N/A')})")
        else:
            print("No recordings found")
    
    asyncio.run(main())
