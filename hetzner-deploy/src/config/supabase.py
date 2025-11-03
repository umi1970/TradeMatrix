"""
Supabase Client Configuration
Provides admin and client instances for backend services
"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file (if it exists)
# In Docker containers, env vars are injected by docker-compose via env_file
env_file = Path(__file__).parent.parent.parent / '.env'
if env_file.exists():
    load_dotenv(env_file)
else:
    # Running in Docker - env vars already injected by docker-compose
    pass


def get_supabase_admin() -> Client:
    """
    Get Supabase admin client with service role key
    Use this for backend operations that bypass RLS
    """
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_service_key = os.getenv("SUPABASE_SERVICE_KEY")

    if not supabase_url or not supabase_service_key:
        raise ValueError(
            "Missing Supabase credentials. Set SUPABASE_URL and SUPABASE_SERVICE_KEY in .env"
        )

    return create_client(supabase_url, supabase_service_key)


def get_supabase_client() -> Client:
    """
    Get Supabase client with anon key
    Use this for operations that respect RLS policies
    """
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_anon_key = os.getenv("SUPABASE_ANON_KEY")

    if not supabase_url:
        raise ValueError("Missing SUPABASE_URL in .env")

    # Fall back to service key if anon key not available
    key = supabase_anon_key or os.getenv("SUPABASE_SERVICE_KEY")

    if not key:
        raise ValueError("Missing SUPABASE_ANON_KEY or SUPABASE_SERVICE_KEY in .env")

    return create_client(supabase_url, key)


class Settings:
    """Settings placeholder for compatibility"""
    pass


settings = Settings()
