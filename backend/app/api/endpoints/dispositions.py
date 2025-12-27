from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.orm import LeadModel
from app.models.offer import OfferModel
from app.services.matchmaker_service import MatchmakerService, BuyerMatch

router = APIRouter()

@router.get("/matches", response_model=List[BuyerMatch])
async def find_buyer_matches(lead_id: str, db: AsyncSession = Depends(get_db)):
    # Fetch Lead
    stmt = select(LeadModel).where(LeadModel.id == lead_id)
    result = await db.execute(stmt)
    lead = result.scalars().first()
    
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
        
    # Fetch latest offer for price context
    stmt_offer = select(OfferModel).where(OfferModel.lead_id == lead_id).order_by(OfferModel.created_at.desc())
    result_offer = await db.execute(stmt_offer)
    offer = result_offer.scalars().first()
    
    lead_data = {
        "offer_amount": offer.offer_amount if offer else 0,
        "address": lead.address_street,
        "zip_code": lead.address_street.split()[-1] if lead.address_street and lead.address_street.split()[-1].isdigit() else "" 
        # Simple zip extraction fallback
    }
    
    service = MatchmakerService()
    return await service.find_buyers(lead_id, lead_data)
