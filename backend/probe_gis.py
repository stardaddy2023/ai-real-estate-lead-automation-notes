import requests

base_urls = [
    "https://gisdata.tucsonaz.gov/server/rest/services",
    "https://maps.tucsonaz.gov/arcgis/rest/services"
]

folders = [
    "Code_Enforcement",
    "CodeEnforcement",
    "Planning",
    "Development",
    "Permits",
    "PublicSafety",
    "Neighborhoods",
    "Property",
    "Violations",
    "OpenData"
]

def probe():
    for base in base_urls:
        print(f"Probing {base}...")
        for folder in folders:
            url = f"{base}/{folder}?f=json"
            try:
                resp = requests.get(url, timeout=5)
                if resp.status_code == 200:
                    # Check if it's JSON and has "services" or "folders"
                    try:
                        data = resp.json()
                        if "services" in data or "folders" in data:
                            print(f"FOUND: {url}")
                            print(data)
                    except:
                        pass
            except Exception as e:
                print(f"Error {url}: {e}")

if __name__ == "__main__":
    probe()
