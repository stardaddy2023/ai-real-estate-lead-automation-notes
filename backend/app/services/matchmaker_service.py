from typing import List, Dict, Optional
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

class BuyerMatch(BaseModel):
    buyer_id: str
    buyer_name: str
    match_score: float # 0-100
    match_reason: str

class MatchmakerService:
    def __init__(self):
        # Mock Buyer Data (In a real app, this would come from a DB)
        self.buyers = [
            {
                "id": "b1",
                "name": "Opendoor",
                "min_price": 100000,
                "max_price": 600000,
                "target_zips": ["85746", "85713", "85705"],
                "criteria": "Standard cosmetic flips, newer than 1980"
            },
            {
                "id": "b2",
                "name": "Offerpad",
                "min_price": 150000,
                "max_price": 500000,
                "target_zips": ["85746", "85710", "85711"],
                "criteria": "Clean titles, no foundation issues"
            },
            {
                "id": "b3",
                "name": "Tucson Flippers LLC",
                "min_price": 50000,
                "max_price": 300000,
                "target_zips": ["85705", "85706", "85713"],
                "criteria": "Heavy rehabs okay, cash only"
            }
        ]

    async def find_buyers(self, lead_id: str, lead_data: Dict) -> List[BuyerMatch]:
        """
        Finds potential buyers for a given lead based on simple rules.
        """
        matches = []
        
        lead_price = float(lead_data.get("offer_amount", 0))
        lead_zip = lead_data.get("zip_code", "")
        
        # If we don't have a zip, try to extract it from address
        if not lead_zip and "address" in lead_data:
            import re
            zip_match = re.search(r'\b\d{5}\b', lead_data["address"])
            if zip_match:
                lead_zip = zip_match.group(0)

        logger.info(f"Matching Lead {lead_id}: Price=${lead_price}, Zip={lead_zip}")

        for buyer in self.buyers:
            score = 0
            reasons = []
            
            # Rule 1: Price Check (30 points)
            if buyer["min_price"] <= lead_price <= buyer["max_price"]:
                score += 30
                reasons.append("Price in range")
            elif lead_price < buyer["min_price"]:
                score += 40 # Even better if it's cheap
                reasons.append("Below max price")
            else:
                reasons.append("Price too high")

            # Rule 2: Zip Code Check (50 points)
            if lead_zip in buyer["target_zips"]:
                score += 50
                reasons.append("Target Zip Code")
            
            # Rule 3: Generic Criteria (20 points - Mocked)
            # In a real system, we'd check property type, year built, etc.
            score += 20
            reasons.append("General criteria match")

            if score >= 50:
                matches.append(BuyerMatch(
                    buyer_id=buyer["id"],
                    buyer_name=buyer["name"],
                    match_score=score,
                    match_reason=", ".join(reasons)
                ))
        
        # Sort by score descending
        matches.sort(key=lambda x: x.match_score, reverse=True)
        return matches
