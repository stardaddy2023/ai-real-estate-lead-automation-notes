import requests
import json
import datetime

url = "https://www.asr.pima.gov/AssessorSiteData/api/get/parceldetails/"

# Parcels to test
parcels = ["131121240", "106020300"]

headers = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "en-US,en;q=0.9",
    "content-type": "application/x-www-form-urlencoded",
    "origin": "https://www.asr.pima.gov",
    "priority": "u=1, i",
    "sec-ch-ua": '"Not(A:Brand";v="8", "Chromium";v="144", "Google Chrome";v="144"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36"
}

# The body is a JSON string passed as raw data with urlencoded header? 
# This is weird but we will mimic it exactly.
# In requests, `data=string` sends the string as body.

current_year = datetime.datetime.now().year
# cURL used 2025. It's safe to use current year or next year.
tax_year = 2025 

print(f"Testing POST to {url}...")

for parcel in parcels:
    payload_dict = {"parcel": parcel, "taxyear": tax_year}
    # Note: The cURL shows data-raw '{"parcel":"...","taxyear":2025}'
    # It does NOT show key=value. It shows a raw JSON string.
    payload_str = json.dumps(payload_dict)
    
    # However, Python requests might try to urlencode if we pass a dict to `data`.
    # To mimic cURL `data-raw`, we pass the string.
    # But wait, `content-type: application/x-www-form-urlencoded` usually implies key=value.
    # If the server accepts JSON string as the *entire body* despite the header, we must send it raw.
    # Let's try sending keys as equal just in case the cURL was misleading, 
    # BUT request payload in cURL --data-raw is explicit. I will send raw string.
    
    # Actually, looking at the cURL again:
    # --data-raw '{"parcel":"131121240","taxyear":2025}'
    # This sends exactly that string bytes.
    
    print(f"\nRequesting Parcel {parcel}...")
    try:
        # We need to explicitly set data to the string to avoid automatic form-encoding of a dict
        # And let the header claim it is urlencoded (even if it's technically JSON content).
        # This is likely a quirk of their backend parser.
        
        # NOTE: If we get an error, we might try passing `={json}` or similar, but let's trust cURL.
        response = requests.post(url, headers=headers, data=payload_str, timeout=10)
        
        print(f"Status: {response.status_code}")
        # print(f"Response: {response.text[:200]}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                if "SalesInfo" in data:
                    sales = data["SalesInfo"]
                    print(f"SUCCESS! Found {len(sales)} sales records.")
                    if sales:
                        print(f"Latest Sale: {sales[0].get('SaleValue')} (Date: {sales[0].get('SaleMonth')}/{sales[0].get('SaleYear')})")
                else:
                    print(f"JSON parsed but no SalesInfo. Keys: {list(data.keys())}")
            except Exception as e:
                print(f"Response not JSON: {e}")
                print(response.text[:500])
        else:
             print(f"Failed with status {response.status_code}")
             
    except Exception as e:
        print(f"Error: {e}")

