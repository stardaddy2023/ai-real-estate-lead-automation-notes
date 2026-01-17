"""Settings API endpoints for managing application configuration."""

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import httpx
import os

from app.core.database import get_db
from app.models.settings import AppSetting
from app.core.config import settings as app_config

router = APIRouter(prefix="/settings", tags=["Settings"])

# Admin key for protecting write operations
ADMIN_API_KEY = os.getenv("ARELA_ADMIN_KEY", "")


async def verify_admin_key(x_admin_key: Optional[str] = Header(None)):
    """
    Dependency to verify admin API key for protected endpoints.
    If ARELA_ADMIN_KEY is not set, auth is skipped (dev mode).
    """
    if not ADMIN_API_KEY:
        return  # Skip auth if not configured (development mode)
    if x_admin_key != ADMIN_API_KEY:
        raise HTTPException(
            status_code=401, 
            detail="Unauthorized: Invalid or missing admin key"
        )


# Pydantic models
class SettingResponse(BaseModel):
    key: str
    masked_value: str  # Never expose full API keys
    description: Optional[str]
    category: str
    is_configured: bool
    updated_at: Optional[datetime]


class SettingUpdate(BaseModel):
    value: str


class SettingCreate(BaseModel):
    key: str
    value: str
    description: str = ""
    category: str = "custom"


class TestResult(BaseModel):
    key: str
    success: bool
    message: str


# Define available settings with descriptions
AVAILABLE_SETTINGS = {
    "GOOGLE_MAPS_API_KEY": {
        "description": "Google Maps JavaScript API key for map display",
        "category": "api_keys",
        "test_url": None,  # Custom test
    },
    "GOOGLE_API_KEY": {
        "description": "Google Gemini/Vertex AI API key",
        "category": "api_keys",
        "test_url": None,
    },
    "FRED_API_KEY": {
        "description": "Federal Reserve Economic Data API key",
        "category": "api_keys",
        "test_url": "https://api.stlouisfed.org/fred/series?series_id=GDP&api_key={key}&file_type=json",
    },
    "CENSUS_API_KEY": {
        "description": "US Census Bureau API key",
        "category": "api_keys",
        "test_url": "https://api.census.gov/data/2020/acs/acs5?get=NAME&for=state:04&key={key}",
    },
    "BLS_API_KEY": {
        "description": "Bureau of Labor Statistics API key",
        "category": "api_keys",
        "test_url": None,  # BLS API is complex
    },
    "VERTEX_AI_LOCATION": {
        "description": "Google Cloud region for Vertex AI (e.g., us-central1)",
        "category": "integrations",
        "test_url": None,
        "default_value": "us-central1",
    },
    "GOOGLE_CLOUD_PROJECT": {
        "description": "Google Cloud Project ID for Vertex AI and other GCP services",
        "category": "integrations",
        "test_url": None,
        "default_value": "",
    },
    "PIMA_RECORDER_URL": {
        "description": "Pima County Recorder document search URL",
        "category": "integrations",
        "test_url": None,
        "default_value": "https://pimacountyaz-web.tylerhost.net/web/search/DOCSEARCH55S10",
    },
}


def mask_value(value: str) -> str:
    """Mask API key for display (show first 4 and last 4 chars)."""
    if not value or len(value) < 12:
        return "****" if value else ""
    return f"{value[:4]}...{value[-4:]}"


@router.get("", response_model=List[SettingResponse])
async def list_settings(db: AsyncSession = Depends(get_db)):
    """List all available settings with their current status."""
    result = await db.execute(select(AppSetting))
    db_settings = {s.key: s for s in result.scalars().all()}
    
    settings_list = []
    for key, meta in AVAILABLE_SETTINGS.items():
        db_setting = db_settings.get(key)
        
        # Check env var fallback
        env_value = getattr(app_config, key, "") or os.getenv(key, "")
        
        # Get default value if defined
        default_value = meta.get("default_value", "")
        
        # Determine current value: DB → env var → default
        current_value = db_setting.value if db_setting else (env_value or default_value)
        
        settings_list.append(SettingResponse(
            key=key,
            masked_value=mask_value(current_value),
            description=meta["description"],
            category=meta["category"],
            is_configured=bool(current_value),
            updated_at=db_setting.updated_at if db_setting else None,
        ))
    
    # Also include custom settings from database (not in AVAILABLE_SETTINGS)
    for key, db_setting in db_settings.items():
        if key not in AVAILABLE_SETTINGS:
            settings_list.append(SettingResponse(
                key=db_setting.key,
                masked_value=mask_value(db_setting.value),
                description=db_setting.description or "Custom setting",
                category=db_setting.category or "custom",
                is_configured=True,
                updated_at=db_setting.updated_at,
            ))
    
    return settings_list


