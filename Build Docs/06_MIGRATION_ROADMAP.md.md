# ARELA Implementation Roadmap

## Phase 0: The "Macro-Scope" (Market Intelligence)
*Goal: Define *where* to hunt before we hunt.*
- **Action:** Build `Market_Scout` to scrape Census/Zillow data.
- **Deliverable:** Interactive Heatmap UI showing "Price-to-Rent" ratios.

## Phase 1: The "Smart Hunter" (Acquisitions & Enrichment)
*Goal: Fix the blocked data and automate the "Hunt."*
- **Current Gap:** `Lead Scout` is good, but `Engagement` is mocked and Recorder is blocked.
- **Action Plan:**
    1. **Upgrade BLOODHOUND:** Implement the **Recorder Bypass** using Playwright.
    2. **Real Skip Tracing:** Replace mock agents with BatchData API integration.
    3. **The "Propensity Score":** Update logic to score leads (0-100) *before* spending money on skip tracing.

## Phase 2: The "Analytical Architect" (Analysis & Vision)
*Goal: Accurate Offers via Vertex AI.*
- **Current Gap:** `Underwriting` is basic math. No Vision AI.
- **Action Plan:**
    1. **Activate REHAB-ESTIMATOR:** Build service to accept photo URLs and identify distress visuals (tarps, broken windows).
    2. **Empower CFO-BOT:** Hardcode "KPI Sweep" logic (1% Rule, MAO) into the agent.

## Phase 3: The "Co-Pilot" Interface (Frontend Overhaul)
*Goal: The "Iron Man" HUD.*
- **Current Gap:** Standard Dashboard.
- **Action Plan:**
    1. **Global Sidebar:** Implement persistent "Co-Pilot" sidebar in Next.js.
    2. **Context Bridge:** Connect `AgentContext` so the AI "sees" what you see on screen.

## Phase 4: The "Cash Register" (Dispositions)
*Goal: Exit Strategy.*
- **Action:** Build `Matchmaker` agent and `Cash_Buyers` vector database.
- **Deliverable:** Automated email blasts to buyers when a contract is signed.