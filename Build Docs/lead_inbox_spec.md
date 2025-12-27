# Component Spec: Lead Inbox

> [!IMPORTANT]
> **Role:** ARCHITECT
> **Target System:** Frontend (Next.js)
> **Purpose:** The main dashboard for viewing and managing leads.

## 1. Architecture
*   **Route:** `/leads`
*   **Component:** `LeadInbox.tsx` (or `LeadsTable.tsx`)
*   **Data Source:** `GET /api/v1/leads` (Async)

## 2. UI Requirements

### Visuals
*   **Layout:** Full-width Datagrid.
*   **Columns:**
    1.  **Address:** `address_street` (Bold) + `address_zip`.
    2.  **Status:** Badge (New=Blue, Contacted=Yellow, Offer=Green).
    3.  **Score:** `distress_score` (0-100). Color scale (Red < 50, Green > 80).
    4.  **Owner:** `owner_name` (or "Unknown").
    5.  **Actions:** "Enrich" Button (triggers Skip Trace).

### Interactions
*   **Row Click:** Navigates to `/leads/[id]` (Deal Detail).
*   **Enrich Button:**
    *   Calls `POST /api/v1/leads/[id]/skiptrace`.
    *   Shows loading spinner.
    *   Updates row data on success.

## 3. Data Integration (API Contract)

### Fetching Leads
```typescript
// Interface matching API Contract
interface Lead {
  id: string;
  address_street: string;
  address_zip: string;
  status: string;
  distress_score: number;
  owner_name?: string;
}

// Hook
const { data, error } = useSWR<Lead[]>('/api/v1/leads', fetcher);
```

### Enriching Lead
```typescript
const enrichLead = async (id: string) => {
  await axios.post(`/api/v1/leads/${id}/skiptrace`);
  mutate('/api/v1/leads'); // Re-fetch
};
```

## 4. Development Plan (PIXEL)
1.  **Type Definitions:** Create `types/lead.ts` matching the JSON Spec.
2.  **API Client:** Ensure `lib/api.ts` or `axios` is configured with Base URL.
3.  **Component:** Build `LeadInbox` using a table library (e.g., TanStack Table or Shadcn UI).
4.  **Page:** Create `app/leads/page.tsx`.
