"""
Test HomeHarvest with different parameters to find fastest approach
"""
import time
from homeharvest import scrape_property

TEST_ADDR = "331 E BLACKLIDGE DR, TUCSON, AZ 85705"

print("Testing different HomeHarvest approaches...")
print("=" * 50)

# Test 1: for_sale (fast but may not have data)
print("\n1. listing_type='for_sale'")
start = time.time()
try:
    df = scrape_property(location=TEST_ADDR, listing_type="for_sale")
    elapsed = time.time() - start
    print(f"   Result: {len(df) if not df.empty else 0} rows ({elapsed:.2f}s)")
    if not df.empty:
        print(f"   Columns: {list(df.columns)[:10]}...")
except Exception as e:
    print(f"   ERROR: {e}")

# Test 2: for_rent (probably empty for most)
print("\n2. listing_type='for_rent'")
start = time.time()
try:
    df = scrape_property(location=TEST_ADDR, listing_type="for_rent")
    elapsed = time.time() - start
    print(f"   Result: {len(df) if not df.empty else 0} rows ({elapsed:.2f}s)")
except Exception as e:
    print(f"   ERROR: {e}")

# Test 3: sold with past_days=30 (much fewer results)
print("\n3. listing_type='sold', past_days=30")
start = time.time()
try:
    df = scrape_property(location=TEST_ADDR, listing_type="sold", past_days=30)
    elapsed = time.time() - start
    print(f"   Result: {len(df) if not df.empty else 0} rows ({elapsed:.2f}s)")
except Exception as e:
    print(f"   ERROR: {e}")

# Test 4: sold with past_days=365 (1 year)
print("\n4. listing_type='sold', past_days=365")
start = time.time()
try:
    df = scrape_property(location=TEST_ADDR, listing_type="sold", past_days=365)
    elapsed = time.time() - start
    print(f"   Result: {len(df) if not df.empty else 0} rows ({elapsed:.2f}s)")
except Exception as e:
    print(f"   ERROR: {e}")

# Test 5: Check what columns contain useful data
print("\n5. Checking useful columns from for_sale result...")
try:
    df = scrape_property(location=TEST_ADDR, listing_type="for_sale")
    if not df.empty:
        row = df.iloc[0]
        useful_cols = ['beds', 'full_baths', 'sqft', 'year_built', 'lot_sqft', 
                      'estimated_value', 'estimate', 'price', 'assessed_value',
                      'stories', 'address', 'street']
        for col in useful_cols:
            if col in row.index:
                print(f"   {col}: {row[col]}")
except Exception as e:
    print(f"   ERROR: {e}")

print("\n" + "=" * 50)
print("Done!")
