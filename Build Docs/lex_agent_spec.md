# Technical Spec: LEX Legal Agent (Phase 3)

> [!IMPORTANT]
> **Role:** ARCHITECT
> **Target System:** Backend (FastAPI + Vector DB)
> **Purpose:** Validate real estate offers against local laws to prevent illegal wholesaling or non-compliant contracts.

## 1. Architecture
*   **Service:** `app.services.lex_service.LexService`
*   **Model:** `gemini-2.5-pro-flash-001` (Reasoning).
*   **Database:** `ChromaDB` (Local Vector Store).
*   **Knowledge Base:** Arizona Real Estate Statutes (Title 32, Chapter 20).

## 2. Logic Flow
1.  **Ingest:** On startup, load `data/laws/arizona_statutes.txt` into ChromaDB (if empty).
2.  **Query:** When checking an offer, search for relevant laws (e.g., "wholesaling disclosure", "earnest money").
3.  **Reason:** Send the Offer Details + Retrieved Laws to Gemini.
4.  **Verdict:** Gemini returns `Approved` (True/False) and `Risk_Analysis` (String).

## 3. API Definition
```python
class LegalReviewResponse(BaseModel):
    approved: bool
    risk_score: int # 0-100 (100 = High Risk)
    flagged_issues: List[str]
    compliance_notes: str

async def review_offer(offer_details: dict) -> LegalReviewResponse:
    pass
```

## 4. Implementation Plan (FORGE)
1.  **Setup:** Install `chromadb`, `sentence-transformers`.
2.  **Data:** Create a dummy `arizona_statutes.txt` with key wholesaling disclosure rules.
3.  **Service:** Implement `LexService` with `check_compliance(offer)`.
