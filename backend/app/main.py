import os
import logging
import sys
import asyncio
from typing import List, Optional, Union, Dict, Any
from fastapi import FastAPI, Depends, HTTPException, Security
from fastapi.security.api_key import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import Base, engine, get_db

# Fix for Windows asyncio compatibility - use Selector policy (NOT Proactor)
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# New Models & Schemas
from app.models.orm import LeadModel
from app.models.user import UserModel
from app.models.offer import OfferModel
from app.schemas import Lead, LeadCreate, User, UserCreate, Offer, OfferCreate

# Agents
from app.agents.analyst_agent import LeadAnalystAgent
from app.agents.engagement_agent import EngagementAgent
from app.agents.underwriting_agent import UnderwritingAgent

# Services
from app.services.real_market_scout_service import RealMarketScoutService
from app.services.pipeline.scout import ScoutService
from app.services.pipeline.cleaner import CleanerService
from app.services.vision_service import VisionService, PropertyConditionReport
from app.services.lex_service import LexService, LegalReviewResponse
from app.services.scribe_service import ScribeService
from app.services.matchmaker_service import MatchmakerService, BuyerMatch
from app.api.endpoints import dispositions, scout

# Conditional import for recorder (requires mcp_servers which is local-only)
try:
    from app.api.endpoints import recorder
    RECORDER_AVAILABLE = True
except ImportError:
    RECORDER_AVAILABLE = False
    print("WARNING: Recorder module not available (mcp_servers not found)")

# Settings endpoint
from app.api.endpoints import settings as settings_router
from app.models.settings import AppSetting

from pydantic import BaseModel

print("LOADING MAIN APP - DEBUG MODE")

# --- AUTHENTICATION ---
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def get_api_key(api_key_header: str = Security(api_key_header)):
    expected_key = os.getenv("ARELA_API_KEY", "arela-dev-key")
    if api_key_header == expected_key:
        return api_key_header
    return api_key_header

