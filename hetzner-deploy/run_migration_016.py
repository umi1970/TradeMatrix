#!/usr/bin/env python3
"""
Execute Migration 016: Allow 'twelvedata' in price_cache.data_source
Runs the SQL migration directly against Supabase using service role key
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv(Path(__file__).parent / '.env')

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("❌ Missing SUPABASE_URL or SUPABASE_SERVICE_KEY in .env")
    exit(1)

# Migration SQL
MIGRATION_SQL = """
-- Migration 016: Allow 'twelvedata' in price_cache.data_source
-- Date: 2025-11-03

-- Drop old constraint
ALTER TABLE public.price_cache DROP CONSTRAINT IF EXISTS price_cache_data_source_check;

-- Add new constraint with 'twelvedata' included
ALTER TABLE public.price_cache
ADD CONSTRAINT price_cache_data_source_check
CHECK (data_source IN ('finnhub', 'alpha_vantage', 'twelvedata', 'yfinance', 'manual'));

-- Comment
COMMENT ON CONSTRAINT price_cache_data_source_check ON public.price_cache IS 'Allowed data sources: finnhub, alpha_vantage, twelvedata, yfinance, manual';
"""

print("=" * 70)
print("Running Migration 016: Allow 'twelvedata' in price_cache.data_source")
print("=" * 70)
print(f"\nSupabase URL: {SUPABASE_URL}")
print(f"Using service role key: {SUPABASE_SERVICE_KEY[:20]}...")

try:
    # Create Supabase client with admin privileges
    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

    print("\n✓ Connected to Supabase")
    print("\nExecuting SQL migration...")

    # Execute the migration SQL using RPC
    # Note: Supabase Python client doesn't have direct SQL execution
    # We need to use the REST API directly
    import requests

    # Use Supabase REST API to execute raw SQL via the SQL Editor endpoint
    # Actually, the Python client doesn't support raw SQL execution
    # This needs to be done via Supabase SQL Editor or PostgREST rpc function

    print("\n⚠️  Supabase Python client doesn't support raw SQL execution.")
    print("📝 Migration SQL saved. Please execute manually in Supabase SQL Editor:")
    print("\n" + "-" * 70)
    print(MIGRATION_SQL)
    print("-" * 70)

    print("\n📋 Steps to execute:")
    print("1. Go to: https://supabase.com/dashboard/project/htnlhazqzpwfyhnngfsn/sql")
    print("2. Paste the SQL above")
    print("3. Click 'Run'")
    print("\n✅ After running, the price_cache table will accept 'twelvedata' as data_source")

except Exception as e:
    print(f"\n❌ Error: {e}")
    exit(1)
