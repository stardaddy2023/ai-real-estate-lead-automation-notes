# Component Spec: Deal Detail UI (Phase 2)

> [!IMPORTANT]
> **Role:** ARCHITECT
> **Target System:** Frontend (Next.js)
> **Purpose:** The "Underwriting Dashboard" for a specific lead.

## 1. Architecture
*   **Route:** `/leads/[id]`
*   **Page:** `app/leads/[id]/page.tsx`
*   **Data Source:** `GET /api/v1/leads/{id}`

## 2. UI Layout (The "Co-Pilot" View)

### Section A: Header
*   **Title:** Address (Large Bold).
*   **Badges:** Status, Distress Score.
*   **Actions:** "Save", "Archive", "Generate Offer".

### Section B: The "Eye" (Visuals)
*   **Component:** `PhotoGrid.tsx`
    *   Display property images (placeholder if none).
    *   "Analyze Photos" button (triggers Vision Service).

### Section C: The "Brain" (Financials)
*   **Component:** `DealMetrics.tsx`
    *   **ARV (After Repair Value):** Editable Input.
    *   **Repair Estimate:** Editable Input (pre-filled by Vision AI).
    *   **Offer Price:** Calculated field (`ARV * 0.7 - Repairs`).

### Section D: The "Map"
*   **Component:** `PropertyMap.tsx` (Google Maps Embed).

## 3. Data Integration
*   **Fetch:** `useSWR('/api/v1/leads/' + id)`
*   **Update:** Autosave on field blur (optional) or "Save" button.

## 4. Development Plan (PIXEL)
1.  **Scaffold:** Create the dynamic route page.
2.  **Components:** Build `PhotoGrid`, `DealMetrics` (using Shadcn Cards).
3.  **State:** Use local state for the Calculator logic (ARV/Repairs/Offer).
