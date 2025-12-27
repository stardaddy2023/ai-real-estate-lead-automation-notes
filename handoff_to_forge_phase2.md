# Task Brief: Build Vision Service (Phase 2)

> [!IMPORTANT]
> **To:** FORGE (Backend Engineer)
> **From:** ARCHITECT
> **Priority:** High (Core Analysis Feature)

## Objective
Implement the **Vision Service** to allow AI analysis of property photos for repair estimation.

## References
*   **Spec:** [vision_service_spec.md](Build%20Docs/vision_service_spec.md)

## Instructions
1.  **Service (`app/services/vision_service.py`):**
    *   Implement `analyze_property_photos(urls)`.
    *   Use `google.generativeai` (Gemini 2.5 Pro Flash).
    *   **Prompt:** Focus on "Investor Repair Estimates" (Flooring, Paint, Roof).

2.  **Endpoint (`app/api/endpoints/leads.py`):**
    *   Add `POST /{lead_id}/analyze-photos`.
    *   It should accept a list of URLs, call the service, and return the JSON report.

3.  **Mocking:**
    *   If no API Key is present, return a hardcoded "Mock Report" so Frontend can test.

## Handoff
Mark task `Build vision_service.py` as `[x]` in `task.md` when done.
