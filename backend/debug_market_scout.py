import time
from app.services.pipeline.market_scout import MarketScoutService

def test_market_scout():
    print("Starting Market Scout Debug...")
    service = MarketScoutService()
    
    # Test Pima County (Default)
    state_fips = "04"
    county_fips = "019"
    market_name = "Pima County, AZ"
    
    start_time = time.time()
    
    print(f"\nAnalyzing {market_name}...")
    try:
        result = service.analyze_market(state_fips, county_fips, market_name)
        end_time = time.time()
        
        print("\nAnalysis Complete!")
        print(f"Time taken: {end_time - start_time:.2f} seconds")
        print("\nResult:")
        print(result)
        
    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    test_market_scout()
