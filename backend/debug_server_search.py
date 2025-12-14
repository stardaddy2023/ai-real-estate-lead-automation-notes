import requests
import json

def test_server_search():
    url = "http://localhost:8000/scout/search"
    payload = {
        "zip_code": "85713",
        "distress_type": "absentee_owner",
        "limit": 500,
        "property_types": []
    }
    
    print(f"Testing POST {url} with payload: {payload}")
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Success! Returned {len(data)} leads")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Connection Failed: {e}")

if __name__ == "__main__":
    test_server_search()
