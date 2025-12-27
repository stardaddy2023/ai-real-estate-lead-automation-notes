import requests
import json

def verify_api():
    url = "http://localhost:8000/scout/search"
    payload = {
        "zip_code": "85711",
        "limit": 5
    }
    
    try:
        print(f"Sending request to {url} with payload {payload}")
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            print(f"Received {len(data)} results")
            if len(data) > 0:
                first = data[0]
                print("First Result Keys:", first.keys())
                print(f"Lat: {first.get('latitude')} ({type(first.get('latitude'))})")
                print(f"Lng: {first.get('longitude')} ({type(first.get('longitude'))})")
                print(f"Full Object: {json.dumps(first, indent=2)}")
            else:
                print("No results returned")
        else:
            print(f"Error: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    verify_api()
