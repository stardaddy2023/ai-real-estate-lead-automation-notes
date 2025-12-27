# Task Brief: Build Offer Generator UI (Phase 3)

> [!IMPORTANT]
> **To:** PIXEL (Frontend Engineer)
> **From:** ARCHITECT
> **Priority:** High (Core Transaction Feature)

## Objective
Implement the **Offer Generator Page** to allow users to configure and send offers.

## References
*   **Spec:** [offer_generator_spec.md](Build%20Docs/offer_generator_spec.md)

## Instructions
1.  **Page (`app/leads/[id]/offer/page.tsx`):**
    *   Create a new page accessible from the "Deal Detail" page (add a "Generate Offer" button there if missing).

2.  **Components:**
    *   **OfferForm:** Inputs for Amount, Earnest Money, Closing Date.
    *   **Preview:** A simple text area or div showing a mock contract summary.

3.  **Interaction:**
    *   **"Generate":** Should simulate a delay and show a "Contract Generated" success message.
    *   **"Send":** Should call `POST /api/v1/offers` (ensure this endpoint exists or mock it).

## Handoff
Mark task `Build "Offer Generator" UI` as `[x]` in `task.md` when done.
