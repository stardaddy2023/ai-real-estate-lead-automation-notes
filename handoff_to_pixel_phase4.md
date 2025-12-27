# Task Brief: Build Dispositions Dashboard (Phase 4)

> [!IMPORTANT]
> **To:** PIXEL (Frontend Engineer)
> **From:** ARCHITECT
> **Priority:** Medium (Exit Strategy UI)

## Objective
Implement the **Dispositions Dashboard** to visualize the "Cash Register" phase (selling the deals).

## References
*   **Spec:** [dispositions_ui_spec.md](Build%20Docs/dispositions_ui_spec.md)

## Instructions
1.  **Page (`app/dispositions/page.tsx`):**
    *   Create a dashboard view.
    *   **Left Column:** "Inventory" (Leads ready to sell).
    *   **Right Column:** "Buyer Matches" (Who wants to buy them).

2.  **Components:**
    *   **InventoryCard:** Shows Address, Contract Price, Expected Profit.
    *   **BuyerCard:** Shows Buyer Name, Match Score, "Send Deal" button.

3.  **Data:**
    *   Since the Backend Matchmaker isn't ready, use **Mock Data** for the buyers.
    *   You can fetch real leads from `/api/v1/leads` but filter for a mock "Contracted" status or just use the existing leads.

## Handoff
Mark task `Build "Dispositions Dashboard"` as `[x]` in `task.md` when done.
