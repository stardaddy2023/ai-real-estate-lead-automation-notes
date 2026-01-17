import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "ARELA"
    API_V1_STR: str = "/api/v1"
    
    # Google Cloud
    GOOGLE_CLOUD_PROJECT: str = os.getenv("GOOGLE_CLOUD_PROJECT", "arela-project")
    GOOGLE_APPLICATION_CREDENTIALS: str = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
    
    # Database - default to SQLite for Cloud Run (use env var for PostgreSQL in production)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./data/arela.db")
    
    # APIs
    GOOGLE_MAPS_API_KEY: str = os.getenv("GOOGLE_MAPS_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "") # Fallback or alternative
    VERTEX_AI_LOCATION: str = os.getenv("VERTEX_AI_LOCATION", "us-central1")
    
    # Market Scout APIs
    FRED_API_KEY: str = os.getenv("FRED_API_KEY", "")
    CENSUS_API_KEY: str = os.getenv("CENSUS_API_KEY", "")
    BLS_API_KEY: str = os.getenv("BLS_API_KEY", "")
    
    # AI
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    
    # Security
    ARELA_ADMIN_KEY: str = os.getenv("ARELA_ADMIN_KEY", "")

    class Config:
        env_file = ".env"

settings = Settings()
