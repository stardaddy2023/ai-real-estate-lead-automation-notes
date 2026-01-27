import requests
import json

# Candidate endpoint based on user input
base_url_1 = "https://www.asr.pima.gov/AssessorSiteData/api/get/parceldetails"
base_url_2 = "https://asr.pima.gov/AssessorSiteData/api/get/parceldetails"

parcels = ["106020300", "131121240"]

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.asr.pima.gov/Parcel/Detail"
}

print("Verifying AssessorSiteData API...")

for parcel in parcels:
    # Construct exact URLs to try
    test_urls = [
        f"{base_url_1}/{parcel}",
        f"{base_url_2}/{parcel}",
    ]
    
    for url in test_urls:
        print(f"GET {url} ...", end=" ")
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            print(f"Status: {resp.status_code}")
            
            if resp.status_code == 200:
                try:
                    data = resp.json()
                    # Check if it has SalesInfo
                    if "SalesInfo" in data:
                        sales = data["SalesInfo"]
                        print(f"  [SUCCESS] Found SalesInfo! Count: {len(sales)}")
                        if len(sales) > 0:
                            print(f"  Latest Sale: {sales[0].get('SaleValue')} on {sales[0].get('SaleYear')}")
                            # Print one full sale record for reference
                            print(json.dumps(sales[0], indent=2))
                        else:
                            print("  SalesInfo is empty.")
                        
                        # We found the working URL pattern
                        print(f"  WORKING URL PATTERN: {url}")
                        quit()
                    else:
                        print("  JSON returned but no SalesInfo key.")
                except Exception as e:
                    print(f"  Not JSON: {str(e)}")
        except Exception as e:
            print(f"  Error: {e}")

print("Done.")
