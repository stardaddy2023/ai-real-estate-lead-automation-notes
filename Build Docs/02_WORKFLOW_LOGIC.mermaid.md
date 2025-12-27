graph TD
    %% Phase 0: Macro Intelligence
    User(CEO) -->|Define Strategy: CashFlow vs Flip| MarketScout[Agent: MARKET-SCOUT]
    MarketScout -->|Analyze: Job Growth, RTP, Migration| HeatMap[UI: Heat Map Visualization]
    HeatMap -->|User Selects Target Zip| Scout[Lead Scout]

    %% Phase 1: Ingestion & Enrichment
    Scout -->|Pull Raw Leads| DB[(Database)]
    DB --> Trigger{Enrich?}
    
    Trigger -- Yes --> Bloodhound[Agent: BLOODHOUND]
    
    subgraph "Sidecar: Recorder MCP"
        Bloodhound -->|MCP Request| MCP_Server[Playwright Server]
        MCP_Server -->|Launch Browser| Pima_Site
        MCP_Server -->|Deed Data| Bloodhound
    end
    
    Bloodhound -->|Update Record| DB

    %% Phase 2: Analysis & Offer
    DB --> CFO[Agent: CFO-BOT]
    CFO -->|Proposed Offer| Legal_Queue

    %% Phase 3: The Legal Firewall
    subgraph "Legal & Compliance"
        Legal_Queue --> LEX[Agent: LEX]
        LEX -->|Check: DNC/Fairness| Compliance{Approved?}
        Compliance -- No --> Warning[Alert Human CEO]
    end
    
    Compliance -- Yes --> Scribe[Agent: SCRIBE]
    Scribe -->|Generate PDF| Contract_Out
    
    %% Phase 4: Dispositions
    Contract_Out -->|Signed by Seller| Disposition_Queue
    
    subgraph "Dispositions"
        Disposition_Queue --> Hype[Agent: HYPE-MAN]
        Hype -->|Ad Copy + Photos| Marketing_Pack
        Marketing_Pack --> Match[Agent: MATCHMAKER]
        Match -->|Query Buyers| Buyer_List[(Cash Buyers DB)]
        Match -->|Email Blast| Sold[Deal Closed]
    end