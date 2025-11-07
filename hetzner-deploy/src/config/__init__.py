"""
Supabase client configuration
Simplified database, auth, and storage access
"""

from supabase import create_client, Client
import os as _os


def get_supabase_client() -> Client:
    """
    Get Supabase client for regular operations (RLS enabled)
    Uses anon key - respects Row Level Security
    """
    supabase_url = _os.getenv('SUPABASE_URL')
    supabase_key = _os.getenv('SUPABASE_KEY') or _os.getenv('SUPABASE_ANON_KEY')

    if not supabase_url or not supabase_key:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY are required")

    return create_client(supabase_url, supabase_key)


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
