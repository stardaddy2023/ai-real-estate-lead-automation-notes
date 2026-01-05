import requests
from bs4 import BeautifulSoup

url = "https://www.to.pima.gov/propertyInquiry/"
try:
    resp = requests.get(url, timeout=10)
    print(f"Status: {resp.status_code}")
    soup = BeautifulSoup(resp.content, "html.parser")
    
    # Search for "Parcel" text
    print("--- Searching for 'Parcel' ---")
    elements = soup.find_all(string=lambda text: "parcel" in text.lower() if text else False)
    for el in elements:
        print(f"Found text: {el.strip()}")
        parent = el.parent
        print(f"Parent: {parent.name} {parent.attrs}")
        # Print nearby inputs
        inputs = parent.find_all_next("input", limit=3)
        for inp in inputs:
            print(f"  Nearby Input: {inp}")

    # Print all inputs again with more detail
    print("\n--- All Inputs ---")
    inputs = soup.find_all("input")
    for inp in inputs:
        print(f"Input: {inp}")

except Exception as e:
    print(f"Error: {e}")
