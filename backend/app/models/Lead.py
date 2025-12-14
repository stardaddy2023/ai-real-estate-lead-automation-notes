from pydantic import BaseModel
from typing import Optional, List

class Lead(BaseModel):
    id: Optional[str] = None
    address: str
    owner_name: Optional[str] = None
    status: str = "new"
    distress_score: int = 0
    latitude: float | None = None
    longitude: float | None = None
    equity_percent: float = 0.0
    tags: List[str] = []
    phone: Optional[str] = None
    email: Optional[str] = None
    mailing_address: Optional[str] = None
    social_ids: Optional[dict] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    sqft: Optional[int] = None
    lot_size: Optional[float] = None
    year_built: Optional[int] = None
    has_pool: Optional[str] = "No"
    has_garage: Optional[str] = "No"
    has_guesthouse: Optional[str] = "No"
    last_sale_date: Optional[str] = None
    last_sale_date: Optional[str] = None
    last_sale_price: Optional[int] = None
    offer_amount: Optional[int] = None
