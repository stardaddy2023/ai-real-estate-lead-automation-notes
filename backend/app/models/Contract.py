from pydantic import BaseModel
from datetime import date

class Contract(BaseModel):
    deal_id: str
    seller_name: str
    purchase_price: float
    closing_date: date
    status: str = "draft"
