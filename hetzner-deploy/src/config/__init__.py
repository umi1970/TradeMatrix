"""
Supabase client configuration
Simplified database, auth, and storage access
"""

from supabase import create_client, Client
from pydantic_settings import BaseSettings
from functools import lru_cache
import os as _os


class Settings(BaseSettings):
    """Application settings"""

    # Supabase
    SUPABASE_URL: str
    SUPABASE_KEY: str = ""  # anon/public key for client-side
    SUPABASE_SERVICE_KEY: str = ""  # service role key for admin operations

    # Redis (for Celery & caching)
    REDIS_URL: str = "redis://localhost:6379"

    # AI Services
    OPENAI_API_KEY: str = ""

    # Twelve Data API
    TWELVEDATA_API_KEY: str = ""

    # Stripe (optional)
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""

    # Email (optional)
    SENDGRID_API_KEY: str = ""
    FROM_EMAIL: str = "noreply@tradematrix.ai"

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"  # Allow extra env vars without validation errors


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


def get_supabase_client() -> Client:
    """
    Get Supabase client for regular operations (RLS enabled)
    Uses anon key - respects Row Level Security
    """
    settings = get_settings()
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)


def get_supabase_admin() -> Client:
    """
    Get Supabase admin client (bypasses RLS)
    Uses service role key - use carefully!
    """
    # Read directly from env to avoid pydantic validation issues
    supabase_url = _os.getenv('SUPABASE_URL')
    service_key = _os.getenv('SUPABASE_SERVICE_KEY') or _os.getenv('SUPABASE_SERVICE_ROLE_KEY')

    if not supabase_url or not service_key:
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY/SUPABASE_SERVICE_ROLE_KEY are required")

    return create_client(supabase_url, service_key)


# Convenience exports (lazy - don't initialize on import)
# Use get_supabase_client() or get_supabase_admin() directly
