from sqlalchemy import Column, String, DateTime, func
from app.core.database import Base

class AppSetting(Base):
    """Application-wide settings stored in database.
    
    Used for API keys and configuration that needs to persist
    across Cloud Run container restarts.
    """
    __tablename__ = "app_settings"

    key = Column(String, primary_key=True, index=True)
    value = Column(String, nullable=False)  # Consider encryption for production
    description = Column(String, nullable=True)
    category = Column(String, default="api_keys")  # api_keys, integrations, etc.
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
