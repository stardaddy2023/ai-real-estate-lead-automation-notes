# Task Brief: Build Lead Inbox UI

> [!IMPORTANT]
> **To:** PIXEL (Frontend Engineer)
> **From:** ARCHITECT
> **Priority:** High (Phase 1 Core UI)

## Objective
Implement the **Lead Inbox** (Dashboard) to display leads fetched from the Backend API.

## References
*   **Spec:** [lead_inbox_spec.md](Build%20Docs/lead_inbox_spec.md)
*   **API Contract:** [api_contract.md](file:///C:/Users/stard/.gemini/antigravity/brain/1e8ebc8d-99d2-48cb-a23f-2f59a3946cc2/api_contract.md)

## Instructions
1.  **Types:**
    *   Create `frontend/types/index.ts` (or similar) and define the `Lead` interface matching the API Contract.

2.  **Component (`LeadInbox.tsx`):**
    *   Build a responsive Datagrid/Table.
    *   Columns: Address, Status, Distress Score, Owner, Actions.
    *   **Style:** Use the existing Design System (Tailwind/Shadcn).
    *   **Logic:** Fetch data from `GET /api/v1/leads`.

3.  **Page (`app/leads/page.tsx`):**
    *   Render the `LeadInbox` component.
    *   Ensure it is accessible via the main navigation.

4.  **Interaction:**
    *   Clicking a row should navigate to `/leads/[id]` (even if that page is empty for now).
    *   Add a placeholder "Enrich" button that logs to console (Backend integration for Enrich comes later if not ready).

## Constraints
*   **Strict Types:** No `any`. Use the defined Interfaces.
*   **Mocking:** If the Backend is offline, use a mock JSON file, but ensure the *structure* matches the API Contract exactly.

## Handoff
Once complete, mark the task in `task.md` as `[x]` and notify ARCHITECT.
