# Service: Pima County Recorder MCP Server

## Objective
Provide a standardized API for agents to request official deed documents, bypassing ReCAPTCHA protections via browser automation.

## Stack
- **Server:** Python `mcp-server` SDK.
- **Engine:** `Playwright` (Chromium).
- **Stealth:** `pip install playwright-stealth`.

## API Definition (Tools)
### 1. `search_recorder_by_name(first, last)`
- **Input:** "John", "Doe"
- **Logic:** Searches grantor/grantee index. Returns list of document IDs.

### 2. `get_document_details(doc_id)`
- **Input:** "2024-1234567"
- **Logic:** Navigates to detail page. Scrapes text. **Detects Mortgage Amount.**

## The "Human-in-the-Loop" Protocol
1. If scraper encounters a CAPTCHA it cannot solve automatically:
2. It sends a "Tool Error" to the Orchestrator: *"CAPTCHA_REQUIRED"*.
3. The UI displays a "Solve CAPTCHA" modal to the user.