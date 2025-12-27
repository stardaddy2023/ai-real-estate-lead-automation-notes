# Technical Spec: Heatmap UI (Phase 0)

> [!IMPORTANT]
> **Role:** ARCHITECT
> **Target System:** Frontend (React/Next.js)
> **Purpose:** Visualize "Hot Zones" (Zip Codes) on a map.

## 1. Architecture
*   **Component:** `frontend/src/components/scout/HeatmapView.tsx`
*   **Parent:** `frontend/src/components/scout/MarketScout.tsx`
*   **Data Source:** `GET /api/v1/scout/heatmap` (Returns `[{lat, lng, weight, zip_code}]`)

## 2. UI Design
*   **Visual:** A map (Leaflet) centered on the county (e.g., Tucson, AZ).
*   **Overlays:** Colored circles for each data point.
    *   **Red:** High Score (Hot)
    *   **Green:** Low Score (Cold)
    *   *Note: This is inverse of typical "Red=Bad", here "Red=Hot/Activity".*
*   **Interaction:** Hover over a circle to see the Zip Code and Score.

## 3. Implementation Plan (PIXEL)
1.  **Dependencies:** Install `react-leaflet` and `leaflet`.
    *   `npm install react-leaflet leaflet`
    *   `npm install -D @types/leaflet`
2.  **Component:** Create `HeatmapView.tsx`.
    *   Fetch data from API.
    *   Render `MapContainer`, `TileLayer`, and `CircleMarker` for each point.
3.  **Integration:** Add a "Heatmap" tab to `MarketScout.tsx` to toggle between "Analysis" (Metrics) and "Heatmap" (Map).
