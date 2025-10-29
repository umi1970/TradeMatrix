"""Configuration module"""

from .supabase import (
    get_settings,
    get_supabase_client,
    get_supabase_admin,
    supabase,
    supabase_admin,
    settings,
)

__all__ = [
    "get_settings",
    "get_supabase_client",
    "get_supabase_admin",
    "supabase",
    "supabase_admin",
    "settings",
]
