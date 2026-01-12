"""Inspect Homeharvest column names to find source field"""
from homeharvest import scrape_property

df = scrape_property(location="85716", listing_type="for_sale")

print(f"Found {len(df)} listings")
print(f"\nAll columns ({len(df.columns)}):")
print(sorted(df.columns.tolist()))

if not df.empty:
    row = df.iloc[0]
    print("\n--- Sample row values ---")
    for col in sorted(df.columns):
        val = row[col]
        if str(val) not in ['nan', 'None', '', '<NA>']:
            val_str = str(val)[:60]
            print(f"  {col}: {val_str}")
