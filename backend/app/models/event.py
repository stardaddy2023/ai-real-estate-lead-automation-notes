from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, func
import uuid
from app.core.database import Base

class LeadEventModel(Base):
    __tablename__ = "lead_events"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    lead_id = Column(String, ForeignKey("leads.id"), nullable=False)
    type = Column(String, nullable=False) # status_change, note, email_sent
    payload = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
