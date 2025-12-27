# Task Brief: Co-Pilot Sidebar (AI HUD)

> [!IMPORTANT]
> **To:** PIXEL (Frontend Engineer)
> **From:** ARCHITECT
> **Priority:** High (Phase 3 Requirement)

## Objective
Build the **Co-Pilot Sidebar** ("Iron Man HUD") that sits on the right side of the dashboard.

## Instructions
1.  **State Management:**
    *   Create `src/store/copilot-store.ts` (Zustand).
    *   Store `isOpen`, `messages`, and `context`.

2.  **Component (`Co-Pilot Sidebar`):**
    *   Create `src/components/copilot/CoPilotSidebar.tsx`.
    *   **UI:** Fixed right sidebar, 400px width, glassmorphism style.
    *   **Content:** Chat history + Input field.

3.  **Layout Integration:**
    *   Update `src/app/dashboard/layout.tsx`.
    *   Add the `CoPilotSidebar` component to the right of the `children`.
    *   Ensure it pushes content or overlays based on preference (Overlay is usually better for HUD).

4.  **Toggle Button:**
    *   Add a "Co-Pilot" button to the top header (or somewhere visible) to toggle `isOpen`.

## Handoff
Mark task `Build Co-Pilot Sidebar` as `[x]` when done.
