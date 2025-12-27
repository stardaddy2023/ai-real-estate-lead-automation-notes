# Technical Spec: SCRIBE Contract Generator (Phase 3)

> [!IMPORTANT]
> **Role:** ARCHITECT
> **Target System:** Backend (Python PDF Gen)
> **Purpose:** Generate legally binding PDF contracts from offer data.

## 1. Architecture
*   **Service:** `app.services.scribe_service.ScribeService`
*   **Templating:** `Jinja2` (HTML Templates).
*   **PDF Engine:** `WeasyPrint` (HTML -> PDF).

## 2. Templates
*   **File:** `app/templates/contracts/psa_v1.html`
*   **Variables:**
    *   `{{ buyer_name }}`
    *   `{{ seller_name }}`
    *   `{{ property_address }}`
    *   `{{ purchase_price }}`
    *   `{{ closing_date }}`
    *   `{{ earnest_money }}`

## 3. API Definition
```python
async def generate_contract_pdf(offer_data: dict) -> str:
    """
    Generates PDF and returns the file path or URL.
    """
    pass
```

## 4. Implementation Plan (FORGE)
1.  **Setup:** Install `jinja2`, `weasyprint`. (Note: WeasyPrint requires GTK on Windows, might need a fallback or Docker. **Fallback:** Use `xhtml2pdf` or just return HTML for now if Windows is tricky).
2.  **Template:** Create a simple HTML Purchase Agreement.
3.  **Endpoint:** `POST /api/v1/offers/{id}/generate-contract`.