@router.post("", response_model=SettingResponse, dependencies=[Depends(verify_admin_key)])
async def create_setting(create: SettingCreate, db: AsyncSession = Depends(get_db)):
    """Create a new custom setting. Requires admin key."""
    # Check if key already exists
    result = await db.execute(select(AppSetting).where(AppSetting.key == create.key))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"Setting already exists: {create.key}")
    
    setting = AppSetting(
        key=create.key,
        value=create.value,
        description=create.description,
        category=create.category,
    )
    db.add(setting)
    await db.commit()
    await db.refresh(setting)
    
    return SettingResponse(
        key=setting.key,
        masked_value=mask_value(setting.value),
        description=setting.description,
        category=setting.category,
        is_configured=True,
        updated_at=setting.updated_at,
    )


@router.put("/{key}", response_model=SettingResponse, dependencies=[Depends(verify_admin_key)])
async def update_setting(key: str, update: SettingUpdate, db: AsyncSession = Depends(get_db)):
    """Update a setting value. Requires admin key."""
    # Check if it's a known setting or custom
    result = await db.execute(select(AppSetting).where(AppSetting.key == key))
    setting = result.scalar_one_or_none()
    
    if key not in AVAILABLE_SETTINGS and not setting:
        raise HTTPException(status_code=404, detail=f"Unknown setting: {key}")
    
    if setting:
        setting.value = update.value
        setting.updated_at = datetime.utcnow()
    else:
        setting = AppSetting(
            key=key,
            value=update.value,
            description=AVAILABLE_SETTINGS[key]["description"],
            category=AVAILABLE_SETTINGS[key]["category"],
        )
        db.add(setting)
    
    await db.commit()
    await db.refresh(setting)
    
    return SettingResponse(
        key=setting.key,
        masked_value=mask_value(setting.value),
        description=setting.description,
        category=setting.category,
        is_configured=True,
        updated_at=setting.updated_at,
    )


@router.post("/{key}/test", response_model=TestResult)
async def test_setting(key: str, db: AsyncSession = Depends(get_db)):
    """Test if an API key is valid."""
    if key not in AVAILABLE_SETTINGS:
        raise HTTPException(status_code=404, detail=f"Unknown setting: {key}")
    
    # Get current value
    result = await db.execute(select(AppSetting).where(AppSetting.key == key))
    db_setting = result.scalar_one_or_none()
    
    env_value = getattr(app_config, key, "") or os.getenv(key, "")
    current_value = db_setting.value if db_setting else env_value
    
    if not current_value:
        return TestResult(key=key, success=False, message="No API key configured")
    
    # Run test
    meta = AVAILABLE_SETTINGS[key]
    test_url = meta.get("test_url")
    
    if not test_url:
        # Keys without test URLs just validate they exist
        return TestResult(key=key, success=True, message="API key is configured (no validation endpoint)")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            url = test_url.format(key=current_value)
            response = await client.get(url)
            
            if response.status_code == 200:
                return TestResult(key=key, success=True, message="API key validated successfully")
            else:
                return TestResult(key=key, success=False, message=f"API returned status {response.status_code}")
    except Exception as e:
        return TestResult(key=key, success=False, message=f"Test failed: {str(e)}")


async def get_setting_value(key: str, db: AsyncSession) -> Optional[str]:
    """Helper to get a setting value (DB first, then env var fallback)."""
    result = await db.execute(select(AppSetting).where(AppSetting.key == key))
    db_setting = result.scalar_one_or_none()
    
    if db_setting:
        return db_setting.value
    
    # Fallback to env var
    return getattr(app_config, key, "") or os.getenv(key, "")


def get_setting_sync(key: str) -> Optional[str]:
    """
    Synchronous helper to get a setting value.
    Uses a separate sync connection to check database.
    Falls back to env var if not in database.
    
    This is safe to call from synchronous service code.
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    
    # Get database URL
    database_url = app_config.DATABASE_URL
    # Remove async driver prefix if present
    if "+aiosqlite" in database_url:
        database_url = database_url.replace("+aiosqlite", "")
    
    try:
        engine = create_engine(database_url, connect_args={"check_same_thread": False} if "sqlite" in database_url else {})
        with Session(engine) as session:
            from sqlalchemy import text
            result = session.execute(
                text("SELECT value FROM app_settings WHERE key = :key"),
                {"key": key}
            )
            row = result.fetchone()
            if row:
                return row[0]
    except Exception:
        # If DB access fails, fall back to env var
        pass
    
    # Fallback to env var
    return getattr(app_config, key, "") or os.getenv(key, "")


class PublicConfig(BaseModel):
    googleMapsApiKey: str


@router.get("/public-config", response_model=PublicConfig)
async def get_public_config(db: AsyncSession = Depends(get_db)):
    """
    Get public configuration for the frontend.
    This endpoint is unauthenticated and safe for public consumption.
    """
    # Get Google Maps API Key
    google_maps_key = await get_setting_value("GOOGLE_MAPS_API_KEY", db)
    
    return PublicConfig(
        googleMapsApiKey=google_maps_key or ""
    )
