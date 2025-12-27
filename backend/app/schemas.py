from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import date, datetime

# --- SHARED ---
class ContactInfo(BaseModel):
    phone: Optional[str] = None
    email: Optional[str] = None
    mailing_address: Optional[str] = None

class PropertyDetails(BaseModel):
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    sqft: Optional[int] = None
    lot_size: Optional[float] = None
    year_built: Optional[int] = None
    zoning: Optional[str] = None
    parcel_id: Optional[str] = None
    property_type: Optional[str] = None

class Flags(BaseModel):
    has_pool: bool = False
    has_garage: bool = False
    has_guesthouse: bool = False

class Financials(BaseModel):
    last_sale_date: Optional[date] = None
    last_sale_price: Optional[int] = None
    offer_amount: Optional[int] = None
    mortgage_amount: Optional[int] = None

# --- USER ---
class UserBase(BaseModel):
    email: str

class UserCreate(UserBase):
    external_id: str

class User(UserBase):
    id: str
    role: str
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# --- LEAD ---
class LeadBase(BaseModel):
    address_street: str
    address_zip: Optional[str] = None
    status: str = "New"
    distress_score: int = 0
    equity_percent: float = 0.0
    owner_name: Optional[str] = None
    
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class LeadCreate(LeadBase):
    pass

class Lead(LeadBase):
    id: str
    user_id: Optional[str] = None
    
    # Nested Objects (Optional to keep list view light, but populated in detail view)
    contact_info: Optional[ContactInfo] = None
    property_details: Optional[PropertyDetails] = None
    flags: Optional[Flags] = None
    financials: Optional[Financials] = None
    
    tags: List[str] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# --- OFFER ---
class OfferBase(BaseModel):
    lead_id: str
    offer_amount: float

class OfferCreate(OfferBase):
    pass

class Offer(OfferBase):
    id: str
    lex_approval_status: bool = False
    contract_pdf_url: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
