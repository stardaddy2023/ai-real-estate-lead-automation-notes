import requests
import json

def check_datasets(year):
    url = f"https://api.census.gov/data/{year}.json"
    print(f"Checking {url}...")
    try:
        resp = requests.get(url)
        if resp.status_code == 200:
            datasets = resp.json()
            print(f"Found {len(datasets)} datasets for {year}")
            if len(datasets) > 0:
                print(f"First item type: {type(datasets[0])}")
                print(f"First item: {datasets[0]}")
            
            # Search for 'bps' or 'pep'
            for d in datasets:
                if isinstance(d, dict):
                    title = d.get('title', '')
                    name = d.get('dataset', [])
                    path = "/".join(name) if isinstance(name, list) else str(name)
                    
                    if 'bps' in title.lower() or 'population estimates' in title.lower():
                        print(f"  - {title} -> {path}")
        else:
            print(f"  Status: {resp.status_code}")
    except Exception as e:
        print(f"  Error: {e}")

if __name__ == "__main__":
    check_datasets(2024)
    check_datasets(2025)
