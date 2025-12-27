# Recorder MCP Server Specification

> [!IMPORTANT]
> **Role:** ARCHITECT
> **Target System:** Pima County Recorder (or generic equivalent for Dev)
> **Purpose:** Enable AI Agents to "read" official property deeds.

## 1. Architecture
*   **Type:** Model Context Protocol (MCP) Server
*   **Transport:** Stdio (Standard Input/Output)
*   **Runtime:** Python 3.12 + `mcp` library
*   **Engine:** Playwright (Async) + `playwright-stealth`

## 2. Tool Definitions

### Tool: `search_deeds`
*   **Description:** Search for recorded documents by Owner Name.
*   **Input Schema:**
    ```json
    {
      "owner_name": "string (Last, First or Business Name)",
      "start_date": "string (YYYY-MM-DD, optional)",
      "end_date": "string (YYYY-MM-DD, optional)"
    }
    ```
*   **Output Schema:**
    ```json
    [
      {
        "doc_id": "2024-12345",
        "record_date": "2024-01-15",
        "doc_type": "DEED OF TRUST",
        "grantor": "SMITH JOHN",
        "grantee": "BANK OF AMERICA"
      }
    ]
    ```

### Tool: `get_deed_details`
*   **Description:** Extract full details from a specific document, including mortgage amounts.
*   **Input Schema:**
    ```json
    {
      "doc_id": "string"
    }
    ```
*   **Output Schema:**
    ```json
    {
      "doc_id": "2024-12345",
      "amount": 250000.00,
      "legal_description": "LOT 45 BLK 2...",
      "related_docs": ["2020-98765"]
    }
    ```

## 3. Implementation Logic (FORGE)

### Browser Strategy
1.  **Headless Mode:** False (initially) or True with `stealth`.
2.  **User Agent:** Must rotate or mimic real Desktop Chrome.
3.  **Selectors:** Use robust XPath/CSS selectors (avoid dynamic IDs).

### CAPTCHA Protocol
*   **Detection:** If page contains `iframe[src*="recaptcha"]` or text "Verify you are human".
*   **Action:**
    1.  Take Screenshot `captcha_alert.png`.
    2.  Raise `McpError` with code `CAPTCHA_REQUIRED`.
    3.  (Future) Pause and await human input? For now, just fail gracefully.

## 4. Development Plan
1.  **Setup:** `uv init recorder-mcp` (or standard venv).
2.  **Install:** `mcp`, `playwright`, `beautifulsoup4`.
3.  **Code:** `server.py` implementing the class `RecorderServer`.
4.  **Test:** Create `test_client.py` to invoke tools locally.
