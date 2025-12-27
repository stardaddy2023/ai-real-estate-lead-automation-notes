import vertexai
from vertexai.generative_models import GenerativeModel
from app.core.config import settings
from typing import List, Optional, Dict
from pydantic import BaseModel
import logging
import os

logger = logging.getLogger(__name__)

class LegalReviewResponse(BaseModel):
    approved: bool
    risk_score: int # 0-100 (100 = High Risk)
    flagged_issues: List[str]
    compliance_notes: str

class LexService:
    def __init__(self):
        self.project_id = settings.GOOGLE_CLOUD_PROJECT
        self.location = settings.VERTEX_AI_LOCATION
        self.credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        
        self.model = None
        if self.project_id and self.credentials_path and os.path.exists(self.credentials_path):
            try:
                vertexai.init(project=self.project_id, location=self.location)
                self.model = GenerativeModel("gemini-2.5-pro-flash-001")
                logger.info("LexService initialized with Vertex AI.")
            except Exception as e:
                logger.error(f"Failed to initialize Vertex AI for LexService: {str(e)}")

    async def review_offer(self, offer_details: Dict) -> LegalReviewResponse:
        """
        Validates an offer against local laws and risk rules.
        """
        flagged_issues = []
        risk_score = 0
        
        # --- 1. In-Memory Rule Checks (Mock Vector DB) ---
        
        # Rule: Predatory Pricing Risk
        # If offer amount is significantly lower than ARV (After Repair Value) or Estimated Value
        offer_amount = float(offer_details.get("offer_amount", 0))
        estimated_value = float(offer_details.get("estimated_value", 0))
        
        if estimated_value > 0 and offer_amount < (estimated_value * 0.5):
            flagged_issues.append("Predatory Pricing Risk: Offer is less than 50% of estimated value.")
            risk_score += 40

        # Rule: Identity Risk
        buyer_name = offer_details.get("buyer_name", "")
        if not buyer_name or buyer_name.lower() == "unknown":
            flagged_issues.append("Identity Risk: Buyer name is missing or invalid.")
            risk_score += 30

        # --- 2. Vertex AI Compliance Note ---
        compliance_notes = "Vertex AI unavailable."
        
        if self.model:
            try:
                prompt = f"""
                You are LEX, a Real Estate Legal Compliance AI for Arizona.
                Review the following offer details for potential legal risks or compliance issues based on Arizona Real Estate Statutes (Title 32).
                
                Offer Details:
                {offer_details}
                
                Focus on:
                1. Wholesaling disclosure requirements.
                2. Earnest money adequacy.
                3. Contract clarity.
                
                Provide a brief, professional compliance note. Do not give legal advice, just flag potential concerns.
                """
                
                response = await self.model.generate_content_async(prompt)
                compliance_notes = response.text
            except Exception as e:
                logger.error(f"LexService AI generation failed: {str(e)}")
                compliance_notes = "AI Analysis failed. Please review manually."
        else:
            compliance_notes = "Mock Compliance Note: Ensure standard Arizona Wholesale Addendum is attached."

        # Determine Approval
        approved = risk_score < 50
        
        return LegalReviewResponse(
            approved=approved,
            risk_score=risk_score,
            flagged_issues=flagged_issues,
            compliance_notes=compliance_notes
        )
