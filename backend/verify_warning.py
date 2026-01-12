import asyncio
import requests

def verify_warning():
    url = "http://127.0.0.1:8000/scout/search"
    
    # Test Case: Vail + Code Violations (Unsupported)
    payload = {
        "city": "Vail",
        "distress_type": ["Code Violations"],
        "limit": 10,
        "skip_homeharvest": True
    }
    
    print(f"Testing Warning with payload: {payload}")
    try:
        res = requests.post(url, json=payload)
        if res.status_code == 200:
            data = res.json()
            if isinstance(data, dict):
                print("Response is a dictionary (Correct).")
                leads = data.get("leads", [])
                warning = data.get("warning")
                print(f"Leads found: {len(leads)}")
                print(f"Warning: {warning}")
                
                if warning and "only available in Tucson" in warning:
                    print("SUCCESS: Warning message received correctly.")
                else:
                    print("FAILURE: Warning message missing or incorrect.")
            else:
                print(f"FAILURE: Response is not a dictionary. Type: {type(data)}")
        else:
            print(f"FAILURE: API returned {res.status_code}")
            print(res.text)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    verify_warning()
