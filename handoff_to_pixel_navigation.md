# Task Brief: Implement Dashboard Navigation

> [!IMPORTANT]
> **To:** PIXEL (Frontend Engineer)
> **From:** ARCHITECT
> **Priority:** High (UX Core)

## Objective
Make the Sidebar functional. Clicking items should change the main view.

## Instructions
1.  **Refactor Dispositions:**
    *   Create `frontend/src/components/dispositions/DispositionsDashboard.tsx`.
    *   Copy logic from `frontend/src/app/dispositions/page.tsx`.
    *   *Note:* The current page uses `async/await` server fetching. Convert this to `useQuery` (client-side) or pass data as props. For now, **mock the data** or use `useEffect` fetch to keep it simple as a Client Component.

2.  **Update `frontend/src/app/dashboard/page.tsx`:**
    *   Import:
        *   `LeadInbox` from `@/components/leads/lead-inbox`
        *   `DispositionsDashboard` from `@/components/dispositions/DispositionsDashboard`
    *   Update the `activeZone` check:
        ```tsx
        switch (activeZone) {
            case 'market_scout': return <MarketScout />;
            case 'leads': return <LeadInbox />;
            case 'crm': return <DispositionsDashboard />; // Mapping 'crm' to Dispositions for now
            case 'analytics': return <AnalyticsView />; // The default view
            default: return <AnalyticsView />;
        }
        ```
    *   *Note:* Move the current "Default Dashboard View" code into a new component `AnalyticsView` to keep `page.tsx` clean.

## Handoff
Mark task `Implement Dashboard Navigation` as `[x]` when done.
