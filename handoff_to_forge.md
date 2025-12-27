# Task Brief: Build Recorder MCP Server

> [!IMPORTANT]
> **To:** FORGE (Backend Engineer)
> **From:** ARCHITECT
> **Priority:** High (Blocker for Data Ingestion)

## Objective
Implement the **Recorder MCP Server** to enable the Orchestrator to search for property deeds and extract mortgage info.

## References
*   **Spec:** [recorder_mcp_spec.md](Build%20Docs/recorder_mcp_spec.md)
*   **Roadmap:** [implementation_plan.md](file:///C:/Users/stard/.gemini/antigravity/brain/1e8ebc8d-99d2-48cb-a23f-2f59a3946cc2/implementation_plan.md) (Phase 1, Item 3)

## Instructions
1.  **Scaffold Directory:**
    *   Create `backend/mcp_servers/recorder/`.
    *   Create `requirements.txt` with: `mcp`, `playwright`, `playwright-stealth`, `beautifulsoup4`, `python-dotenv`.

2.  **Implement Server (`server.py`):**
    *   Use the `mcp` Python SDK.
    *   Implement the `search_deeds` and `get_deed_details` tools as defined in the Spec.
    *   **Crucial:** Use `playwright-stealth` to avoid detection.
    *   **Error Handling:** If a CAPTCHA is detected, raise an `McpError` with code `CAPTCHA_REQUIRED` (as per Spec).

3.  **Testing:**
    *   Create a simple `test_client.py` that connects to the server via stdio and calls `search_deeds` with a dummy name (or a real one if you have credentials/target).

## Constraints
*   **Do NOT** modify the Spec. If you hit a blocker, report back to ARCHITECT.
*   **Do NOT** hardcode credentials. Use `.env`.

## Handoff
Once complete, mark the task in `task.md` as `[x]` and notify ARCHITECT.
