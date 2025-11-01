#!/usr/bin/env python3
"""
Manual EOD Data Fetch Test
Run this to fetch and store EOD data for all configured symbols
"""

import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime, timezone

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from supabase import create_client
from src.eod_data_fetcher import EODDataFetcher


async def test_manual_fetch():
    """
    Perform manual EOD data fetch for all symbols
    """
    print("=" * 70)
    print("TradeMatrix.ai - Manual EOD Data Fetch Test")
    print("=" * 70)
    print(f"Started at: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n")

    # Step 1: Load environment variables
    print("[1/5] Loading environment variables...")
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_KEY')

    if not supabase_url or not supabase_key:
        print("❌ ERROR: Missing SUPABASE_URL or SUPABASE_SERVICE_KEY")
        return False

    print(f"✅ SUPABASE_URL: {supabase_url[:30]}...")
    print(f"✅ SUPABASE_SERVICE_KEY: {'*' * 20}\n")

    # Step 2: Connect to Supabase
    print("[2/5] Connecting to Supabase...")
    try:
        supabase = create_client(supabase_url, supabase_key)
        print("✅ Connected successfully\n")
    except Exception as e:
        print(f"❌ ERROR: Failed to connect: {e}")
        return False

    # Step 3: Initialize EOD Fetcher
    print("[3/5] Initializing EOD Data Fetcher...")
    try:
        config_path = str(Path(__file__).parent.parent.parent / 'config' / 'rules' / 'eod_data_config.yaml')

        if not Path(config_path).exists():
            print(f"❌ ERROR: Config file not found: {config_path}")
            return False

        fetcher = EODDataFetcher(
            supabase_client=supabase,
            config_path=config_path
        )
        print(f"✅ Fetcher initialized with config: {config_path}\n")
    except Exception as e:
        print(f"❌ ERROR: Failed to initialize fetcher: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Step 4: Fetch symbols to process
    print("[4/5] Fetching active symbols...")
    try:
        response = supabase.table('symbols')\
            .select('id, symbol, name, stooq_symbol, yahoo_symbol')\
            .eq('is_active', True)\
            .execute()

        symbols = response.data if response.data else []

        if not symbols:
            print("❌ ERROR: No active symbols found")
            return False

        print(f"✅ Found {len(symbols)} active symbols:\n")
        for sym in symbols:
            print(f"   📊 {sym['symbol']}: {sym['name']}")
            print(f"      Stooq: {sym.get('stooq_symbol', 'N/A')}")
            print(f"      Yahoo: {sym.get('yahoo_symbol', 'N/A')}")
        print()
    except Exception as e:
        print(f"❌ ERROR: Failed to fetch symbols: {e}")
        return False

    # Step 5: Fetch EOD data for all symbols
    print("[5/5] Fetching EOD data for all symbols...")
    print("-" * 70)

    try:
        results = await fetcher.fetch_all_symbols()

        print("\n" + "=" * 70)
        print("FETCH RESULTS:")
        print("=" * 70)

        success_count = results.get('success_count', 0)
        failed_count = results.get('failed_count', 0)
        total = success_count + failed_count

        print(f"\n📊 Summary:")
        print(f"   ✅ Successful: {success_count}/{total}")
        print(f"   ❌ Failed: {failed_count}/{total}")
        print(f"   📅 Trade Date: {results.get('trade_date', 'N/A')}")
        print(f"   ⏱️  Duration: {results.get('duration_ms', 0)}ms")

        # Show individual symbol results
        print(f"\n📋 Individual Results:")
        for symbol_result in results.get('results', []):
            symbol = symbol_result.get('symbol', 'Unknown')
            status = symbol_result.get('status', 'unknown')

            if status == 'success':
                print(f"\n   ✅ {symbol}")
                data = symbol_result.get('data', {})
                if data:
                    print(f"      Close: {data.get('close', 'N/A')}")
                    print(f"      High: {data.get('high', 'N/A')}")
                    print(f"      Low: {data.get('low', 'N/A')}")
                    print(f"      Volume: {data.get('volume', 'N/A')}")

                levels = symbol_result.get('levels_calculated', False)
                if levels:
                    print(f"      Levels: ✅ Calculated")
                else:
                    print(f"      Levels: ⚠️  Not calculated")

            elif status == 'failed':
                print(f"\n   ❌ {symbol}")
                error = symbol_result.get('error', 'Unknown error')
                print(f"      Error: {error}")

        # Check database
        print("\n" + "=" * 70)
        print("DATABASE VERIFICATION:")
        print("=" * 70)

        # Count records in eod_data
        eod_data_count = supabase.table('eod_data').select('id', count='exact').execute()
        print(f"\n✅ eod_data table: {eod_data_count.count} records")

        # Count records in eod_levels
        eod_levels_count = supabase.table('eod_levels').select('id', count='exact').execute()
        print(f"✅ eod_levels table: {eod_levels_count.count} records")

        # Count records in eod_fetch_log
        eod_log_count = supabase.table('eod_fetch_log').select('id', count='exact').execute()
        print(f"✅ eod_fetch_log table: {eod_log_count.count} records")

        # Show latest levels
        print("\n" + "=" * 70)
        print("LATEST EOD LEVELS:")
        print("=" * 70)

        latest_levels = supabase.table('eod_levels')\
            .select('*, symbols(symbol, name)')\
            .order('trade_date', desc=True)\
            .limit(5)\
            .execute()

        if latest_levels.data:
            print()
            for level in latest_levels.data:
                if level.get('symbols'):
                    symbol = level['symbols']['symbol']
                    name = level['symbols']['name']
                    print(f"📊 {symbol} ({name})")
                    print(f"   Date: {level.get('trade_date', 'N/A')}")
                    print(f"   Yesterday High: {level.get('yesterday_high', 'N/A')}")
                    print(f"   Yesterday Low: {level.get('yesterday_low', 'N/A')}")
                    print(f"   Yesterday Close: {level.get('yesterday_close', 'N/A')}")
                    print(f"   ATR 5d: {level.get('atr_5d', 'N/A')}")
                    print(f"   ATR 20d: {level.get('atr_20d', 'N/A')}")
                    print()
        else:
            print("\n⚠️  No levels data found yet")

        print("=" * 70)
        print("✅ TEST COMPLETED SUCCESSFULLY!")
        print("=" * 70)
        print(f"\nFinished at: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")

        return True

    except Exception as e:
        print(f"\n❌ ERROR during fetch: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Load .env file
    from dotenv import load_dotenv

    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print(f"Loaded .env from: {env_path}\n")
    else:
        print("⚠️  No .env file found, using system environment variables\n")

    # Run test
    success = asyncio.run(test_manual_fetch())

    sys.exit(0 if success else 1)
