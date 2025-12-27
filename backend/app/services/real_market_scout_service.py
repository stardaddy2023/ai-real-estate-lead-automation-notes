import pandas as pd
import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()

class RealMarketScoutService:
    def __init__(self):
        self.fred_key = os.getenv("FRED_API_KEY")
        self.census_key = os.getenv("CENSUS_API_KEY")
        self.bls_key = os.getenv("BLS_API_KEY")
        
        # Fallback to hardcoded keys if env vars are missing (TEMPORARY for compatibility with user script)
        if not self.fred_key:
            self.fred_key = '06da43c4ff34b3260240142361c237b6'
        if not self.census_key:
            self.census_key = 'f84b4852a0c872020f8c4f5a6f53cfdc65a78460'

    def get_mortgage_rates(self):
        """Fetch 30-Year Fixed Rate Mortgage Average from FRED."""
        # Direct API call to enforce timeout
        url = "https://api.stlouisfed.org/fred/series/observations"
        params = {
            "series_id": "MORTGAGE30US",
            "api_key": self.fred_key,
            "file_type": "json",
            "sort_order": "desc",
            "limit": 1
        }
        
        try:
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if "observations" in data and data["observations"]:
                    obs = data["observations"][0]
                    rate = float(obs["value"])
                    date = obs["date"]
                    return rate, date
            
            print(f"Error fetching Mortgage Rates: Status {response.status_code}")
            return 7.0, "N/A"
        except Exception as e:
            print(f"Error fetching Mortgage Rates: {e}")
            return 7.0, "N/A" # Fallback conservative estimate

    def get_unemployment_county(self, county_fips, state_fips):
        """
        Fetch County Unemployment Rate from BLS (Bureau of Labor Statistics).
        """
        # Construct BLS Series ID for the county
        # Example: Pima AZ (04019) -> LAUCN040190000000003
        series_id = f"LAUCN{state_fips}{county_fips}0000000003"
        
        # Public URL for BLS (Time Series)
        url = f"https://api.bls.gov/publicAPI/v2/timeseries/data/{series_id}"
        
        headers = {'Content-type': 'application/json'}
        

        payload = {
            "seriesid": [series_id], 
            "startyear": "2024", 
            "endyear": "2025"
        }
        
        if self.bls_key:
            payload["registrationKey"] = self.bls_key
            
        data = json.dumps(payload)
        
        try:
            response = requests.post(url, data=data, headers=headers, timeout=5)
            json_data = response.json()
            
            if 'Results' in json_data and 'series' in json_data['Results']:
                series_data = json_data['Results']['series'][0]['data']
                if series_data:
                    latest = series_data[0]
                    rate = float(latest['value'])
                    period = f"{latest['periodName']} {latest['year']}"
                    return rate, period
            
            print("   No BLS data found (Check FIPS code)")
            return 5.0, "N/A" # Neutral fallback
        except Exception as e:
            print(f"   BLS API Error: {e}")
            return 5.0, "N/A"

    def get_building_permits(self, state_fips, county_fips):
        """
        Fetch New Housing Permits from Census BPS API.
        """
        year = 2024 # Try 2024 first
        url = f"https://api.census.gov/data/{year}/bps/county"
        
        # 'EST': Estimates of total units
        params = {
            'get': 'EST,NAME',
            'for': f'county:{county_fips}',
            'in': f'state:{state_fips}',
            'key': self.census_key
        }
        
        try:
            resp = requests.get(url, params=params, timeout=5)
            if resp.status_code != 200:
                # Fallback to 2023
                year = 2023
                url = f"https://api.census.gov/data/{year}/bps/county"
                resp = requests.get(url, params=params, timeout=5)
                
            if resp.status_code != 200:
                # Fallback to 2022 (Last resort)
                year = 2022
                url = f"https://api.census.gov/data/{year}/bps/county"
                resp = requests.get(url, params=params, timeout=5)

            if resp.status_code == 200:
                data = resp.json()
                # data[0] is header, data[1] is values
                # data[1][0] is the estimate count
                if len(data) > 1:
                    permits = int(data[1][0])
                    return permits, str(year)
            return 0, "N/A"
        except:
            return 0, "N/A"

    def get_population_growth(self, state_fips, county_fips):
        """
        Fetch Population Growth using Census ACS 5-Year Estimates.
        Compares latest available year vs previous year.
        Variable: B01003_001E (Total Population)
        """
        # Try 2024 vs 2023 (if 2024 is out), else 2023 vs 2022
        # Since it's Dec 2025, 2024 ACS might be out (released Dec 2025).
        years_to_try = [2024, 2023]
        
        current_pop = 0
        prev_pop = 0
        used_year = 0
        
        for year in years_to_try:
            url = f"https://api.census.gov/data/{year}/acs/acs5"
            params = {
                'get': 'B01003_001E', # Total Population
                'for': f'county:{county_fips}',
                'in': f'state:{state_fips}',
                'key': self.census_key
            }
            
            try:
                resp = requests.get(url, params=params, timeout=5)
                if resp.status_code == 200:
                    data = resp.json()
                    if len(data) > 1:
                        current_pop = int(data[1][0])
                        used_year = year
                        break
            except Exception as e:
                print(f"Error fetching ACS population for {year}: {e}")
                
        if not current_pop or not used_year:
            print("Could not fetch current population data.")
            return 0.0
            
        # Fetch Previous Year
        prev_year = used_year - 1
        url_prev = f"https://api.census.gov/data/{prev_year}/acs/acs5"
        params['key'] = self.census_key # Ensure key is there
        
        try:
            resp = requests.get(url_prev, params=params, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                if len(data) > 1:
                    prev_pop = int(data[1][0])
        except Exception as e:
            print(f"Error fetching ACS population for {prev_year}: {e}")
            
        if prev_pop > 0:
            growth = ((current_pop - prev_pop) / prev_pop) * 100
            return round(growth, 2), f"{used_year} vs {prev_year}"
            
        return 0.0, "N/A"

    def analyze_market(self, state_fips: str, county_fips: str, market_name: str):
        """
        Analyze a specific market and return a score and report.
        """
        print(f"\nAnalyzing Market: {market_name} ({state_fips}{county_fips})")
        
        score = 0
        
        # 1. UNEMPLOYMENT (Weight: 25%)
        unemp_rate, unemp_date = self.get_unemployment_county(county_fips, state_fips)
        unemp_score = 0
        if unemp_rate < 4.0: unemp_score = 25
        elif unemp_rate < 5.0: unemp_score = 15
        elif unemp_rate < 6.0: unemp_score = 5
        score += unemp_score
        
        # 2. BUILDING PERMITS (Weight: 25%)
        permits, permit_date = self.get_building_permits(state_fips, county_fips)
        permit_score = 0
        if permits > 5000: permit_score = 25
        elif permits > 1000: permit_score = 15
        elif permits > 100: permit_score = 5
        score += permit_score
        
        # 3. MORTGAGE RATES (Weight: 10%)
        rate, rate_date = self.get_mortgage_rates()
        rate_score = 0
        if rate < 6.5: rate_score = 10
        elif rate < 7.5: rate_score = 5
        score += rate_score
        
        # 4. POPULATION GROWTH (Weight: 40%)
        pop_growth_pct, pop_date = self.get_population_growth(state_fips, county_fips)
        pop_score = 0
        if pop_growth_pct > 2.0: pop_score = 40
        elif pop_growth_pct > 1.0: pop_score = 25
        elif pop_growth_pct > 0: pop_score = 10
        score += pop_score
        
        verdict = "COLD (Caution)"
        if score >= 75: verdict = "SCORCHING (Buy Now)"
        elif score >= 50: verdict = "HEALTHY (Look for deals)"

        return {
            "market_name": market_name,
            "score": score,
            "verdict": verdict,
            "metrics": {
                "unemployment_rate": unemp_rate,
                "building_permits": permits,
                "mortgage_rate": rate,
                "population_growth": pop_growth_pct
            },
            "dates": {
                "unemployment": unemp_date,
                "permits": permit_date,
                "mortgage": rate_date,
                "population": pop_date
            },
            "breakdown": {
                "unemployment_score": unemp_score,
                "permit_score": permit_score,
                "rate_score": rate_score,
                "pop_score": pop_score
            }
        }
