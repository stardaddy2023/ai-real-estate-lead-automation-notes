**ARCHITECT ONLINE.**

We are pivoting to the **PropStream-Inspired UI Strategy**. PropStream is the gold standard because it balances density (lots of data) with clarity (easy filtering).

This design document outlines the Frontend Architecture for **ARELA (AI Real Estate Lead Automation)**, merging your "Google Swarm" backend with a high-performance React/Next.js frontend.

### **Frontend Design Document: ARELA Dashboard**

**Objective:**
Create a "Single Pane of Glass" for real estate acquisitions. The user should never have to leave this dashboard to find, filter, or close a deal.

**Core Philosophy:**
* **Map-First:** The map is the primary interface, not a list.
* **Dense Data:** Show key metrics (Equity, MLS Status, Distress) immediately without clicking.
* **One-Click Actions:** "Skip Trace", "Send SMS", and "Run Comps" should be accessible directly from the property card.

---

### **1. The Layout Architecture (The "PropStream" Flow)**

The application is divided into four primary zones.



**Zone A: The Command Center (Left Sidebar)**
* **Purpose:** Navigation between high-level modules.
* **Items:**
    1.  **Search (Map):** The default view.
    2.  **My Properties (CRM):** Leads you have saved/favorited.
    3.  **Contacts:** List of owners you are engaging.
    4.  **Campaigns:** SMS/Voice marketing stats.
    5.  **Analytics:** "The Watchtower" metrics (API costs, success rates).
    6.  **Settings:** API Keys, Team Management.

**Zone B: The Filter Engine (Top Bar)**
* **Purpose:** Rapidly slice the data. This is the "Filter Agent" interface.
* **Key Filters (Dropdowns with Counters):**
    * **Location:** County, City, Zip.
    * **Property Characteristics:** Bed/Bath, SqFt, Lot Size, Year Built.
    * **MLS Status:** On Market, Off Market, Failed Listing.
    * **Pre-Foreclosure:** NOD (Notice of Default), Auction Date.
    * **Liens:** Tax Liens, HOA Liens, Mechanic's Liens.
    * **Valuation:** Est. Value, Est. Equity %, Mortgage Balance.
    * **Ownership:** Owner Occupied vs. Absentee, Corporate Owned, Years Owned.
* **"Quick Lists" (Preset Filters):**
    * "High Equity Vacants"
    * "Tired Landlords" (Owned >10yrs + Absentee)
    * "Flippers" (Cash Buyers who bought in last 6mo)

**Zone C: The Map Canvas (Center Stage)**
* **Technology:** React-Leaflet or Mapbox GL JS.
* **Features:**
    * **Pins:** Color-coded by status (Red = Pre-Foreclosure, Green = High Equity, Blue = Cash Buyer).
    * **Clustering:** Groups pins at high zoom levels to prevent clutter.
    * **Polygon Tool:** "Draw" a circle or square around a neighborhood to select all properties inside.
    * **Hover Cards:** Hovering over a pin shows a mini-card: Address, Est. Equity, Last Sale Date.

**Zone D: The Property Detail Panel (Slide-out Right)**
* **Trigger:** Clicking a pin or list item opens this panel (does not leave the page).
* **Tabs:**
    1.  **Details:** Property specs, photos (Google Street View), tax info.
    2.  **Comps & AV:** Automated Valuation Model (AVM) and comparable sales list.
    3.  **Tax & Mortgage:** Loan balances, lien history.
    4.  **Documents:** Foreclosure filings, deeds.
    5.  **Agent Actions:**
        * **"Run AI Analysis":** Triggers the *Underwriting Agent*.
        * **"Skip Trace":** Triggers the *Engagement Agent* to find phone numbers.
        * **"Send Campaign":** Adds to SMS/Voice queue.

---

### **2. User Stories & Interaction Flows**

**Flow 1: The "Driving for Dollars" Virtual Tour**
1.  User selects "Pima County" and clicks "Vacant" filter.
2.  Map updates to show 500 red pins.
3.  User draws a polygon around "Downtown Tucson".
4.  Map filters to 45 pins.
5.  User clicks "Select All" -> "Add to List: Tucson Vacants".

**Flow 2: The "Deep Dive" Underwrite**
1.  User clicks a specific property pin.
2.  Right panel slides out.
3.  User clicks **"AI Underwrite"**.
4.  *The Analyst Agent* runs in the background (spinner icon).
5.  Panel updates with:
    * **ARV:** $450,000
    * **Repairs:** $45,000 (Based on age/condition)
    * **MAO (Max Allowable Offer):** $290,000
    * **Strategy:** "Fix and Flip" (High confidence)

**Flow 3: The "Blast" Campaign**
1.  User goes to "My Properties" -> "Tucson Vacants" list.
2.  Selects 10 leads.
3.  Clicks "Skip Trace" ($0.12/record).
4.  Wait for completion notification.
5.  Clicks "Start Campaign" -> Selects "Cold SMS Sequence #1".
6.  *The Engagement Agent* takes over and starts messaging.

---

### **3. Technical Specs for the Frontend**

**Framework:** Next.js 14 (App Router)
* **Why:** Server-Side Rendering (SSR) for fast initial load of heavy data. SEO friendly (if public).

**Styling:** Tailwind CSS + shadcn/ui
* **Why:** `shadcn/ui` provides beautiful, accessible components (Data Tables, Dialogs, Dropdowns) that look professional out of the box. It mimics the clean, "SaaS" look of Linear or Vercel.

**State Management:** TanStack Query (React Query) + Zustand
* **Why:**
    * **TanStack Query:** Handles caching the massive property datasets. If you zoom out and zoom back in, it remembers the data so it doesn't re-fetch.
    * **Zustand:** Manages global UI state (e.g., "Is the filter panel open?", "Which property is selected?").

**Maps:** Mapbox GL JS (or React-Map-GL)
* **Why:** Much faster than Google Maps for thousands of markers. Allows custom styling (e.g., "Satellite View" for roof inspection).

**Data Visualization:** Recharts
* **Why:** For the "Watchtower" analytics (Line charts for spending, Bar charts for lead conversion).

---

### **4. Implementation Roadmap (Frontend)**

**Phase 1: The Skeleton**
* Set up Next.js project.
* Install Tailwind + shadcn/ui.
* Build the App Shell (Sidebar + Top Bar layout).

**Phase 2: The Map Core**
* Integrate Mapbox.
* Connect to the `get_properties` API endpoint.
* Render pins based on Lat/Long from the database.

**Phase 3: The Detail Panel**
* Build the slide-out component.
* Create the "Property Card" displaying data from the API.
* Add the "Run AI Analysis" button (mocked at first).

**Phase 4: The Filters**
* Build the top bar dropdowns.
* Connect them to API query parameters (`?county=Pima&min_equity=50`).

