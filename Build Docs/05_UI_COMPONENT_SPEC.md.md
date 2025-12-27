# UI Component Specification (Frontend)

## 1. Module 1: Market Intelligence (The Hunter)
- **Page:** `/market-map`
- **Visuals:**
  - **Heatmap Layer:** Colored polygons (Red=Seller Market, Green=Buyer Market).
  - **Layered Filters:** Toggle switches for "Absentee Owner", "Vacant", "Tax Liens".

## 2. Module 2: Lead Analysis (The Scorer)
- **Page:** `/leads`
- **Visuals:**
  - **Sortable List:** Columns for "Propensity Score".
  - **Highlighting:** Rows with Score > 90 are highlighted Green.

## 3. Module 3: Outreach (The Engager)
- **Page:** `/campaigns`
- **Visuals:**
  - **Kanban Board:** Columns (New, Attempted, Responded, Contract).
  - **Unified Inbox:** Merges SMS, Email, and Call logs into one chat thread.

## 4. Module 4: Underwriting (The Architect)
- **Page:** `/deal/[id]`
- **Visuals:**
  - **Deal Dashboard:** - **Top:** Cards for ARV, Profit Spread, ROI.
    - **Middle:** Interactive Calculator (Slider for Rehab Budget).
    - **Bottom:** "Generate Offer" Button.

## 5. Module 5: Transactions (The Closer)
- **Component:** `TransactionTracker.tsx`
- **Visual Style:** "Domino's Pizza Tracker" (Steps: Title Search -> Inspection -> Clear to Close).

## 6. Global: Co-Pilot Sidebar
- **Component:** `AgentSidebar.tsx`
- **Behavior:** Context-aware chat that persists on the right side of the screen.