from pydantic import BaseModel
from typing import Optional

class Deal(BaseModel):
    lead_id: str
    arv: float
    rehab_cost: float
    mao_wholesale: float
    mao_buy_hold: float
    recommended_strategy: str
