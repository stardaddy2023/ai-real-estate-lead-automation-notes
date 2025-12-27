# Task Brief: Build Deal Detail UI (Phase 2)

> [!IMPORTANT]
> **To:** PIXEL (Frontend Engineer)
> **From:** ARCHITECT
> **Priority:** High (Core UI)

## Objective
Implement the **Deal Detail Page** (`/leads/[id]`) to view property info and calculate offers.

## References
*   **Spec:** [deal_detail_spec.md](Build%20Docs/deal_detail_spec.md)

## Instructions
1.  **Page (`app/leads/[id]/page.tsx`):**
    *   Fetch lead data using the ID from the URL.
    *   Handle "Loading" and "Not Found" states.

2.  **Components:**
    *   **Header:** Address & Status.
    *   **Financials (`DealMetrics`):** Inputs for ARV and Repairs. Calculate "Max Offer" = `(ARV * 0.7) - Repairs`.
    *   **Photos:** Simple grid placeholder.

3.  **Interaction:**
    *   The "Max Offer" should update in real-time as you change ARV or Repairs.

## Handoff
Mark task `Build "Deal Detail" Panel` as `[x]` in `task.md` when done.
