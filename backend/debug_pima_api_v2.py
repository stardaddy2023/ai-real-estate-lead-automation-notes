import requests
import json

# Target Parcel from user's JSON (131121240) and original (106020300)
parcels = ["131121240", "106020300"]

# Potential endpoints
urls = [
    "https://www.asr.pima.gov/api/Parcel/GetParcel",
    "https://www.asr.pima.gov/api/Parcel/Get",
    "https://www.asr.pima.gov/Parcel/Detail/GetParcel",
    "https://www.asr.pima.gov/Parcel/GetParcelData",
    "https://asr.pima.gov/api/Parcel/GetParcel"
]

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": "https://www.asr.pima.gov/Parcel/Detail?parcel=131121240"
}

print("Probing API endpoints with AJAX headers...")

for parcel in parcels:
    print(f"\n--- Testing Parcel {parcel} ---")
    for base_url in urls:
        # Try query param styles
        test_urls = [
            f"{base_url}?parcel={parcel}",
            f"{base_url}/{parcel}"
        ]
        
        for url in test_urls:
            try:
                # print(f"Trying {url}...", end=" ")
                resp = requests.get(url, headers=headers, timeout=5)
                # print(f"{resp.status_code}")
                
                if resp.status_code == 200:
                    ct = resp.headers.get("Content-Type", "")
                    if "json" in ct.lower():
                        data = resp.json()
                        # Check for unique keys from user's JSON
                        if "Mailing" in data and "SalesInfo" in data:
                            print(f"\n[SUCCESS] Found Endpoint: {url}")
                            print(f"SalesInfo: {json.dumps(data.get('SalesInfo'), indent=2)}")
                            quit() # Exit on first success
                    elif "text/html" in ct.lower() and len(resp.text) < 5000:
                         # Sometimes JSON is returned with text/html content type
                         try:
                             data = resp.json()
                             if "Mailing" in data:
                                 print(f"\n[SUCCESS] Found Endpoint (text/html): {url}")
                                 print(f"SalesInfo: {data.get('SalesInfo')}")
                                 quit()
                         except:
                             pass
            except Exception as e:
                pass

print("\nFinished probing. If no success, we need the URL from the user.")
