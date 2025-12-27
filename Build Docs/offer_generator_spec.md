# Component Spec: Offer Generator UI (Phase 3)

> [!IMPORTANT]
> **Role:** ARCHITECT
> **Target System:** Frontend (Next.js)
> **Purpose:** The interface for generating and sending legal offers.

## 1. Architecture
*   **Route:** `/leads/[id]/offer`
*   **Page:** `app/leads/[id]/offer/page.tsx`
*   **Data Source:** `POST /api/v1/offers`

## 2. UI Layout

### Section A: Offer Configuration
*   **Component:** `OfferForm.tsx`
*   **Fields:**
    *   **Offer Amount:** (Pre-filled from Deal Detail MAO).
    *   **Earnest Money:** (Default $1,000).
    *   **Closing Date:** (Date Picker, Default +30 days).
    *   **Contingencies:** Checkboxes (Inspection, Financing, Appraisal).

### Section B: Legal Preview
*   **Component:** `ContractPreview.tsx`
*   **Visual:** A read-only view of the generated contract text (or a placeholder PDF viewer).
*   **Status:** "Draft", "Generating...", "Ready".

### Section C: Actions
*   **Buttons:**
    *   "Generate Contract" (Triggers SCRIBE - Mock for now).
    *   "Send Offer" (Triggers Email - Mock for now).

## 3. Data Integration
*   **Submit:**
    ```typescript
    POST /api/v1/offers
    {
      "lead_id": "uuid",
      "offer_amount": 250000,
      "contract_terms": { ... }
    }
    ```

## 4. Development Plan (PIXEL)
1.  **Scaffold:** Create the route `/leads/[id]/offer`.
2.  **Form:** Build `OfferForm` using `react-hook-form` and `zod`.
3.  **State:** Manage the "Draft" vs "Generated" state.
