from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Numeric, func
import uuid
from app.core.database import Base

class OfferModel(Base):
    __tablename__ = "offers"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    lead_id = Column(String, ForeignKey("leads.id"), nullable=False)
    offer_amount = Column(Numeric(12, 2), nullable=True)
    lex_approval_status = Column(Boolean, default=False)
    contract_pdf_url = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
