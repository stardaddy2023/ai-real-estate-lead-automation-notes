"""
Explore all available HomeHarvest columns to find:
- Photos, Pool, Garage, Heating, Cooling, Exterior Walls, Roof Type
"""
from homeharvest import scrape_property
import pandas as pd

TEST_ADDR = "331 E BLACKLIDGE DR, TUCSON, AZ 85705"

print("Exploring HomeHarvest columns...")
print("=" * 60)

# Get a sold listing with more data
df = scrape_property(location=TEST_ADDR, listing_type="sold", past_days=365)

if not df.empty:
    row = df.iloc[0]
    print(f"\nAll columns ({len(df.columns)} total):")
    print("-" * 60)
    
    # Group columns for easier reading
    for col in sorted(df.columns):
        val = row[col]
        # Skip very long values
        if isinstance(val, str) and len(val) > 100:
            val = val[:100] + "..."
        print(f"  {col}: {val}")
    
    print("\n" + "=" * 60)
    
    # Look for specific fields
    interesting_fields = [
        'primary_photo', 'photo', 'photos', 'alt_photos', 'image',
        'pool', 'has_pool', 'swimming_pool',
        'garage', 'garage_sqft', 'parking', 'parking_garage',
        'heating', 'heat', 'heating_cooling',
        'cooling', 'air_conditioning', 'ac',
        'exterior', 'exterior_features', 'construction', 'construction_type',
        'roof', 'roof_type', 'roofing',
        'fireplace', 'fireplaces',
        'hoa', 'hoa_fee',
        'description', 'text',
    ]
    
    print("\nSearching for specific fields:")
    for field in interesting_fields:
        if field in df.columns:
            val = row[field]
            if pd.notna(val) and val not in ['', None, '<NA>']:
                print(f"  FOUND: {field} = {str(val)[:100]}")

print("\nDone!")
