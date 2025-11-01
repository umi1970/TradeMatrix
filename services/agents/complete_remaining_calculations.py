#!/usr/bin/env python3
"""
Complete remaining EOD level calculations for DOW and EURUSD
This script is optimized to calculate only the remaining symbols
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

sys.path.insert(0, str(Path(__file__).parent / 'src'))
from calculate_remaining_levels import calculate_levels_for_date


def calculate_symbol_levels(supabase, symbol_id, symbol, name):
    """Calculate EOD levels for a specific symbol"""
    print(f"\n{'=' * 70}")
    print(f"Processing: {name} ({symbol})")
    print(f"{'=' * 70}")

    # Get all dates with pagination
    print("\n📊 Fetching all trade dates (with pagination)...")
    all_dates = []
    page_size = 1000
    offset = 0

    while True:
        response = supabase.table('eod_data')\
            .select('trade_date')\
            .eq('symbol_id', symbol_id)\
            .order('trade_date', desc=False)\
            .range(offset, offset + page_size - 1)\
            .execute()

        if not response.data or len(response.data) == 0:
            break

        all_dates.extend([row['trade_date'] for row in response.data])
        print(f"   Fetched {len(all_dates)} dates so far...")

        if len(response.data) < page_size:
            break

        offset += page_size

    if not all_dates:
        print(f"⚠️  No data found for {symbol}, skipping...")
        return {'calculated': 0, 'failed': 0}

    print(f"\n✅ Total dates: {len(all_dates)}")
    print(f"   Date range: {all_dates[0]} to {all_dates[-1]}")

    # Calculate levels in batches
    print("\n🧮 Calculating levels...")
    calculated = 0
    failed = 0
    batch_size = 100

    for i in range(0, len(all_dates), batch_size):
        batch = all_dates[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (len(all_dates) + batch_size - 1) // batch_size

        print(f"   Batch {batch_num}/{total_batches}...", end=' ')

        batch_calculated = 0
        for date in batch:
            if calculate_levels_for_date(supabase, symbol_id, date):
                batch_calculated += 1
            else:
                failed += 1

        calculated += batch_calculated
        print(f"✅ {batch_calculated}/{len(batch)} calculated")

    print(f"\n📊 {name} Summary:")
    print(f"   ✅ Calculated: {calculated}")
    print(f"   ❌ Failed: {failed}")

    return {'calculated': calculated, 'failed': failed}


def main():
    print("=" * 70)
    print("Complete Remaining EOD Level Calculations")
    print("=" * 70)

    load_dotenv(Path(__file__).parent / '.env')

    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_KEY')

    if not supabase_url or not supabase_key:
        print("❌ ERROR: Missing SUPABASE_URL or SUPABASE_SERVICE_KEY")
        return 1

    supabase = create_client(supabase_url, supabase_key)

    # Only process symbols that need remaining calculations
    # Skip DAX (100% complete) and NASDAQ (being calculated)
    symbols_to_process = [
        ('ca518eb7-c0bf-417c-8ae2-66cd5c12a6da', '^DJI', 'Dow Jones'),
        ('9321e996-99df-4835-8285-793bb414de1d', 'EURUSD', 'EUR/USD'),
    ]

    total_calculated = 0
    total_failed = 0

    for symbol_id, symbol, name in symbols_to_process:
        result = calculate_symbol_levels(supabase, symbol_id, symbol, name)
        total_calculated += result['calculated']
        total_failed += result['failed']

    print(f"\n" + "=" * 70)
    print(f"✅ ALL REMAINING SYMBOLS COMPLETED!")
    print(f"=" * 70)
    print(f"\n📊 Grand Total:")
    print(f"   ✅ Calculated: {total_calculated}")
    print(f"   ❌ Failed: {total_failed}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
