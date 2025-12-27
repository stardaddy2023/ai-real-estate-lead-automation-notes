Below is the **Master Architectural Blueprint** that aligns your defined Roles and Workflows into the existing ARELA tech stack (FastAPI + Next.js + Vertex AI).

---

### 1. The Unified System Architecture (ARELA 2.0)

We are restructuring your project into **Five Independent Micro-Services (Departments)** that communicate via the **AI Orchestrator**.

#### The Core Topology

- **The Brain (Orchestrator):** A central `OrchestratorService` in FastAPI. It holds the "State" of every lead.
    
- **The Nervous System:** A Pub/Sub model (or simple Async Event Bus) where agents publish updates (e.g., "Lead #102 Scored") and other agents subscribe (e.g., "Outreach Agent" listens for "High Score").
    
- **The Interface:** Next.js Frontend with a **Global Context Co-Pilot** (Sidebar).
    

![Image of microservices architecture diagram](https://encrypted-tbn3.gstatic.com/licensed-image?q=tbn:ANd9GcTrVC9vBuNmSBCPkRIHQb6DYyZH1N6QwStVAbk6tod91udM5aUR0WQplnaUhcbQXHS5rcdxdcQQ8xWENqsjFCYOGLgF_CXS0NoZWet55Ij2rV5ee3w)

Shutterstock

#### Role-to-Code Alignment Matrix

|**Department**|**Agent Persona**|**ARELA Code Implementation**|
|---|---|---|
|**1. Executive**|**Human CEO**|**Frontend:** `AdminDashboard` (Buy Box Settings).|
||**AI Orchestrator**|**Backend:** `app/services/orchestrator.py` (State Machine).|
|**2. Acquisitions**|**SCOUT**|**Backend:** `app/services/pipeline/scout.py` (GIS Fetch).|
||**BLOODHOUND**|**Backend:** `app/services/pipeline/enrichment.py` (Skip Trace/Recorder).|
||**SIREN**|**Backend:** `app/agents/outreach_agent.py` (Twilio/SendGrid/RVM).|
|**3. Analysis**|**SHERLOCK**|**Backend:** `app/agents/analyst_agent.py` (Comps/Valuation).|
||**REHAB-ESTIMATOR**|**Backend:** `app/services/vision_service.py` (Gemini Pro Vision).|
||**CFO-BOT**|**Backend:** `app/agents/underwriting_agent.py` (KPI/Offer Calc).|
|**4. Transactions**|**SCRIBE**|**Backend:** `app/services/legal_service.py` (Jinja2 Templates -> PDF).|
||**GUARDIAN**|**Backend:** `app/agents/transaction_coordinator.py` (Task Scheduler).|
|**5. Dispositions**|**HYPE-MAN**|**Backend:** `app/agents/marketing_agent.py` (Copywriting).|
||**MATCHMAKER**|**Backend:** `app/services/buyer_matching.py` (Tagging System).|

---

### 2. The Data Flow (Mermaid.js)

This graph visualizes how a "Raw Address" survives the gauntlet to become a "Closed Deal."

Code snippet

```
graph TD
    %% Executive Layer
    CEO(Human CEO) -->|Sets Buy Box| ORCH{AI Orchestrator}

    %% Acquisitions Layer
    subgraph Acquisitions [The Hunter]
        SCOUT[SCOUT: GIS & Code Data] -->|Raw Leads| ORCH
        ORCH -->|Trigger| BLOOD[BLOODHOUND: Skip Trace & Recorder]
        BLOOD -->|Enriched Data| SIREN[SIREN: SMS & RVM]
        SIREN -->|Lead Replies 'Yes'| ORCH
    end

    %% Analysis Layer
    subgraph Analysis [The Architect]
        ORCH -->|Trigger| SHERLOCK[SHERLOCK: ARV & Comps]
        ORCH -->|Trigger| REHAB[REHAB: Vision AI]
        SHERLOCK & REHAB --> CFOBOT[CFO-BOT: Max Allowable Offer]
        CFOBOT -->|Offer Approved| ORCH
    end

    %% Transactions Layer
    subgraph Transactions [The Closer]
        ORCH -->|Trigger| SCRIBE[SCRIBE: Gen LOI/Contract]
        SCRIBE -->|Signed| GUARD[GUARDIAN: Timeline Mgmt]
    end

    %% Dispositions Layer
    subgraph Dispositions [The Cash Register]
        GUARD -->|Clear to Close| HYPE[HYPE-MAN: Write Ad Copy]
        HYPE --> MATCH[MATCHMAKER: Blast Cash Buyers]
    end
```

---

### 3. The Migration Plan

We cannot build all five departments at once. We will deploy them in **Three Strategic Phases** to maintain stability in your current Antigravity environment.

#### Phase 1: The "Smart Hunter" (Acquisitions & Enrichment)

_Goal: Fix the blocked data and automate the "Hunt."_

- **Current Gap:** `Lead Scout` is good, but `Engagement` is mocked and Recorder is blocked.
    
- **Action Plan:**
    
    1. **Upgrade BLOODHOUND:** Implement the **Recorder Bypass**.
        
        - _Tech:_ Add `playwright` to your `requirements.txt`. Create `app/services/scrapers/recorder_stealth.py` to handle the ReCAPTCHA session.
            
    2. **Real Skip Tracing:** Replace `engagement_agent.py` mock with a real API integration (e.g., BatchData or SkipGenie) inside `enrichment.py`.
        
    3. **The "Propensity Score":** Update `analyst_agent.py` to run the 0-100 scoring logic _before_ we pay for skip tracing.
        

#### Phase 2: The "Analytical Architect" (Analysis & Vision)

_Goal: Accurate Offers via Vertex AI._

- **Current Gap:** `Underwriting` is basic math. No Vision AI.
    
- **Action Plan:**
    
    1. **Activate REHAB-ESTIMATOR:** Create a new service that accepts photo URLs. Use `Vertex AI (Gemini Pro Vision)` to identify "Distress Visuals" (tarp on roof, broken windows).
        
    2. **Empower CFO-BOT:** Hardcode your "KPI Sweep" logic into `underwriting_agent.py`. It must accept inputs (ARV, Repairs) and output the MAO (Max Allowable Offer).
        

#### Phase 3: The "Co-Pilot" Interface (Frontend Overhaul)

_Goal: The "Iron Man" HUD._

- **Current Gap:** Standard Dashboard.
    
- **Action Plan:**
    
    1. **Global Sidebar:** Implement a persistent Right Sidebar in Next.js (`layout.tsx`).
        
    2. **Context Bridge:** Create a React Context (`AgentContext`) that feeds the current page state (e.g., "Viewing Lead #101") to the Chat window so the AI knows what you are looking at.
        

---

### 4. Architect's Recommendation: The Immediate Next Step

We must clear the blockage before building the fancy agents. If we can't get Recorder data or Owner Phones, the rest of the system starves.

**I propose we start with Phase 1: Upgrading BLOODHOUND.**

**Shall I generate the `Playwright` code to bypass the Recorder ReCAPTCHA, or would you prefer to integrate the `Skip Trace API` first?**