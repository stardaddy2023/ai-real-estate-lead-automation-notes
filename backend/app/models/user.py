from sqlalchemy import Column, String, DateTime, func
import uuid
from app.core.database import Base

class UserModel(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    external_id = Column(String, unique=True, index=True, nullable=False) # OAuth Provider ID
    role = Column(String, default="user") # admin, user
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
