import requests
import os
from dotenv import load_dotenv

load_dotenv()

CENSUS_KEY = os.getenv("CENSUS_API_KEY") or 'f84b4852a0c872020f8c4f5a6f53cfdc65a78460'

def test_population_api(year):
    print(f"\nTesting Population API for {year}...")
    # Using PEP (Population Estimates Program)
    # https://api.census.gov/data/2019/pep/population
    # Note: Endpoint structure changes sometimes.
    # For 2020+, it might be 'pep/population' or similar.
    
    url = f"https://api.census.gov/data/{year}/pep/population"
    params = {
        'get': 'POP,NAME',
        'for': 'county:019', # Pima County
        'in': 'state:04',    # Arizona
        'key': CENSUS_KEY
    }
    
    try:
        resp = requests.get(url, params=params)
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            print(f"Response: {resp.json()}")
            return True
        else:
            print(f"Error: {resp.text}")
            return False
    except Exception as e:
        print(f"Exception: {e}")
        return False

def test_permits_api(year):
    print(f"\nTesting Permits API for {year}...")
    url = f"https://api.census.gov/data/{year}/bps/county"
    params = {
        'get': 'EST,NAME',
        'for': 'county:019',
        'in': 'state:04',
        'key': CENSUS_KEY
    }
    
    try:
        resp = requests.get(url, params=params)
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            print(f"Response: {resp.json()}")
            return True
        else:
            print(f"Error: {resp.text}")
            return False
    except Exception as e:
        print(f"Exception: {e}")
        return False

if __name__ == "__main__":
    # Test recent years
    for y in [2025, 2024, 2023]:
        test_population_api(y)
        test_permits_api(y)
