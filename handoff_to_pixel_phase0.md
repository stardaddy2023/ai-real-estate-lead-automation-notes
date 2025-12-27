# Task Brief: Build Heatmap UI (Phase 0)

> [!IMPORTANT]
> **To:** PIXEL (Frontend Engineer)
> **From:** ARCHITECT
> **Priority:** Medium (Market Intelligence)

## Objective
Implement the **Interactive Heatmap UI** to visualize market data.

## References
*   **Spec:** [heatmap_ui_spec.md](Build%20Docs/heatmap_ui_spec.md)
*   **Existing Code:** `frontend/src/components/scout/MarketScout.tsx`

## Instructions
1.  **Install Dependencies:**
    *   `npm install react-leaflet leaflet`
    *   `npm install -D @types/leaflet`
    *   *Note: If `npm install` fails on Windows, try `npm install --legacy-peer-deps`.*

2.  **Create Component (`frontend/src/components/scout/HeatmapView.tsx`):**
    *   Fetch data from `http://localhost:8000/api/v1/scout/heatmap`.
    *   Render a Leaflet Map centered on Tucson (Lat: 32.22, Lng: -110.97).
    *   Map `weight` (0.0-1.0) to Opacity or Color Intensity.

3.  **Integrate:**
    *   Update `MarketScout.tsx` to include a Tab/Toggle: "Market Report" vs "Heatmap".
    *   Render `HeatmapView` when "Heatmap" is selected.

## Handoff
Mark task `Build Interactive Heatmap UI` as `[x]` in `task.md` when done.
