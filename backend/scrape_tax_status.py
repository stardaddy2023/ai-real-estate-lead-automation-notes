from playwright.sync_api import sync_playwright
import time

def check_taxes(parcel_id):
    url = "https://paypimagov.com/"
    print(f"Checking {url} for {parcel_id}...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto(url, timeout=30000)
            page.wait_for_load_state("networkidle")
            
            # Handle "First time here?" modal
            try:
                # Wait for modal or search box
                # If modal appears, click close
                if page.is_visible("button[aria-label='Close']"):
                    print("Closing modal...")
                    page.click("button[aria-label='Close']")
                    time.sleep(1) # Wait for animation
            except Exception as e:
                print(f"Modal handling error: {e}")

            # Type parcel ID
            page.wait_for_selector("#searchBox", state="visible")
            page.fill("#searchBox", parcel_id)
            page.press("#searchBox", "Enter")
            
            # Wait for results
            # Either a table row or "No Records Found"
            try:
                page.wait_for_selector(".searchResults tbody tr, .alert-warning", timeout=10000)
            except:
                print("Timeout waiting for results")
            
            # Check for results
            content = page.content()
            if "No Records Found" in content or "alert-warning" in content and "ng-hide" not in page.locator(".alert-warning").get_attribute("class"):
                 print("Result: No records found")
            else:
                # Extract data from table
                rows = page.locator(".searchResults tbody tr").all()
                if rows:
                    print(f"Result: Found {len(rows)} records")
                    for row in rows:
                        text = row.inner_text()
                        print(f"Row: {text}")
                        # Look for "Total Due" or similar in the row text or columns
                else:
                    print("Result: No rows found (but no error?)")
            
            page.screenshot(path="tax_debug_v2.png")
                
        except Exception as e:
            print(f"Error: {e}")
        finally:
            browser.close()

check_taxes("10101001A")
