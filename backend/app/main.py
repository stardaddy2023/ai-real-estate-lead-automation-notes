from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from sqlalchemy.orm import Session
from app.core.database import Base, engine, get_db
from app.models.orm import LeadModel
from app.models.Lead import Lead
from app.agents.analyst_agent import LeadAnalystAgent
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="ARELA API", version="0.1.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Welcome to ARELA API"}

@app.get("/leads")
def get_leads(db: Session = Depends(get_db)):
    return db.query(LeadModel).all()

@app.get("/leads/{lead_id}")
def get_lead(lead_id: int, db: Session = Depends(get_db)):
    lead = db.query(LeadModel).filter(LeadModel.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead

@app.post("/leads")
def create_lead(lead: Lead, db: Session = Depends(get_db)):
    # Convert Pydantic model to dict, excluding None values to let DB defaults handle them if needed
    # But here we want to pass everything provided
    lead_data = lead.dict(exclude_unset=True)
    
    # Ensure strategy has a default if not provided
    if "strategy" not in lead_data:
        lead_data["strategy"] = "Wholesale"
        
    db_lead = LeadModel(**lead_data)
    db.add(db_lead)
    db.commit()
    db.refresh(db_lead)
    return db_lead

@app.post("/leads/{lead_id}/analyze")
async def analyze_lead_endpoint(lead_id: int, db: Session = Depends(get_db)):
    lead = db.query(LeadModel).filter(LeadModel.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Prepare data for agent
    lead_data = {
        "address": lead.address,
        "distress_score": lead.distress_score,
        "status": lead.status,
        "sqft": lead.sqft,
        "bedrooms": lead.bedrooms,
        "bathrooms": lead.bathrooms,
        "year_built": lead.year_built,
        "lot_size": lead.lot_size,
        "owner_name": lead.owner_name
    }
    
    # Run Agent
    agent = LeadAnalystAgent()
    analysis_result = await agent.analyze_lead(lead_data)
    
    # Update DB
    lead.distress_score = analysis_result.get("score", 0)
    lead.strategy = analysis_result.get("strategy", "Review")
    # Note: We might want to save the reasoning too, but LeadModel needs a column for it.
    # For now, we'll just return it to the frontend.
    
    db.commit()
    db.refresh(lead)
    
    # Safe serialization
    lead_dict = {k: v for k, v in lead.__dict__.items() if not k.startswith('_')}
    
    # Return combined data
    return {
        **lead_dict,
        "reasoning": analysis_result.get("reasoning", "")
    }

from app.agents.engagement_agent import EngagementAgent

@app.post("/leads/{lead_id}/skiptrace")
async def skip_trace_endpoint(lead_id: int, db: Session = Depends(get_db)):
    lead = db.query(LeadModel).filter(LeadModel.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Run Agent
    agent = EngagementAgent()
    result = await agent.skip_trace({"address": lead.address})
    
    # Update DB
    if result.get("status") == "found":
        lead.phone = result.get("phone")
        lead.email = result.get("email")
        lead.owner_name = result.get("owner_name")
        lead.mailing_address = result.get("mailing_address")
        lead.social_ids = result.get("social_ids")
        db.commit()
        db.refresh(lead)
    
    return lead

from app.agents.underwriting_agent import UnderwritingAgent

@app.post("/leads/{lead_id}/offer")
async def generate_offer_endpoint(lead_id: int, db: Session = Depends(get_db)):
    print(f"Received offer generation request for lead {lead_id}")
    lead = db.query(LeadModel).filter(LeadModel.id == lead_id).first()
    if not lead:
        print(f"Lead {lead_id} not found")
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Prepare data
    property_data = {
        "sqft": lead.sqft,
        "has_pool": lead.has_pool,
        "has_garage": lead.has_garage
    }
    print(f"Property data: {property_data}")
    
    # Run Agent
    try:
        agent = UnderwritingAgent()
        result = await agent.generate_offer(property_data)
        print(f"Offer result: {result}")
    except Exception as e:
        print(f"Agent error: {e}")
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")
    
    # Update DB
    lead.offer_amount = result.get("offer_amount")
    db.commit()
    db.refresh(lead)
    
    # Safe serialization
    lead_dict = {k: v for k, v in lead.__dict__.items() if not k.startswith('_')}
    
    return {
        **lead_dict,
        "offer_details": result
    }

# --- MARKET SCOUT MODULE ---
from app.services.pipeline.market_scout import MarketScoutService

class MarketAnalysisRequest(BaseModel):
    state_fips: str
    county_fips: str
    market_name: str

@app.get("/scout/autocomplete")
async def autocomplete_address(query: str):
    """
    Returns address suggestions based on partial input.
    """
    service = ScoutService()
    suggestions = await service.autocomplete_address(query)
    return {"suggestions": suggestions}

@app.post("/scout/market")
def analyze_market_endpoint(request: MarketAnalysisRequest):
    service = MarketScoutService()
    return service.analyze_market(
        state_fips=request.state_fips,
        county_fips=request.county_fips,
        market_name=request.market_name
    )

# --- LEAD SCOUT MODULE ---
from app.services.pipeline.scout import ScoutService
from app.services.pipeline.cleaner import CleanerService
from typing import List, Dict, Any

class SearchFilters(BaseModel):
    zip_code: Optional[str] = None
    city: Optional[str] = None
    county: Optional[str] = None
    address: Optional[str] = None
    distress_type: Optional[str] = None # "code_violations", "absentee_owner", "all"
    property_types: Optional[List[str]] = None
    limit: int = 100

@app.post("/scout/search")
async def search_leads(filters: SearchFilters):
    scout = ScoutService()
    cleaner = CleanerService()
    
    # 1. Fetch Raw Leads
    raw_leads = await scout.fetch_leads(filters.dict())
    
    # 2. Clean & Normalize
    cleaned_leads = cleaner.clean_leads(raw_leads)
    
    # 3. Enforce Limit
    # ScoutService over-fetches to account for attrition, so we must slice here.
    return cleaned_leads[:filters.limit]

@app.post("/scout/import")
async def import_leads(leads: List[Dict[str, Any]], db: Session = Depends(get_db)):
    imported_count = 0
    updated_count = 0
    
    for lead_data in leads:
        address = lead_data.get("address")
        if not address:
            continue
            
        # Check if exists
        existing_lead = db.query(LeadModel).filter(LeadModel.address == address).first()
        
        if existing_lead:
            # Update missing info only
            updated = False
            fields_to_update = [
                "owner_name", "sqft", "parcel_id", "zoning", "property_type", 
                "lot_size", "last_sale_date", "last_sale_price", "mailing_address",
                "latitude", "longitude"
            ]
            
            for field in fields_to_update:
                if not getattr(existing_lead, field) and lead_data.get(field):
                    setattr(existing_lead, field, lead_data.get(field))
                    updated = True
            
            if updated:
                updated_count += 1
        else:
            # Create new
            new_lead = LeadModel(
                address=address,
                owner_name=lead_data.get("owner_name"),
                status="New",
                strategy=lead_data.get("strategy", "Wholesale"),
                distress_score=50 if lead_data.get("distress_signals") else 0,
                sqft=lead_data.get("sqft"),
                year_built=lead_data.get("year_built"),
                mailing_address=lead_data.get("mailing_address"),
                parcel_id=lead_data.get("parcel_id"),
                zoning=lead_data.get("zoning"),
                property_type=lead_data.get("property_type"),
                lot_size=lead_data.get("lot_size"),
                last_sale_date=lead_data.get("last_sale_date"),
                last_sale_price=lead_data.get("last_sale_price"),
                latitude=lead_data.get("latitude"),
                longitude=lead_data.get("longitude")
            )
            db.add(new_lead)
            imported_count += 1
            
    db.commit()
    return {"imported": imported_count, "updated": updated_count}
