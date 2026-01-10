
import requests

def probe_api():
    parcel_id = "117023950"
    endpoints = [
        f"https://asr.pima.gov/api/parcel/{parcel_id}",
        f"https://asr.pima.gov/api/v1/parcel/{parcel_id}",
        f"https://asr.pima.gov/api/parcels/{parcel_id}",
        f"https://asr.pima.gov/Parcel/Details/{parcel_id}",
        f"https://asr.pima.gov/api/search/{parcel_id}"
    ]
    
    for url in endpoints:
        print(f"Probing {url}...")
        try:
            resp = requests.get(url, timeout=5)
            print(f"Status: {resp.status_code}")
            if resp.status_code == 200:
                try:
                    data = resp.json()
                    print("SUCCESS! JSON Response:")
                    print(str(data)[:200])
                    return
                except:
                    print("Response is not JSON")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    probe_api()
