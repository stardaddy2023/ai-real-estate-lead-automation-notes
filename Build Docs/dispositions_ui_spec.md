# Component Spec: Dispositions Dashboard (Phase 4)

> [!IMPORTANT]
> **Role:** ARCHITECT
> **Target System:** Frontend (Next.js)
> **Purpose:** The interface for matching "Contracted" leads with Buyers (Exit Strategy).

## 1. Architecture
*   **Route:** `/dispositions`
*   **Page:** `app/dispositions/page.tsx`
*   **Data Source:** `GET /api/v1/dispositions/matches` (Mock for now).

## 2. UI Layout

### Section A: Inventory (Left Col)
*   **Component:** `InventoryList.tsx`
*   **Content:** List of Leads with Status = "Contracted".
*   **Action:** Click to select a lead for matching.

### Section B: Matchmaker (Right Col)
*   **Component:** `BuyerMatches.tsx`
*   **Content:** List of potential buyers for the selected lead.
*   **Metrics:** "Match Score" (0-100%), "Buy Box" fit.
*   **Action:** "Blast to Buyers" (Email trigger).

## 3. Data Integration
*   **Mock Data:** Since the backend Matchmaker isn't built, use mock data:
    ```json
    [
      { "buyer": "Opendoor", "score": 95, "reason": "Buy Box: Phoenix, <$400k" },
      { "buyer": "Local Flipper LLC", "score": 82, "reason": "Bought nearby" }
    ]
    ```

## 4. Development Plan (PIXEL)
1.  **Scaffold:** Create `/dispositions` route.
2.  **Layout:** Two-column layout (Inventory vs Matches).
3.  **Mock:** Hardcode the "Matches" for now to demonstrate the UI flow.
