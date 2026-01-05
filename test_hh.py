from homeharvest import scrape_property
import pandas as pd
from datetime import datetime

def test_hh():
    address = "123 S Stone Ave, Tucson, AZ 85701"
    print(f"Scraping {address}...")
    
    try:
        properties = scrape_property(
            location=address,
            listing_type="sold",
            past_days=3650
        )
        
        if not properties.empty:
            print(f"Found {len(properties)} results.")
            print(properties.iloc[0])
        else:
            print("No results found.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_hh()
