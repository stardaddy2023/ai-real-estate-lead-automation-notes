# Technical Spec: Matchmaker Service (Phase 4)

> [!IMPORTANT]
> **Role:** ARCHITECT
> **Target System:** Backend (FastAPI + ChromaDB)
> **Purpose:** Automatically match "Contracted" leads with the best potential buyers.

## 1. Architecture
*   **Service:** `app.services.matchmaker_service.MatchmakerService`
*   **Database:** `ChromaDB` (Shared with LEX or separate collection).
*   **Model:** `text-embedding-004` (or similar) for vectorizing criteria.

## 2. Logic Flow
1.  **Ingest Buyers:**
    *   Buyers have a "Buy Box" (e.g., "Phoenix, <$400k, 3+ Bed").
    *   Vectorize this Buy Box description.
2.  **Match Lead:**
    *   When a lead status changes to "Contracted", trigger matching.
    *   Vectorize the Lead's attributes (Location, Price, Condition).
    *   Perform a similarity search against the Buyer collection.
3.  **Score:**
    *   Return top 5 buyers with a "Match Score" (Cosine Similarity).

## 3. API Definition
```python
class BuyerMatch(BaseModel):
    buyer_id: str
    buyer_name: str
    match_score: float # 0-100
    match_reason: str

async def find_buyers(lead_id: str) -> List[BuyerMatch]:
    pass
```

## 4. Implementation Plan (FORGE)
1.  **Setup:** Use existing `chromadb` setup.
2.  **Seed Data:** Create a `buyers.json` with 5-10 mock buyers (Opendoor, Offerpad, Local Flippers).
3.  **Service:** Implement `MatchmakerService`.
    *   If Vector DB is too complex for this sprint, a **Rule-Based Matcher** is acceptable (e.g., simple Python `if/else` on Zip Code and Price).
    *   *Architect Note:* For Phase 4 MVP, Rule-Based is preferred for speed.
