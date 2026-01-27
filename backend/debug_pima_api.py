import requests
import json

base_urls = [
    "https://asr.pima.gov/api",
    "https://www.asr.pima.gov/api",
    "https://asr.pima.gov/Parcel/api",
]

endpoints = [
    "/Parcel/GetParcel?parcel=106020300",
    "/Parcel/Get?parcel=106020300",
    "/Parcel/Detail?parcel=106020300&format=json",
    "/Sales/Get?parcel=106020300",
    "/val/GetValuation?parcel=106020300"
]

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.asr.pima.gov/Parcel/Detail?parcel=106020300"
}

print("Probing API endpoints...")

for base in base_urls:
    for ep in endpoints:
        url = f"{base}{ep}"
        print(f"Trying {url}...", end=" ")
        try:
            resp = requests.get(url, headers=headers, timeout=5)
            print(f"Status: {resp.status_code}")
            if resp.status_code == 200:
                ct = resp.headers.get("Content-Type", "")
                print(f"  Content-Type: {ct}")
                if "json" in ct:
                    try:
                        data = resp.json()
                        print("  JSON SUCCESS!")
                        print(str(data)[:200])
                        # If meaningful, stop?
                        if "106020300" in str(data) or "74000" in str(data):
                            print("  MATCH FOUND!")
                    except:
                        pass
        except Exception as e:
            print(f"Error: {e}")
