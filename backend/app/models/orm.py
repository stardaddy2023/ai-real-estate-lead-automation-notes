from sqlalchemy import Column, Integer, String, Float, JSON
from app.core.database import Base

class LeadModel(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    address = Column(String, index=True)
    owner_name = Column(String, nullable=True)
    status = Column(String, default="new")
    distress_score = Column(Integer, default=0)
    equity_percent = Column(Float, default=0.0)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    tags = Column(JSON, default=[])
    strategy = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    mailing_address = Column(String, nullable=True)
    social_ids = Column(JSON, nullable=True)
    bedrooms = Column(Integer, nullable=True)
    bathrooms = Column(Float, nullable=True)
    sqft = Column(Integer, nullable=True)
    lot_size = Column(Float, nullable=True) # In acres
    year_built = Column(Integer, nullable=True)
    has_pool = Column(String, default="No") # Boolean or String "Yes"/"No"
    has_garage = Column(String, default="No")
    has_guesthouse = Column(String, default="No")
    last_sale_date = Column(String, nullable=True)
    last_sale_price = Column(Integer, nullable=True)
    offer_amount = Column(Integer, nullable=True)
    zoning = Column(String, nullable=True)
    property_type = Column(String, nullable=True) # e.g. SFR, MFR, Land
    mortgage_amount = Column(Integer, nullable=True)
    source = Column(String, nullable=True)
    parcel_id = Column(String, nullable=True) # Ensure this is here if not already
