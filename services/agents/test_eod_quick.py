#!/usr/bin/env python3
"""
Quick test for EOD Data Fetcher
Run this to check if EOD implementation is ready to use
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from supabase import create_client
from src.eod_data_fetcher import EODDataFetcher


async def test_eod_implementation():
    """Test if EOD implementation is ready to use"""

    print("=" * 60)
    print("TradeMatrix.ai - EOD Implementation Quick Test")
    print("=" * 60)

    # Step 1: Check environment variables
    print("\n[1/5] Checking environment variables...")
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_SERVICE_ROLE_KEY')

    if not supabase_url or not supabase_key:
        print("❌ FAILED: Missing SUPABASE_URL or SUPABASE_SERVICE_KEY in .env")
        return False

    print(f"✅ SUPABASE_URL: {supabase_url[:30]}...")
    print(f"✅ SUPABASE_SERVICE_KEY: {'*' * 20}")

    # Step 2: Connect to Supabase
    print("\n[2/5] Connecting to Supabase...")
    try:
        # Try simple initialization without options
        from supabase import create_client as _create_client
        supabase = _create_client(supabase_url, supabase_key)
        print("✅ Connected to Supabase")
    except TypeError as e:
        # If that fails, it might be version incompatibility
        print(f"❌ FAILED: Supabase client version incompatibility: {e}")
        print("   Try upgrading: pip install --upgrade supabase")
        return False
    except Exception as e:
        print(f"❌ FAILED: Could not connect to Supabase: {e}")
        return False

    # Step 3: Check if tables exist
    print("\n[3/5] Checking if EOD tables exist...")
    try:
        # Try to query symbols table
        response = supabase.table('symbols').select('id, symbol').limit(1).execute()
        print(f"✅ symbols table exists ({len(response.data) if response.data else 0} records)")

        # Try to query eod_levels table
        response = supabase.table('eod_levels').select('id').limit(1).execute()
        print(f"✅ eod_levels table exists ({len(response.data) if response.data else 0} records)")

        # Try to query eod_data table
        response = supabase.table('eod_data').select('id').limit(1).execute()
        print(f"✅ eod_data table exists ({len(response.data) if response.data else 0} records)")

        # Try to query eod_fetch_log table
        response = supabase.table('eod_fetch_log').select('id').limit(1).execute()
        print(f"✅ eod_fetch_log table exists ({len(response.data) if response.data else 0} records)")

    except Exception as e:
        print(f"❌ FAILED: EOD tables not found. Run migrations first!")
        print(f"   Error: {e}")
        return False

    # Step 4: Check if symbols are configured
    print("\n[4/5] Checking if symbols are configured...")
    try:
        response = supabase.table('symbols')\
            .select('symbol, name, is_active')\
            .eq('is_active', True)\
            .execute()

        if not response.data or len(response.data) == 0:
            print("❌ FAILED: No active symbols found in database")
            return False

        print(f"✅ Found {len(response.data)} active symbols:")
        for symbol in response.data:
            print(f"   - {symbol['symbol']}: {symbol['name']}")
    except Exception as e:
        print(f"❌ FAILED: Could not fetch symbols: {e}")
        return False

    # Step 5: Test EOD Fetcher initialization
    print("\n[5/5] Testing EOD Fetcher initialization...")
    try:
        config_path = str(Path(__file__).parent.parent.parent / 'config' / 'rules' / 'eod_data_config.yaml')

        if not Path(config_path).exists():
            print(f"❌ FAILED: Config file not found: {config_path}")
            return False

        fetcher = EODDataFetcher(supabase_client=supabase, config_path=config_path)
        print("✅ EOD Fetcher initialized successfully")

        # Optional: Test a single symbol fetch (commented out to avoid API calls)
        # print("\n[OPTIONAL] Testing DAX fetch from Stooq...")
        # dax_data = await fetcher.fetch_from_stooq('^DJI')
        # if dax_data:
        #     print(f"✅ Successfully fetched DAX data: Close = {dax_data['close']}")
        # else:
        #     print("⚠️  Could not fetch DAX data (API might be rate-limited)")

    except Exception as e:
        print(f"❌ FAILED: Could not initialize EOD Fetcher: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Success!
    print("\n" + "=" * 60)
    print("✅ ALL CHECKS PASSED!")
    print("=" * 60)
    print("\nYour EOD implementation is ready to use!")
    print("\nNext steps:")
    print("1. Start Redis: docker run -d -p 6379:6379 redis:7-alpine")
    print("2. Start Celery worker: celery -A eod_tasks worker --loglevel=info")
    print("3. Start Celery beat: celery -A eod_tasks beat --loglevel=info")
    print("4. Or run manual fetch: python -c 'from eod_tasks import fetch_eod_data; fetch_eod_data.delay()'")

    return True


if __name__ == "__main__":
    # Load .env file
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / 'services' / 'api' / '.env'
    if not env_path.exists():
        env_path = Path(__file__).parent / '.env'

    if env_path.exists():
        load_dotenv(env_path)
        print(f"Loaded .env from: {env_path}")
    else:
        print("⚠️  No .env file found, using system environment variables")

    # Run test
    result = asyncio.run(test_eod_implementation())

    sys.exit(0 if result else 1)
