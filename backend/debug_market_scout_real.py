from app.services.pipeline.market_scout import MarketScoutService
import json

def test_market_scout():
    print("Initializing Market Scout...")
    scout = MarketScoutService()
    
    # Pima County, AZ
    state_fips = "04"
    county_fips = "019"
    market_name = "Tucson (Pima County)"
    
    print(f"Analyzing {market_name}...")
    result = scout.analyze_market(state_fips, county_fips, market_name)
    
    print("\n--- Analysis Result ---")
    print(json.dumps(result, indent=2))
    
    metrics = result.get("metrics", {})
    print("\n--- Verification ---")
    print(f"Unemployment Rate: {metrics.get('unemployment_rate')}% (Should be real number)")
    print(f"Building Permits: {metrics.get('building_permits')} (Should be > 0)")
    print(f"Mortgage Rate: {metrics.get('mortgage_rate')}% (Should be real number)")
    print(f"Population Growth: {metrics.get('population_growth')}% (Should be real number, not 1.5 placeholder)")
    
    dates = result.get("dates", {})
    print("\n--- Dates Verification ---")
    print(f"Unemployment Date: {dates.get('unemployment')}")
    print(f"Permits Date: {dates.get('permits')}")
    print(f"Mortgage Date: {dates.get('mortgage')}")
    print(f"Population Date: {dates.get('population')}")

if __name__ == "__main__":
    test_market_scout()
