class UnderwritingAgent:
    def __init__(self):
        pass

    async def underwrite_deal(self, property_data: dict):
        """
        Calculates ARV, Rehab costs, and Max Allowable Offer.
        """
        arv = property_data.get("arv", 300000) # Placeholder ARV
        rehab = property_data.get("rehab_estimate", 40000)
        
        mao = self._calculate_mao(arv, rehab)
        
        print(f"Underwriting complete. MAO: ${mao}")
        
        return {
            "arv": arv, 
            "rehab_cost": rehab,
            "mao": mao, 
            "strategy": "wholesale"
        }

    def _calculate_mao(self, arv: float, rehab: float) -> float:
        # 70% Rule: (ARV * 0.70) - Rehab
        return (arv * 0.70) - rehab

    async def generate_offer(self, property_data: dict):
        """
        Generates an offer based on property details.
        """
        # Simple logic for now: 
        # ARV = sqft * $200 (market avg)
        # Rehab = $40k base + $10k if pool + $5k if no garage
        
        sqft = property_data.get("sqft")
        if sqft is None:
            sqft = 1500
        has_pool = property_data.get("has_pool", "No") == "Yes"
        has_garage = property_data.get("has_garage", "No") == "Yes"
        
        arv = sqft * 200
        rehab = 40000
        if has_pool:
            rehab += 10000
        if not has_garage:
            rehab += 5000
            
        mao = self._calculate_mao(arv, rehab)
        
        return {
            "arv": arv,
            "rehab_estimate": rehab,
            "offer_amount": int(mao),
            "reasoning": f"Based on 70% rule: (ARV ${arv:,} * 0.7) - Rehab ${rehab:,}"
        }
