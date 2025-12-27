# Technical Spec: Co-Pilot Sidebar ("The Iron Man HUD")

> [!IMPORTANT]
> **Goal:** Create a persistent, context-aware AI sidebar that acts as the user's "Co-Pilot" across the entire application.

## 1. Architecture
The Co-Pilot Sidebar will be a **Global Client Component** integrated into the main `DashboardLayout`.

### Component Structure
```tsx
// src/components/copilot/CoPilotSidebar.tsx
export function CoPilotSidebar() {
  const { isOpen, toggle } = useCoPilotStore();
  // ...
}
```

### State Management (Zustand)
We need a `useCoPilotStore` to manage:
*   `isOpen`: Boolean (Sidebar visibility).
*   `messages`: Array of chat messages (User/AI).
*   `context`: Object containing current page data (e.g., selected Lead ID, Market data).

## 2. UI Design
*   **Position:** Fixed Right Side (collapsible).
*   **Width:** 350px - 400px.
*   **Theme:** Dark/Glassmorphism (distinct from main nav).
*   **Sections:**
    1.  **Header:** Agent Status (e.g., "LEX Online", "CFO-BOT Ready").
    2.  **Chat Stream:** Scrollable area for conversation.
    3.  **Context Panel (Mini):** Shows what the AI is "looking at" (e.g., "Analyzing Lead #123").
    4.  **Input Area:** Text input + "Attach" button.

## 3. Context Bridge
The "Context Bridge" allows the AI to know what's on the screen.
*   **Mechanism:** Pages/Components will use a `useEffect` to update the `useCoPilotStore` with their current data.
    ```tsx
    // Example in LeadDetail.tsx
    useEffect(() => {
      setContext({ type: 'lead', data: lead });
    }, [lead]);
    ```

## 4. Implementation Steps (PIXEL)
1.  **Create Store:** `src/store/copilot-store.ts`.
2.  **Build Component:** `src/components/copilot/CoPilotSidebar.tsx`.
3.  **Integrate Layout:** Add to `src/app/dashboard/layout.tsx` (Right side).
4.  **Add Toggle:** Add a button in the main Header to toggle the Co-Pilot.
