"""
Try for_sale listings on a different address with more photos/details
"""
from homeharvest import scrape_property
import pandas as pd

# Try a few different addresses that might have active listings
ADDRESSES = [
    "3101 N COUNTRY CLUB RD, TUCSON, AZ",  # Larger home
    "6220 E TANQUE VERDE RD, TUCSON, AZ",  # Commercial area
]

print("Testing for_sale listings for more data...")
print("=" * 60)

for addr in ADDRESSES:
    print(f"\nAddress: {addr}")
    df = scrape_property(location=addr, listing_type="for_sale")
    
    if not df.empty:
        row = df.iloc[0]
        print(f"  Got {len(df)} rows")
        
        # Show all non-NA values
        for col in sorted(df.columns):
            val = row[col]
            if pd.notna(val) and str(val) not in ['', 'None', '<NA>']:
                val_str = str(val)[:80]
                print(f"    {col}: {val_str}")
    else:
        print("  EMPTY result")

print("\n" + "=" * 60)
print("Done!")
