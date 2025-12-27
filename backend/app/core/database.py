from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from app.core.config import settings

# Ensure Async Driver for SQLite
database_url = settings.DATABASE_URL
if database_url.startswith("sqlite://") and "aiosqlite" not in database_url:
    database_url = database_url.replace("sqlite://", "sqlite+aiosqlite://")

engine = create_async_engine(
    database_url, 
    connect_args={"check_same_thread": False} if "sqlite" in database_url else {},
    echo=False
)

AsyncSessionLocal = sessionmaker(
    bind=engine, 
    class_=AsyncSession, 
    expire_on_commit=False,
    autoflush=False
)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
