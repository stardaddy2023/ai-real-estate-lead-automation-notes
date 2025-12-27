from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.services.market_scout_service import MarketScoutService, HeatmapPoint

router = APIRouter()

@router.get("/heatmap", response_model=List[HeatmapPoint])
async def get_heatmap_data(county_fips: str = "04019"):
    """
    Get heatmap data for market analysis.
    Defaults to Pima County (04019).
    """
    service = MarketScoutService()
    return service.get_heatmap_data(county_fips)
