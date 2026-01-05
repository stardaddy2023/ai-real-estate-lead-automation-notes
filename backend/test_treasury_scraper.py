import requests
from bs4 import BeautifulSoup

def check_taxes(parcel_id):
    url = "https://www.to.pima.gov/propertyInquiry/"
    session = requests.Session()
    
    # 1. Get CSRF Token
    try:
        resp = session.get(url, timeout=10)
        soup = BeautifulSoup(resp.content, "html.parser")
        csrf_token = soup.find("input", {"name": "csrfmiddlewaretoken"})["value"]
        print(f"Got CSRF: {csrf_token[:10]}...")
    except Exception as e:
        print(f"Error getting CSRF: {e}")
        return

    # 2. Prepare Payload
    # Try to format parcel if needed. Removing dashes for now based on placeholder?
    # Placeholder was 000000000 (9 digits).
    # Pima parcels are often Book-Map-Parcel-Split e.g. 101-01-001A
    # Let's try raw input first.
    
    payload = {
        "csrfmiddlewaretoken": csrf_token,
        "form_statecode": parcel_id,
        "form_asofdate": "01/03/2026" # Using today's date from context
    }
    
    headers = {
        "Referer": url,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    # 3. Post
    try:
        post_resp = session.post(url, data=payload, headers=headers, timeout=10)
        print(f"POST Status: {post_resp.status_code}")
        
        # 4. Analyze Result
        # Dump to file for inspection
        with open("treasury_result.html", "w", encoding="utf-8") as f:
            f.write(post_resp.text)
            
        if "No results found" in post_resp.text:
            print("Result: No results found")
        elif "Total Due" in post_resp.text:
            print("Result: Found Total Due!")
        else:
            print("Result: Unknown response (check treasury_result.html)")
            
    except Exception as e:
        print(f"Error posting: {e}")

# Test with a likely valid parcel (random guess based on standard Pima format)
# 101-01-001A is a common starting point
check_taxes("10101001A") 
