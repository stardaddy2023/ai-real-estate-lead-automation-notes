# Task Brief: Build LEX & SCRIBE (Phase 3)

> [!IMPORTANT]
> **To:** FORGE (Backend Engineer)
> **From:** ARCHITECT
> **Priority:** High (Phase 3 Backend)

## Objective
Implement the **Legal Engine (LEX)** and **Contract Generator (SCRIBE)** to finalize the "Shield & Sword" phase.

## References
*   **LEX Spec:** [lex_agent_spec.md](Build%20Docs/lex_agent_spec.md)
*   **SCRIBE Spec:** [scribe_spec.md](Build%20Docs/scribe_spec.md)

## Instructions

### 1. LEX (Legal Agent)
*   **File:** `app/services/lex_service.py`
*   **Logic:**
    *   Create a simple in-memory check for now (Mock Vector DB is fine if Chroma is too heavy).
    *   **Rule:** If `offer_amount` < `ARV * 0.5`, flag as "Predatory Pricing Risk".
    *   **Rule:** If `buyer_name` is missing, flag as "Identity Risk".
    *   Use Gemini 2.5 Pro Flash to generate a "Compliance Note".

### 2. SCRIBE (Contract Gen)
*   **File:** `app/services/scribe_service.py`
*   **Logic:**
    *   Use `Jinja2` to render an HTML string from `app/templates/contracts/psa.html`.
    *   **PDF:** Try `weasyprint`. If it fails on Windows, just save the rendered HTML as `.html` and return that path.
*   **Endpoint:** `POST /api/v1/offers/{id}/contract` -> Returns file URL/Path.

## Handoff
Mark tasks `Deploy LEX Agent` and `Build SCRIBE` as `[x]` in `task.md` when done.
