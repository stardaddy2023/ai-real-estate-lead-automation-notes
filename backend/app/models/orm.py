from sqlalchemy import Column, Integer, String, Float, JSON, Boolean, DateTime, ForeignKey, Date, func
import uuid
from app.core.database import Base

class LeadModel(Base):
    __tablename__ = "leads"

    # Core Identity (UUID as String)
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    
    # Address (Aligned with Properties spec)
    address_street = Column(String, index=True, nullable=False) # Was 'address'
    address_zip = Column(String(10), index=True, nullable=True)
    
    owner_name = Column(String, nullable=True)
    status = Column(String, default="New") # New, Skiptraced, Contacted
    distress_score = Column(Integer, default=0)
    equity_percent = Column(Float, default=0.0)
    
    # Location
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    
    # Contact Info
    phone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    mailing_address = Column(String, nullable=True)
    social_ids = Column(JSON, default={})
    
    # Property Details
    bedrooms = Column(Integer, nullable=True)
    bathrooms = Column(Float, nullable=True)
    sqft = Column(Integer, nullable=True)
    lot_size = Column(Float, nullable=True) # In acres
    year_built = Column(Integer, nullable=True)
    zoning = Column(String, nullable=True)
    property_type = Column(String, nullable=True)
    parcel_id = Column(String, nullable=True)
    
    # Flags (Boolean)
    has_pool = Column(Boolean, default=False)
    has_garage = Column(Boolean, default=False)
    has_guesthouse = Column(Boolean, default=False)
    
    # Financials
    last_sale_date = Column(Date, nullable=True)
    last_sale_price = Column(Integer, nullable=True)
    offer_amount = Column(Integer, nullable=True)
    mortgage_amount = Column(Integer, nullable=True)
    
    # Meta
    tags = Column(JSON, default=[])
    strategy = Column(String, nullable=True)
    source = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
