"""
Propensity Scoring Service - Calculates lead score based on distress signals and property data.

Scoring Formula: Motivation + Equity + Asset = Score (0-100)
- 0-50: Cold ❄️ (Archive)
- 51-79: Warm 🌤️ (Drip only)
- 80-100: Hot 🔥 (Skip trace + call)
"""

from typing import Dict, List, Optional
from datetime import datetime, date
from pydantic import BaseModel


class ScoreResult(BaseModel):
    """Result from propensity scoring"""
    score: int  # 0-100
    label: str  # "Cold", "Warm", "Hot"
    emoji: str  # ❄️, 🌤️, 🔥
    signals: List[str]  # List of detected signals
    breakdown: Dict[str, int]  # { motivation, equity, asset }


class PropensityScoringService:
    """
    Calculates lead propensity score based on:
    - Motivation (distress signals indicating seller pain)
    - Equity (profitability indicators)
    - Asset (buy box match)
    """
    
    # Motivation Signals (Seller Pain)
    MOTIVATION_WEIGHTS = {
        "Notice of Trustee Sale": 40,
        "Pre-Foreclosure": 40,
        "Lis Pendens": 35,
        "Tax Delinquent": 30,
        "Code Violations": 20,
        "Divorce": 15,
        "Quitclaim Deed": 15,
        "Judgment": 15,
        "Mechanics Lien": 15,
        "Vacant Property": 15,
        "Absentee Owner": 10,
        "Out of State": 10,
        "Probate": 10,
    }
    
    # Equity Weights (Profitability)
    EQUITY_WEIGHTS = {
        "Free & Clear": 30,
        "Long Ownership (>10yr)": 10,
        "Recent Purchase (<2yr)": -20,
        "Low Equity (<10%)": -50,
    }
    
    # Sale Date Weights (years since last sale)
    SALE_DATE_WEIGHTS = {
        "15+ years": 25,   # Likely free & clear
        "5-15 years": 15,  # Good equity built
        "3-5 years": 5,    # Some equity
        "< 3 years": -10,  # Recent purchase, little equity
    }
    
    # Recorder Document Weights (from bulk enhance)
    RECORDER_DOCUMENT_WEIGHTS = {
        "has_notice_sale": 40,        # Trustee sale scheduled - HOT
        "has_lis_pendens": 35,        # Litigation pending
        "has_lien": 15,               # Any liens
        "has_judgment": 15,           # Court judgment
        "has_reconveyance": 25,       # Loan paid off = equity!
    }
    
    # Asset Weights (Buy Box Match)
    ASSET_WEIGHTS = {
        "3+ Bed / 2+ Bath": 5,
        "In Target Zip": 10,
    }
    
    def score_lead(self, lead: Dict, recorder_data: Optional[Dict] = None) -> ScoreResult:
        """
        Calculate propensity score for a lead.
        
        Args:
            lead: Lead data with distress_signals, record_date, etc.
            recorder_data: Optional recorder lookup results (doc types found)
            
        Returns:
            ScoreResult with score, label, and breakdown
        """
        signals_found = []
        motivation_score = 0
        equity_score = 0
        asset_score = 0
        
        # --- MOTIVATION SCORING ---
        distress_signals = lead.get("distress_signals", [])
        
        for signal in distress_signals:
            for key, weight in self.MOTIVATION_WEIGHTS.items():
                if key.lower() in signal.lower():
                    motivation_score += weight
                    signals_found.append(f"{signal} (+{weight})")
                    break
        
        # Check for code violations
        violation_count = lead.get("violation_count", 0)
        if violation_count and violation_count > 0:
            if "Code Violations" not in [s.split(" (+")[0] for s in signals_found]:
                motivation_score += 20
                signals_found.append(f"Code Violations ({violation_count}) (+20)")
        
        # Check for Out of State (from mailing address)
        mailing_address = lead.get("mailing_address", "")
        if mailing_address and ", AZ" not in mailing_address.upper() and ", ARIZONA" not in mailing_address.upper():
            # Check if it's a real out-of-state address (not just empty)
            if len(mailing_address) > 10 and any(c.isalpha() for c in mailing_address):
                # Look for state abbreviations that aren't AZ
                state_abbrevs = ["CA", "TX", "FL", "NY", "NV", "CO", "WA", "OR", "IL", "PA", "OH"]
                for state in state_abbrevs:
                    if f", {state}" in mailing_address.upper():
                        motivation_score += 10
                        signals_found.append(f"Out of State ({state}) (+10)")
                        break
        
        # Recorder data signals (from bulk enhance)
        if recorder_data:
            # Notice of Sale - urgent foreclosure
            if recorder_data.get("has_notice_sale"):
                points = self.RECORDER_DOCUMENT_WEIGHTS.get("has_notice_sale", 40)
                motivation_score += points
                signals_found.append(f"Notice of Sale (+{points})")
            
            # Lis Pendens - litigation
            if recorder_data.get("has_lis_pendens"):
                points = self.RECORDER_DOCUMENT_WEIGHTS.get("has_lis_pendens", 35)
                motivation_score += points
                signals_found.append(f"Lis Pendens (+{points})")
            
            # Liens
            if recorder_data.get("has_lien"):
                points = self.RECORDER_DOCUMENT_WEIGHTS.get("has_lien", 15)
                motivation_score += points
                signals_found.append(f"Liens Found (+{points})")
            
            # Judgment
            if recorder_data.get("has_judgment"):
                points = self.RECORDER_DOCUMENT_WEIGHTS.get("has_judgment", 15)
                motivation_score += points
                signals_found.append(f"Judgment (+{points})")
            
            # Reconveyance = loan paid off = equity!
            if recorder_data.get("has_reconveyance"):
                points = self.RECORDER_DOCUMENT_WEIGHTS.get("has_reconveyance", 25)
                equity_score += points
                signals_found.append(f"Loan Paid Off (RECON) (+{points})")
        
        # --- EQUITY SCORING ---
        record_date = lead.get("record_date")
        
        if record_date:
            # Calculate years since last recording
            try:
                if isinstance(record_date, str):
                    # Try parsing common date formats
                    for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%Y/%m/%d"]:
                        try:
                            dt = datetime.strptime(record_date, fmt)
                            break
                        except:
                            dt = None
                elif isinstance(record_date, (int, float)):
                    # Epoch timestamp in milliseconds
                    dt = datetime.fromtimestamp(record_date / 1000)
                else:
                    dt = None
                
                if dt:
                    years_owned = (datetime.now() - dt).days / 365
                    
                    if years_owned > 15:
                        # Likely free & clear
                        equity_score += 30
                        signals_found.append(f"Free & Clear (est. {int(years_owned)}yr) (+30)")
                    elif years_owned > 10:
                        equity_score += 10
                        signals_found.append(f"Long Ownership ({int(years_owned)}yr) (+10)")
                    elif years_owned < 2:
                        equity_score -= 20
                        signals_found.append(f"Recent Purchase ({int(years_owned)}yr) (-20)")
            except Exception as e:
                pass  # Skip if date parsing fails
        
        # Check recorder data for deed type
        if recorder_data:
            if recorder_data.get("deed_type") == "WTDEED" and not recorder_data.get("has_dot"):
                equity_score += 30
                signals_found.append("Warranty Deed (no loan) (+30)")
            elif recorder_data.get("has_reconveyance"):
                equity_score += 25
                signals_found.append("Loan Paid Off (RECON) (+25)")
        
        # --- ASSET SCORING ---
        beds = lead.get("beds") or lead.get("bedrooms") or 0
        baths = lead.get("baths") or lead.get("bathrooms") or 0
        
        if beds >= 3 and baths >= 2:
            asset_score += 5
            signals_found.append("3+ Bed / 2+ Bath (+5)")
        
        # --- CALCULATE TOTAL SCORE ---
        raw_score = motivation_score + equity_score + asset_score
        
        # Cap score to 0-100 range
        score = max(0, min(100, raw_score))
        
        # Determine label
        if score >= 80:
            label = "Hot"
            emoji = "🔥"
        elif score >= 51:
            label = "Warm"
            emoji = "🌤️"
        else:
            label = "Cold"
            emoji = "❄️"
        
        return ScoreResult(
            score=score,
            label=label,
            emoji=emoji,
            signals=signals_found,
            breakdown={
                "motivation": motivation_score,
                "equity": equity_score,
                "asset": asset_score
            }
        )


# Singleton instance
_scoring_service: Optional[PropensityScoringService] = None


def get_scoring_service() -> PropensityScoringService:
    """Get or create singleton PropensityScoringService instance."""
    global _scoring_service
    if _scoring_service is None:
        _scoring_service = PropensityScoringService()
    return _scoring_service
