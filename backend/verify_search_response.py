import requests
import json

url = "http://localhost:8000/scout/search"
payload = {
    "zip_code": "85711",
    "limit": 25,
    "distress_type": ["Absentee Owner"],
    "property_types": ["Single Family"]
}
headers = {
    "Content-Type": "application/json"
}

try:
    print(f"Sending request to {url}...")
    response = requests.post(url, json=payload, headers=headers)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Received {len(data)} items.")
        if len(data) > 0:
            print("First item sample:")
            print(json.dumps(data[0], indent=2))
            
            # Verify ID presence
            if "id" in data[0]:
                print("SUCCESS: 'id' field is present.")
            else:
                print("FAILURE: 'id' field is MISSING.")
    else:
        print(f"Error: {response.text}")

except Exception as e:
    print(f"Exception: {e}")
