#!/usr/bin/env python3
"""
Calculate remaining EOD levels for all dates
Fixes the pagination issue from initial import
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from decimal import Decimal

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from supabase import create_client
from dotenv import load_dotenv


def calculate_levels_for_date(supabase, symbol_id: str, trade_date: str) -> bool:
    """Calculate EOD levels for a specific date"""
    try:
        date_obj = datetime.strptime(trade_date, '%Y-%m-%d').date()
        start_date = (date_obj - timedelta(days=30)).isoformat()

        # Get historical data
        response = supabase.table('eod_data')\
            .select('*')\
            .eq('symbol_id', symbol_id)\
            .gte('trade_date', start_date)\
            .lte('trade_date', trade_date)\
            .order('trade_date', desc=False)\
            .execute()

        if not response.data or len(response.data) < 2:
            return False

        data = response.data
        current_idx = None

        for idx, row in enumerate(data):
            if row['trade_date'] == trade_date:
                current_idx = idx
                break

        if current_idx is None or current_idx == 0:
            return False

        yesterday = data[current_idx - 1]

        # Calculate ATR
        atr_5d = None
        atr_20d = None

        if current_idx >= 5:
            tr_values = []
            for i in range(current_idx - 4, current_idx + 1):
                if i > 0:
                    high = Decimal(str(data[i]['high']))
                    low = Decimal(str(data[i]['low']))
                    prev_close = Decimal(str(data[i-1]['close']))

                    tr = max(
                        high - low,
                        abs(high - prev_close),
                        abs(low - prev_close)
                    )
                    tr_values.append(tr)

            if tr_values:
                atr_5d = float(sum(tr_values) / len(tr_values))

        if current_idx >= 20:
            tr_values = []
            for i in range(current_idx - 19, current_idx + 1):
                if i > 0:
                    high = Decimal(str(data[i]['high']))
                    low = Decimal(str(data[i]['low']))
                    prev_close = Decimal(str(data[i-1]['close']))

                    tr = max(
                        high - low,
                        abs(high - prev_close),
                        abs(low - prev_close)
                    )
                    tr_values.append(tr)

            if tr_values:
                atr_20d = float(sum(tr_values) / len(tr_values))

        current = data[current_idx]
        daily_change_points = float(Decimal(str(current['close'])) - Decimal(str(yesterday['close'])))
        daily_change_percent = (daily_change_points / float(yesterday['close'])) * 100 if float(yesterday['close']) != 0 else 0

        levels_record = {
            'symbol_id': symbol_id,
            'trade_date': trade_date,
            'yesterday_high': float(yesterday['high']),
            'yesterday_low': float(yesterday['low']),
            'yesterday_close': float(yesterday['close']),
            'yesterday_open': float(yesterday['open']),
            'yesterday_range': float(Decimal(str(yesterday['high'])) - Decimal(str(yesterday['low']))),
            'atr_5d': atr_5d,
            'atr_20d': atr_20d,
            'daily_change_points': daily_change_points,
            'daily_change_percent': daily_change_percent
        }

        supabase.table('eod_levels')\
            .upsert(levels_record, on_conflict='symbol_id,trade_date')\
            .execute()

        return True

    except Exception as e:
        return False


def main():
    print("=" * 70)
    print("Calculate Remaining EOD Levels for All Symbols")
    print("=" * 70)

    load_dotenv(Path(__file__).parent / '.env')

    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_KEY')

    supabase = create_client(supabase_url, supabase_key)

    # Define all symbols to process
    symbols = [
        ('21177e0b-02a2-48e9-8577-a40d7a5e18d9', '^GDAXI', 'DAX 40'),
        ('c969db54-fb12-4f4e-95b0-472dd682682b', '^NDX', 'NASDAQ 100'),
        ('ca518eb7-c0bf-417c-8ae2-66cd5c12a6da', '^DJI', 'Dow Jones'),
        ('9321e996-99df-4835-8285-793bb414de1d', 'EURUSD', 'EUR/USD'),
    ]

    total_calculated = 0
    total_failed = 0

    for symbol_id, symbol, name in symbols:
        print(f"\n{'=' * 70}")
        print(f"Processing: {name} ({symbol})")
        print(f"{'=' * 70}")

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
            continue

        print(f"\n✅ Total dates: {len(all_dates)}")
        print(f"   Date range: {all_dates[0]} to {all_dates[-1]}")

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

        total_calculated += calculated
        total_failed += failed

    print(f"\n" + "=" * 70)
    print(f"✅ ALL SYMBOLS COMPLETED!")
    print(f"=" * 70)
    print(f"\n📊 Grand Total:")
    print(f"   ✅ Calculated: {total_calculated}")
    print(f"   ❌ Failed: {total_failed}")


if __name__ == "__main__":
    main()
