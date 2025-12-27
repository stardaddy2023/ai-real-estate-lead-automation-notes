This is the **Master Blueprint & Roadmap** for the ARELA Platform. It consolidates the architecture, the development team, and the execution strategy into a single "Command Center" view.

### **1. The Executive Summary**

- **Objective:** Build an autonomous "Hedge Fund in a Box" that scrapes, analyzes, negotiates, contracts, and sells real estate with human oversight.
    
- **Core Philosophy:** "Antigravity" – Maximum leverage using AI agents to do the heavy lifting (scraping, math, legal checks) while you (CEO) control the "Kill Switch."
    
- **Tech Stack:** Python 3.12 (Backend), Next.js 16 (Frontend), Gemini 2.5 Flash/3.0 Pro (Intelligence), Project IDX (Dev Environment).
    

---

### **2. The "Antigravity" Dev Team (Your Builders)**

![Image of agile software development team roles](https://encrypted-tbn1.gstatic.com/licensed-image?q=tbn:ANd9GcSQ5vbeUPScgYZ82WUpExdYsFpsbU5CfqMYKPSBoOH4nTvXJMRwFGk8cL4bHLPWDd3KXPCZ_8gbtskBg6aj47llyhNkOKty1NPjmhncy6kMAcBGjQU)

Shutterstock

This is the virtual pod you manage inside Project IDX.

- **ARCHITECT (System Design):** The Keeper of the Schema.
    
- **FORGE (Backend):** Python/FastAPI builder. Creates the API & MCP Scraper.
    
- **PIXEL (Frontend):** Next.js/React builder. Creates the "Co-Pilot" Dashboard.
    
- **VECTOR (DevOps):** Cloud/Docker expert. Ensures the server stays up.
    
- **SYNAPSE (AI Ops):** Prompt Engineer. Tunes Gemini 2.5 Flash for speed/accuracy.
    
- **BREAKER (QA):** The Tester. Tries to break the system before users do.
    
- **LEX (Legal AI):** Compliance officer. (Runtime Agent, not a Dev builder).
    

---

### **3. The Master Architecture (The Ecosystem)**

This system is composed of **Five Intelligent Departments** connected by a central Orchestrator.

Code snippet

```
graph TD
    %% The Brain
    Orchestrator{AI ORCHESTRATOR}
    User((CEO / Human)) <-->|Dashboard| Orchestrator

    %% Department 1: Acquisitions
    subgraph "Dept 1: Acquisitions (The Hunter)"
        Scout[SCOUT: GIS Data] --> Orchestrator
        Bloodhound[BLOODHOUND: Skip Trace] --> Orchestrator
        Recorder[MCP Server: Recorder Scraper] <--> Bloodhound
        Siren[SIREN: Outreach/SMS] <--> Orchestrator
    end

    %% Department 2: Analysis
    subgraph "Dept 2: Analysis (The Architect)"
        Sherlock[SHERLOCK: Comps] --> Orchestrator
        Rehab[REHAB: Vision AI] --> Orchestrator
        CFO[CFO-BOT: Underwriting] --> Orchestrator
    end

    %% Department 3: Transactions
    subgraph "Dept 3: Transactions (The Shield)"
        Lex[LEX: Legal Compliance] -->|Veto/Approve| Orchestrator
        Scribe[SCRIBE: Contract Gen] --> Orchestrator
        Guardian[GUARDIAN: Timeline] --> Orchestrator
    end

    %% Department 4: Dispositions
    subgraph "Dept 4: Dispositions (The Cash Register)"
        Hype[HYPE-MAN: Marketing] --> Orchestrator
        Match[MATCHMAKER: Buyer Matching] --> Orchestrator
    end
    
    %% Infrastructure
    subgraph "Infrastructure Layer"
        DB[(PostgreSQL)]
        VectorDB[(Vector Embeddings)]
        Ext_API[External APIs: Twilio, BatchData, Maps]
    end
    
    Orchestrator <--> DB
    Orchestrator <--> VectorDB
    Orchestrator <--> Ext_API
```

---

### **4. The Development Roadmap (Phased Execution)**

We will build this in 4 distinct Sprints to manage complexity.

#### **Phase 1: The "Unblock & Ingest" Sprint (Weeks 1-3)**

**Goal:** Reliable data flow. No more mock data.

- **FORGE:** Build **Recorder MCP Server** (Playwright) to bypass ReCAPTCHA.
    
- **FORGE:** Integrate **BatchData API** for real Skip Tracing.
    
- **ARCHITECT:** Finalize `PostgreSQL` schema (Lead, Owner, Property tables).
    
- **PIXEL:** Build the "Lead Inbox" UI (Datagrid with "Enrich" button).
    
- **Deliverable:** A live system where you input a Zip Code, and it spits out enriched leads with Phone Numbers and Mortgage info.
    

#### **Phase 2: The "Brain & Vision" Sprint (Weeks 4-6)**

**Goal:** Automated Valuation.

- **SYNAPSE:** Tune **CFO-BOT** prompts to accurately calculate MAO (Max Allowable Offer).
    
- **FORGE:** Build `vision_service.py` to let **Gemini Pro Vision** analyze property photos.
    
- **PIXEL:** Build the "Deal Detail" panel (Photos, Map, Financial Calculator).
    
- **Deliverable:** You click a lead, and the system tells you: _"Buy this for $210k. Repairs estimate: $40k. Profit: $35k."_
    

#### **Phase 3: The "Shield & Sword" Sprint (Weeks 7-9)**

**Goal:** Safe, Legal Offers & Contracts.

- **ARCHITECT:** Deploy **LEX** (Legal Agent) with a Vector DB of Arizona Real Estate Laws.
    
- **FORGE:** Build **SCRIBE** (PDF Generation) using Jinja2 templates.
    
- **PIXEL:** Build the "Offer Generator" UI (Review -> Approve -> Send).
    
- **Deliverable:** You click "Approve," and the system generates a legally compliant LOI/Contract and emails it.
    

#### **Phase 4: The "Cash Register" Sprint (Weeks 10-12)**

**Goal:** Exit Strategy (Dispositions).

- **FORGE:** Build **MATCHMAKER** logic (Vector matching Deals to Buyers).
    
- **PIXEL:** Build the "Marketing Dashboard" (Email blast stats).
    
- **VECTOR:** Dockerize the entire stack and deploy to Google Cloud Run for production stability.
    
- **Deliverable:** Signed contracts are automatically packaged and blasted to your cash buyers list.
    

---

### **5. Immediate Action Plan**

We are starting Phase 1.

Ticket #001: Create the Recorder MCP Server.

Assignee: FORGE & VECTOR.

