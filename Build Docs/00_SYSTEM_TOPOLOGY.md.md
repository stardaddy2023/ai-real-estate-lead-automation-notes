# ARELA 2.1 System Topology & Stack

## 1. Core Infrastructure (The "Antigravity" Environment)
- **Runtime:** Google Project IDX (Cloud Workstations).
- **Language:** Python 3.12 (Strict Lock due to GeoAlchemy compatibility).
- **Orchestrator:** FastAPI (Async) acting as the central nervous system.
- **Frontend:** Next.js 16.1 (App Router) + React 19.
- **Intelligence:**
  - **Reasoning:** Google Vertex AI (Gemini 3.0 Pro).
  - **Velocity:** Google Vertex AI (Gemini 2.5 Flash).

## 2. Micro-Service Architecture
The application is divided into specific service modules to prevent monolithic bloat.

### A. The Core API (`app/main.py`)
- **Role:** Handles auth, state management, and user requests.
- **Database:** PostgreSQL (Production) / SQLite (Dev) via SQLAlchemy 2.0.

### B. The Swarm Clusters (Agent Logic)
1. **Intelligence Cluster (NEW):**
   - **`Market_Scout`:** Scrapes Migration Data (Census), Job Growth (BLS), and Rental Rates (Zillow/RentCast).
   - **Logic:** Calculates "Price-to-Rent Ratio" and "Absorption Rate."

2. **Acquisitions Cluster:** `Lead_Scout` (GIS), `Bloodhound` (Enrichment), `Siren` (Outreach).
3. **Analysis Cluster:** `Sherlock` (Comps), `Rehab_Vision` (Images), `CFO_Bot` (Underwriting).
4. **Transactions Cluster:** `Lex` (Legal), `Scribe` (Docs), `Guardian` (Coordination).
5. **Dispositions Cluster:** `Hype_Man` (Marketing), `Matchmaker` (Buyer Mapping).

### C. The "Sidecar" Services (Isolated Processes)
To ensure stability, risky operations run in isolated environments.
1. **Recorder MCP Server:**
   - **Tech:** Python + Playwright + Stealth Plugin.
   - **Protocol:** Model Context Protocol (MCP).
   - **Function:** Launches headless Chrome to bypass ReCAPTCHA on County Recorder sites.
   - **Communication:** WebSockets via MCP.