# --- APP SETUP ---
app = FastAPI(title="ARELA API", version="0.2.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all for debugging
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root health check - single definition
@app.get("/")
async def root_health_check():
    return {"status": "ok", "message": "ARELA Backend Running"}

# Initialize DB Tables (Async)
@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.get("/health")
async def health_status():
    return {"status": "ok", "mode": "async"}

# --- ROUTERS ---
app.include_router(dispositions.router, prefix="/api/v1/dispositions", tags=["dispositions"])
app.include_router(scout.router, prefix="/api/v1/scout", tags=["scout"])
app.include_router(settings_router.router, prefix="/api/v1", tags=["settings"])
if RECORDER_AVAILABLE:
    app.include_router(recorder.router, prefix="/api/v1/recorder", tags=["recorder"])

# --- SINGLETON SERVICES (for caching) ---
_scout_service_instance: Optional[ScoutService] = None

def _get_scout_service() -> ScoutService:
    """Singleton factory for ScoutService to persist HomeHarvest cache across requests."""
    global _scout_service_instance
    if _scout_service_instance is None:
        _scout_service_instance = ScoutService()
        print("Created singleton ScoutService instance (HomeHarvest cache enabled)")
    return _scout_service_instance

# --- USERS ---
@app.post("/api/v1/users/sync", response_model=User)
async def sync_user(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Ensures the OAuth user exists in our local DB.
    """
    stmt = select(UserModel).where(UserModel.email == user_in.email)
    result = await db.execute(stmt)
    user = result.scalars().first()
    
    if not user:
        user = UserModel(
            email=user_in.email,
            external_id=user_in.external_id
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    return user

# --- LEADS ---
@app.get("/api/v1/leads", response_model=List[Lead])
async def get_leads(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    stmt = select(LeadModel).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()

@app.get("/api/v1/leads/{lead_id}", response_model=Lead)
async def get_lead(lead_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(LeadModel).where(LeadModel.id == lead_id)
    result = await db.execute(stmt)
    lead = result.scalars().first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead

@app.post("/api/v1/leads", response_model=Lead)
async def create_lead(lead_in: LeadCreate, db: AsyncSession = Depends(get_db)):
    lead_data = lead_in.dict(exclude_unset=True)
    
    db_lead = LeadModel(**lead_data)
    db.add(db_lead)
    await db.commit()
    await db.refresh(db_lead)
    return db_lead


class LeadImportItem(BaseModel):
    """Schema for importing leads from Scout"""
    address: str
    address_zip: Optional[str] = None
    owner_name: Optional[str] = None
    mailing_address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    sqft: Optional[int] = None
    year_built: Optional[int] = None
    property_type: Optional[str] = None
    parcel_id: Optional[str] = None
    zoning: Optional[str] = None
    has_pool: bool = False
    has_garage: bool = False
    has_guesthouse: bool = False
    distress_score: int = 0


class LeadImportResponse(BaseModel):
    imported: int
    skipped: int
    total: int
    message: str


@app.post("/api/v1/leads/import", response_model=LeadImportResponse)
async def import_leads(leads: List[LeadImportItem], db: AsyncSession = Depends(get_db)):
    """
    Bulk import leads from LeadScout into the database.
    Dedupes by address (skips if already exists).
    """
    imported_count = 0
    skipped_count = 0
    
    for lead_data in leads:
        # Normalize address for deduplication
        address_normalized = lead_data.address.strip().upper()
        
        # Check if lead already exists
        stmt = select(LeadModel).where(
            LeadModel.address_street == address_normalized
        )
        result = await db.execute(stmt)
        existing = result.scalars().first()
        
        if existing:
            skipped_count += 1
            continue
        
        # Create new lead
        db_lead = LeadModel(
            address_street=lead_data.address,
            address_zip=lead_data.address_zip,
            owner_name=lead_data.owner_name,
            mailing_address=lead_data.mailing_address,
            latitude=lead_data.latitude,
            longitude=lead_data.longitude,
            bedrooms=lead_data.bedrooms,
            bathrooms=lead_data.bathrooms,
            sqft=lead_data.sqft,
            year_built=lead_data.year_built,
            property_type=lead_data.property_type,
            parcel_id=lead_data.parcel_id,
            zoning=lead_data.zoning,
            has_pool=lead_data.has_pool,
            has_garage=lead_data.has_garage,
            has_guesthouse=lead_data.has_guesthouse,
            distress_score=lead_data.distress_score,
            status="New",
            source="LeadScout"
        )
        db.add(db_lead)
        imported_count += 1
    
    await db.commit()
    
    return LeadImportResponse(
        imported=imported_count,
        skipped=skipped_count,
        total=len(leads),
        message=f"Imported {imported_count} leads, skipped {skipped_count} duplicates"
    )

# --- OFFERS ---
@app.post("/api/v1/offers", response_model=Offer)
async def create_offer(offer_in: OfferCreate, db: AsyncSession = Depends(get_db)):
    # Verify lead exists
    stmt = select(LeadModel).where(LeadModel.id == offer_in.lead_id)
    result = await db.execute(stmt)
    lead = result.scalars().first()
    
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
        
    db_offer = OfferModel(
        lead_id=offer_in.lead_id,
        offer_amount=offer_in.offer_amount
    )
    db.add(db_offer)
    await db.commit()
    await db.refresh(db_offer)
    return db_offer

@app.post("/api/v1/offers/{offer_id}/compliance", response_model=LegalReviewResponse)
async def check_offer_compliance(offer_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(OfferModel).where(OfferModel.id == offer_id)
    result = await db.execute(stmt)
    offer = result.scalars().first()
    
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    
    # Fetch Lead for context (ARV, etc.)
    stmt_lead = select(LeadModel).where(LeadModel.id == offer.lead_id)
    result_lead = await db.execute(stmt_lead)
    lead = result_lead.scalars().first()
    
    offer_details = {
        "offer_amount": offer.offer_amount,
        "buyer_name": "ARELA Holdings LLC", # Placeholder
        "estimated_value": lead.distress_score * 10000 if lead else 0, # Mock ARV logic
        "property_address": lead.address_street if lead else "Unknown"
    }
    
    service = LexService()
    return await service.review_offer(offer_details)

@app.post("/api/v1/offers/{offer_id}/contract")
async def generate_contract(offer_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(OfferModel).where(OfferModel.id == offer_id)
    result = await db.execute(stmt)
    offer = result.scalars().first()
    
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")
        
    stmt_lead = select(LeadModel).where(LeadModel.id == offer.lead_id)
    result_lead = await db.execute(stmt_lead)
    lead = result_lead.scalars().first()
    
    offer_data = {
        "lead_id": lead.id if lead else "unknown",
        "offer_amount": offer.offer_amount,
        "property_address": lead.address_street if lead else "Unknown",
        "buyer_name": "ARELA Holdings LLC",
        "seller_name": lead.owner_name if lead else "Unknown Owner"
    }
    
    service = ScribeService()
    file_path = service.generate_contract_pdf(offer_data)
    
    service = ScribeService()
    file_path = service.generate_contract_pdf(offer_data)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)



# --- AGENT ENDPOINTS (Legacy/Refactored) ---

@app.post("/leads/{lead_id}/analyze")
async def analyze_lead_endpoint(lead_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(LeadModel).where(LeadModel.id == lead_id)
    result = await db.execute(stmt)
    lead = result.scalars().first()
    
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    lead_data = {
        "address": lead.address_street,
        "distress_score": lead.distress_score,
        "status": lead.status,
        "sqft": lead.sqft,
        "bedrooms": lead.bedrooms,
        "bathrooms": lead.bathrooms,
        "year_built": lead.year_built,
        "lot_size": lead.lot_size,
        "owner_name": lead.owner_name
    }
    
    agent = LeadAnalystAgent()
    analysis_result = await agent.analyze_lead(lead_data)
    
    lead.distress_score = analysis_result.get("score", 0)
    lead.strategy = analysis_result.get("strategy", "Review")
    
    await db.commit()
    await db.refresh(lead)
    
    lead_dict = {k: v for k, v in lead.__dict__.items() if not k.startswith('_')}
    
    return {
        **lead_dict,
        "reasoning": analysis_result.get("reasoning", "")
    }

@app.post("/leads/{lead_id}/skiptrace")
async def skip_trace_endpoint(lead_id: str, db: AsyncSession = Depends(get_db)):
    """
    Perform skip trace lookup on a lead using BatchData API.
    Updates the lead with phone, email, and contact info.
    """
    from app.services.skip_trace_service import get_skip_trace_service
    
    stmt = select(LeadModel).where(LeadModel.id == lead_id)
    result = await db.execute(stmt)
    lead = result.scalars().first()
    
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Get skip trace service (uses BatchData API or mock mode)
    skip_trace = get_skip_trace_service()
    
    # Perform lookup
    result = await skip_trace.lookup(
        address=lead.address_street,
        owner_name=lead.owner_name,
        zip_code=lead.address_zip
    )
    
    # Update lead with results
    if result.status == "found":
        lead.phone = result.phone
        lead.email = result.email
        lead.owner_name = result.owner_name or lead.owner_name  # Don't overwrite if empty
        lead.mailing_address = result.mailing_address or lead.mailing_address
        lead.social_ids = result.social_ids or {}
        lead.status = "Skiptraced"  # Update status
        await db.commit()
        await db.refresh(lead)
    
    # Return lead data with skip trace message
    lead_dict = {k: v for k, v in lead.__dict__.items() if not k.startswith('_')}
    return {
        **lead_dict,
        "skip_trace_status": result.status,
        "skip_trace_message": result.message
    }

@app.post("/leads/{lead_id}/offer")
async def generate_offer_endpoint(lead_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(LeadModel).where(LeadModel.id == lead_id)
    result = await db.execute(stmt)
    lead = result.scalars().first()
    
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    property_data = {
        "sqft": lead.sqft,
        "has_pool": lead.has_pool,
        "has_garage": lead.has_garage
    }
    
    try:
        agent = UnderwritingAgent()
        result = await agent.generate_offer(property_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")
    
    lead.offer_amount = result.get("offer_amount")
    await db.commit()
    await db.refresh(lead)
    
    lead_dict = {k: v for k, v in lead.__dict__.items() if not k.startswith('_')}
    
    return {
        **lead_dict,
        "offer_details": result
    }

# --- VISION ENDPOINTS ---

class PhotoAnalysisRequest(BaseModel):
    photo_urls: List[str]

@app.post("/api/v1/leads/{lead_id}/analyze-photos", response_model=PropertyConditionReport)
async def analyze_photos_endpoint(lead_id: str, request: PhotoAnalysisRequest, db: AsyncSession = Depends(get_db)):
    # Verify lead exists
    stmt = select(LeadModel).where(LeadModel.id == lead_id)
    result = await db.execute(stmt)
    lead = result.scalars().first()
    
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    service = VisionService()
    report = await service.analyze_property_photos(request.photo_urls)
    
    return report

# --- SCOUT ENDPOINTS ---

class MarketAnalysisRequest(BaseModel):
    state_fips: str
    county_fips: str
    market_name: str

@app.get("/scout/autocomplete")
async def autocomplete_address(query: str):
    service = ScoutService()
    suggestions = await service.autocomplete_address(query)
    return {"suggestions": suggestions}

@app.post("/scout/market")
async def analyze_market_endpoint(request: MarketAnalysisRequest):
    service = RealMarketScoutService()
    return service.analyze_market(
        state_fips=request.state_fips,
        county_fips=request.county_fips,
        market_name=request.market_name
    )

class SearchFilters(BaseModel):
    zip_code: Optional[str] = None
    city: Optional[str] = None
    county: Optional[str] = None
    address: Optional[str] = None
    distress_type: Optional[Union[List[str], str]] = None
    property_types: Optional[List[str]] = None
    property_subtypes: Optional[List[str]] = None  # Parcel use codes for sub-types
    limit: int = 100
    bounds: Optional[Dict[str, float]] = None # {xmin, ymin, xmax, ymax}
    skip_homeharvest: bool = False # Fast mode - skip HomeHarvest enrichment
    neighborhood: Optional[str] = None # Search by subdivision/neighborhood name
    hot_list: Optional[List[str]] = None  # Hot list filters: FSBO, Price Reduced, High Days on Market, New Listing
    listing_statuses: Optional[List[str]] = None  # Listing status filter: For Sale, Contingent, Pending, etc.
    # Property detail filters (for MLS/HomeHarvest search)
    min_beds: Optional[int] = None
    max_beds: Optional[int] = None
    min_baths: Optional[int] = None
    max_baths: Optional[int] = None
    min_sqft: Optional[int] = None
    max_sqft: Optional[int] = None
    min_year_built: Optional[int] = None
    max_year_built: Optional[int] = None
    # Property feature filters
    has_pool: Optional[bool] = None
    has_garage: Optional[bool] = None
    has_guest_house: Optional[bool] = None

@app.post("/scout/search")
async def search_leads(filters: SearchFilters):
    # Force reload check
    with open("debug_cleaner.log", "a") as f:
        f.write(f"API RECEIVED SEARCH (RELOADED V2): {filters.dict()}\n")
    
    # Use singleton ScoutService to persist HomeHarvest cache across requests
    scout = _get_scout_service()
    cleaner = CleanerService()
    
    raw_leads = await scout.fetch_leads(filters.dict())
    
    with open("debug_cleaner.log", "a") as f:
        f.write(f"API FOUND {len(raw_leads)} RAW LEADS\n")
        
    cleaned_leads = cleaner.clean_leads(raw_leads)
    
    with open("debug_cleaner.log", "a") as f:
        f.write(f"API RETURNING {len(cleaned_leads)} CLEANED LEADS\n")
    
    # Debug Serialization
    try:
        import json
        json_str = json.dumps(cleaned_leads[:filters.limit], default=str)
        with open("debug_cleaner.log", "a") as f:
            f.write("Serialization SUCCESS\n")
    except Exception as e:
        with open("debug_cleaner.log", "a") as f:
            f.write(f"Serialization FAILED: {e}\n")
            
    # Check for Code Violation Warning
    warning = None
    distress = filters.distress_type
    # Normalize distress to list
    distress_list = distress if isinstance(distress, list) else ([distress] if distress else [])
    
    if "Code Violations" in distress_list:
        # Check if any leads actually have Code Violations
        has_violations = any("Code Violation" in (lead.get("distress_signals") or []) for lead in cleaned_leads)
        
        if not has_violations:
            city = filters.city.upper() if filters.city else None
            if city and city != "TUCSON":
                warning = f"Code Violations are only available in Tucson. Showing available property records for '{city}'."
            elif filters.zip_code and len(cleaned_leads) == 0:
                 # Only show warning if NO results found at all (implies search failed or truly empty)
                 # But don't say "Only available in Tucson" for zips, as that's confusing for Tucson zips
                 warning = f"No Code Violations found in {filters.zip_code}."
            elif len(cleaned_leads) == 0:
                 warning = "No Code Violations found matching your criteria."

    return {
        "leads": cleaned_leads[:filters.limit],
        "warning": warning
    }

@app.post("/scout/import")
async def import_leads(leads: List[Dict[str, Any]], db: AsyncSession = Depends(get_db)):
    imported_count = 0
    updated_count = 0
    
    for lead_data in leads:
        address = lead_data.get("address")
        if not address:
            continue
            
        stmt = select(LeadModel).where(LeadModel.address_street == address)
        result = await db.execute(stmt)
        existing_lead = result.scalars().first()
        
        if existing_lead:
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
            new_lead = LeadModel(
                address_street=address,
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
            
    await db.commit()
    return {"imported": imported_count, "updated": updated_count}


