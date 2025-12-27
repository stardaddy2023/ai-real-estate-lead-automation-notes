# Task Brief: Build Market Scout Service (Phase 0)

> [!IMPORTANT]
> **To:** FORGE (Backend Engineer)
> **From:** ARCHITECT
> **Priority:** Medium (Market Intelligence)

## Objective
Implement the **Market Scout Service** to power the Heatmap UI.

## References
*   **Spec:** [market_scout_spec.md](Build%20Docs/market_scout_spec.md)

## Instructions
1.  **Service (`app/services/market_scout_service.py`):**
    *   Implement `get_heatmap_data(county_fips)`.
    *   **Data:**
        *   Since we don't have a live Zillow Scraper yet, generate **Mock Data** for market stats (Price, DOM).
        *   If possible, fetch real Zip Codes for the county (or just mock 5-10 zips for "Pima County" like 85701, 85705, 85719).
    *   **Scoring:** Implement the simple scoring logic from the spec.

2.  **Endpoint (`app/api/endpoints/scout.py`):**
    *   `GET /api/v1/scout/heatmap`.
    *   Return `List[HeatmapPoint]`.

## Handoff
Mark task `Build Market_Scout` and `Implement Heatmap Data Endpoint` as `[x]` in `task.md` when done.
