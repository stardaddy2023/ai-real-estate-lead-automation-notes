# Technical Spec: Vision Service (Phase 2)

> [!IMPORTANT]
> **Role:** ARCHITECT
> **Target System:** Backend (FastAPI + Gemini)
> **Purpose:** Analyze property photos to estimate rehab costs automatically.

## 1. Architecture
*   **Service:** `app.services.vision_service.VisionService`
*   **Model:** `gemini-2.5-pro-flash` (or latest available).
*   **Input:** List of Image URLs (strings).
*   **Output:** Structured JSON (Repair Estimate).

## 2. API Definition

### Function Signature
```python
async def analyze_property_photos(photo_urls: List[str]) -> PropertyConditionReport:
    pass
```

### Data Models (Pydantic)
```python
class DetectedIssue(BaseModel):
    category: str # e.g., "Roof", "Flooring", "Kitchen"
    description: str
    severity: str # "Low", "Medium", "High"
    estimated_cost: float

class PropertyConditionReport(BaseModel):
    overall_condition: str # "Poor", "Fair", "Good", "Excellent"
    detected_issues: List[DetectedIssue]
    total_repair_estimate: float
    confidence_score: float
```

## 3. Implementation Logic (FORGE)
1.  **Prompt Engineering:**
    *   System Prompt: "You are an expert Construction Estimator. Analyze these images for distress. Ignore furniture. Focus on structural/cosmetic repairs needed for a flip."
    *   Output Format: Force JSON response.
2.  **Integration:**
    *   Use `google.generativeai` SDK.
    *   Handle rate limits and empty image lists gracefully.
3.  **Mocking:**
    *   If `GOOGLE_API_KEY` is missing, return a mock report (e.g., "Mock Analysis: Needs Paint").

## 4. Endpoint
*   `POST /api/v1/leads/{lead_id}/analyze-photos`
*   Accepts: `{"photo_urls": [...]}`
*   Returns: `PropertyConditionReport`
