# Task Brief: Build Matchmaker Service (Phase 4)

> [!IMPORTANT]
> **To:** FORGE (Backend Engineer)
> **From:** ARCHITECT
> **Priority:** High (Exit Strategy Backend)

## Objective
Implement the **Matchmaker Service** to find buyers for our contracted leads.

## References
*   **Spec:** [matchmaker_spec.md](Build%20Docs/matchmaker_spec.md)

## Instructions
1.  **Service (`app/services/matchmaker_service.py`):**
    *   Implement `find_buyers(lead_id)`.
    *   **Logic:**
        *   Load a static list of buyers (Mock Data is fine).
        *   Compare Lead Price vs Buyer Max Price.
        *   Compare Lead Zip vs Buyer Target Zips.
        *   Return the top matches.
    *   *Note:* You can skip full Vector Search for now if simple logic works better for the MVP.

2.  **Endpoint (`app/api/endpoints/dispositions.py`):**
    *   `GET /api/v1/dispositions/matches?lead_id={id}`.
    *   Return the list of `BuyerMatch` objects.

## Handoff
Mark task `Build MATCHMAKER logic` as `[x]` in `task.md` when done.
