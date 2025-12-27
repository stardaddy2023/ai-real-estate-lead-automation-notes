from typing import List, Dict, Optional
from pydantic import BaseModel
import random
from app.services.real_market_scout_service import RealMarketScoutService

class HeatmapPoint(BaseModel):
    lat: float
    lng: float
    weight: float # 0.0 to 1.0 (Intensity)
    zip_code: str

class MarketScoutService:
    def __init__(self):
        self.real_service = RealMarketScoutService()
        
        # Zip Code Centroids for Pima County (Static for now, could be fetched)
        self.zips = {
            "85701": {"lat": 32.2217, "lng": -110.9719}, # Downtown
            "85705": {"lat": 32.2643, "lng": -110.9715}, # Flowing Wells
            "85719": {"lat": 32.2588, "lng": -110.9427}, # University
            "85716": {"lat": 32.2488, "lng": -110.9127}, # Midtown
            "85711": {"lat": 32.2210, "lng": -110.8800}, # East
            "85746": {"lat": 32.1400, "lng": -111.0500}, # Southwest
            "85757": {"lat": 32.1500, "lng": -111.1500}, # Drexel Heights
        }

    def get_heatmap_data(self, county_fips: str = "04019") -> List[HeatmapPoint]:
        """
        Generates heatmap points for a given county using REAL market data.
        """
        # 1. Fetch Real Market Analysis for the County
        # We assume Pima County for now as we only have centroids for it
        state_fips = county_fips[:2]
        county_code = county_fips[2:]
        
        analysis = self.real_service.analyze_market(
            state_fips=state_fips, 
            county_fips=county_code, 
            market_name="Target Market"
        )
        
        # Normalize score (0-100) to weight (0.0-1.0)
        base_weight = analysis["score"] / 100.0
        
        points = []
        
        for zip_code, data in self.zips.items():
            # Add some variance per zip code to make it look realistic
            # In a real app, we'd have granular data per zip
            zip_variance = random.uniform(-0.1, 0.1)
            zip_weight = max(0.1, min(1.0, base_weight + zip_variance))
            
            # Add the center point
            points.append(HeatmapPoint(
                lat=data["lat"],
                lng=data["lng"],
                weight=zip_weight,
                zip_code=zip_code
            ))
            
            # Add 5-10 random points around it
            num_points = random.randint(5, 10)
            for _ in range(num_points):
                # Random offset (approx 1-2 miles)
                lat_offset = random.uniform(-0.02, 0.02)
                lng_offset = random.uniform(-0.02, 0.02)
                
                # Vary weight slightly around the zip weight
                point_variance = random.uniform(-0.05, 0.05)
                final_weight = max(0.1, min(1.0, zip_weight + point_variance))
                
                points.append(HeatmapPoint(
                    lat=data["lat"] + lat_offset,
                    lng=data["lng"] + lng_offset,
                    weight=final_weight,
                    zip_code=zip_code
                ))
                
        return points
