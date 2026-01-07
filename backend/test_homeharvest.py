"""
Debug script to test HomeHarvest directly and understand why it's returning 0 results
"""
import time
from homeharvest import scrape_property

TEST_ADDRESSES = [
    "331 E BLACKLIDGE DR, TUCSON, AZ 85705",
    "125 W GLENN ST, TUCSON, AZ 85705",
    "1021 E 9TH ST, TUCSON, AZ 85719",
]

print("Testing HomeHarvest directly...")
print("=" * 50)

for addr in TEST_ADDRESSES:
    print(f"\nAddress: {addr}")
    start = time.time()
    
    try:
        # Test with 'sold' listing type (what the code uses)
        df = scrape_property(
            location=addr,
            listing_type="sold",
            past_days=3650  # 10 years
        )
        elapsed = time.time() - start
        
        if df.empty:
            print(f"  Result: EMPTY DataFrame ({elapsed:.2f}s)")
        else:
            print(f"  Result: Got {len(df)} rows ({elapsed:.2f}s)")
            row = df.iloc[0]
            print(f"    beds: {row.get('beds')}")
            print(f"    baths: {row.get('full_baths')}")
            print(f"    sqft: {row.get('sqft')}")
            print(f"    year_built: {row.get('year_built')}")
            print(f"    estimate: {row.get('estimate')}")
            
    except Exception as e:
        elapsed = time.time() - start
        print(f"  ERROR ({elapsed:.2f}s): {type(e).__name__}: {e}")

print("\n" + "=" * 50)
print("Now testing with 'for_sale' listing type...")

for addr in TEST_ADDRESSES[:1]:  # Just one
    print(f"\nAddress: {addr}")
    start = time.time()
    
    try:
        df = scrape_property(
            location=addr,
            listing_type="for_sale"
        )
        elapsed = time.time() - start
        
        if df.empty:
            print(f"  Result: EMPTY DataFrame ({elapsed:.2f}s)")
        else:
            print(f"  Result: Got {len(df)} rows ({elapsed:.2f}s)")
            
    except Exception as e:
        elapsed = time.time() - start
        print(f"  ERROR ({elapsed:.2f}s): {type(e).__name__}: {e}")

print("\n" + "=" * 50)
print("Done!")
