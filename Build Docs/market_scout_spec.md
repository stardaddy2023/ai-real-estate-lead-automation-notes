# Technical Spec: Market Scout Service (Phase 0)

> [!IMPORTANT]
> **Role:** ARCHITECT
> **Target System:** Backend (FastAPI)
> **Purpose:** Aggregate market data to identify "Hot Zones" (Zip Codes) for investment.

## 1. Architecture
*   **Service:** `app.services.market_scout_service.MarketScoutService`
*   **Data Sources:**
    *   **Census API:** For demographic data (Median Income, Vacancy Rate).
    *   **Mock Market Data:** For Real Estate trends (Days on Market, Median Price) - *Mocked to avoid scraping blocks during MVP.*

## 2. Logic Flow
1.  **Request:** User selects a County (e.g., "Pima County, AZ").
2.  **Fetch Data:**
    *   Call Census API (or use static data if API key missing) for all Zips in County.
    *   Generate Mock Market Data for each Zip.
3.  **Score:** Calculate a "Heat Score" (0-100) for each Zip.
    *   *Formula:* `(Vacancy * 0.4) + (Low Income * 0.3) + (High Yield * 0.3)`
4.  **Response:** Return list of Zips with coordinates and scores.

## 3. API Definition
```python
class HeatmapPoint(BaseModel):
    zip_code: str
    latitude: float
    longitude: float
    heat_score: float # 0-100
    metrics: dict # { "vacancy": 0.05, "median_price": 350000 }

async def get_heatmap(county_fips: str) -> List[HeatmapPoint]:
    pass
```

## 4. Implementation Plan (FORGE)
1.  **Service:** Implement `MarketScoutService`.
    *   Use `uszipcode` library or a static JSON map for Zip->Lat/Lon conversion.
    *   Implement `_fetch_census_data()` (Mock or Real).
    *   Implement `_calculate_heat_score()`.
2.  **Endpoint:** `GET /api/v1/scout/heatmap`.
