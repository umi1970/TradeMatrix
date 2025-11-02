#!/usr/bin/env python3
"""
Import Historical Market Data from CSV
Imports historical OHLCV data and calculates EOD levels
"""

import csv
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Any
import asyncio

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from supabase import create_client
from dotenv import load_dotenv


class HistoricalDataImporter:
    """Import historical market data from CSV files"""

    def __init__(self, supabase_client):
        self.supabase = supabase_client

    def read_csv(self, csv_path: str) -> List[Dict[str, Any]]:
        """
        Read CSV file and parse data

        Expected format: Date,Open,High,Low,Close,Volume
        """
        print(f"\n📂 Reading CSV: {csv_path}")

        if not Path(csv_path).exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")

        data = []
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)

            for row in reader:
                try:
                    # Parse and validate data
                    record = {
                        'date': datetime.strptime(row['Date'], '%Y-%m-%d').date(),
                        'open': Decimal(row['Open']),
                        'high': Decimal(row['High']),
                        'low': Decimal(row['Low']),
                        'close': Decimal(row['Close']),
                        'volume': int(float(row['Volume'])) if row.get('Volume') and row['Volume'] else 0
                    }
                    data.append(record)
                except Exception as e:
                    print(f"⚠️  Skipping invalid row: {row.get('Date', 'Unknown')} - {e}")
                    continue

        print(f"✅ Parsed {len(data)} records")
        print(f"   Date range: {data[0]['date']} to {data[-1]['date']}")

        return data

    def get_symbol_id(self, symbol: str) -> str:
        """Get symbol UUID from database"""
        print(f"\n🔍 Looking up symbol: {symbol}")

        response = self.supabase.table('symbols')\
            .select('id, symbol, name')\
            .eq('symbol', symbol)\
            .limit(1)\
            .execute()

        if not response.data or len(response.data) == 0:
            raise ValueError(f"Symbol '{symbol}' not found in database")

        symbol_data = response.data[0]
        print(f"✅ Found: {symbol_data['name']} (ID: {symbol_data['id']})")

        return symbol_data['id']

    def import_data(
        self,
        symbol_id: str,
        data: List[Dict[str, Any]],
        batch_size: int = 1000
    ) -> Dict[str, Any]:
        """
        Import data into eod_data table in batches
        """
        print(f"\n📊 Importing {len(data)} records into eod_data...")

        imported = 0
        skipped = 0
        errors = 0

        # Process in batches
        for i in range(0, len(data), batch_size):
            batch = data[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(data) + batch_size - 1) // batch_size

            print(f"   Batch {batch_num}/{total_batches} ({len(batch)} records)...", end=' ')

            # Prepare batch records
            records = []
            for record in batch:
                records.append({
                    'symbol_id': symbol_id,
                    'trade_date': record['date'].isoformat(),
                    'open': float(record['open']),
                    'high': float(record['high']),
                    'low': float(record['low']),
                    'close': float(record['close']),
                    'volume': record['volume'],
                    'data_source': 'historical_import'
                })

            try:
                # Insert batch (upsert to handle duplicates)
                response = self.supabase.table('eod_data')\
                    .upsert(records, on_conflict='symbol_id,trade_date')\
                    .execute()

                if response.data:
                    imported += len(response.data)
                    print(f"✅ {len(response.data)} inserted")
                else:
                    print(f"⚠️  No data returned")

            except Exception as e:
                errors += 1
                print(f"❌ Error: {str(e)[:100]}")
                continue

        print(f"\n📊 Import Summary:")
        print(f"   ✅ Imported: {imported}")
        print(f"   ⚠️  Skipped: {skipped}")
        print(f"   ❌ Errors: {errors}")

        return {
            'imported': imported,
            'skipped': skipped,
            'errors': errors
        }

    def calculate_levels_for_date(
        self,
        symbol_id: str,
        trade_date: str
    ) -> bool:
        """
        Calculate EOD levels for a specific date

        Requires at least 20 days of historical data for ATR calculation
        """
        from src.eod_data_fetcher import EODDataFetcher

        # We'll call the same logic that EODDataFetcher uses
        # but directly with SQL for better performance

        try:
            # Get previous 20 days of data for ATR
            date_obj = datetime.strptime(trade_date, '%Y-%m-%d').date()
            start_date = (date_obj - timedelta(days=30)).isoformat()  # 30 to be safe

            response = self.supabase.table('eod_data')\
                .select('*')\
                .eq('symbol_id', symbol_id)\
                .gte('trade_date', start_date)\
                .lte('trade_date', trade_date)\
                .order('trade_date', desc=False)\
                .execute()

            if not response.data or len(response.data) < 2:
                return False  # Not enough data

            data = response.data
            current_idx = None

            # Find current date index
            for idx, row in enumerate(data):
                if row['trade_date'] == trade_date:
                    current_idx = idx
                    break

            if current_idx is None or current_idx == 0:
                return False  # Current date not found or no previous day

            # Get yesterday's data (previous trading day)
            yesterday = data[current_idx - 1]

            # Calculate ATR if we have enough data
            atr_5d = None
            atr_20d = None

            if current_idx >= 5:
                # Calculate 5-day ATR
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
                # Calculate 20-day ATR
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

            # Calculate daily changes
            current = data[current_idx]
            daily_change_points = float(Decimal(str(current['close'])) - Decimal(str(yesterday['close'])))
            daily_change_percent = (daily_change_points / float(yesterday['close'])) * 100 if float(yesterday['close']) != 0 else 0

            # Create levels record
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

            # Insert/update levels
            self.supabase.table('eod_levels')\
                .upsert(levels_record, on_conflict='symbol_id,trade_date')\
                .execute()

            return True

        except Exception as e:
            print(f"Error calculating levels for {trade_date}: {e}")
            return False

    def calculate_all_levels(
        self,
        symbol_id: str,
        start_date: str = None,
        batch_size: int = 100
    ) -> Dict[str, int]:
        """
        Calculate EOD levels for all dates with data (with pagination)
        """
        print(f"\n🧮 Calculating EOD levels...")

        # Get all trade dates WITH PAGINATION
        all_dates = []
        offset = 0
        page_size = 1000

        while True:
            query = self.supabase.table('eod_data')\
                .select('trade_date')\
                .eq('symbol_id', symbol_id)\
                .order('trade_date', desc=False)\
                .range(offset, offset + page_size - 1)

            if start_date:
                query = query.gte('trade_date', start_date)

            response = query.execute()

            if not response.data or len(response.data) == 0:
                break

            all_dates.extend([row['trade_date'] for row in response.data])

            if len(response.data) < page_size:
                break

            offset += page_size

        if not all_dates:
            print("❌ No data found to calculate levels")
            return {'calculated': 0, 'failed': 0}

        dates = all_dates
        print(f"   Found {len(dates)} trading days")
        print(f"   Date range: {dates[0]} to {dates[-1]}")

        calculated = 0
        failed = 0

        # Process in batches for progress reporting
        for i in range(0, len(dates), batch_size):
            batch = dates[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(dates) + batch_size - 1) // batch_size

            print(f"   Batch {batch_num}/{total_batches}...", end=' ')

            batch_calculated = 0
            for date in batch:
                if self.calculate_levels_for_date(symbol_id, date):
                    batch_calculated += 1
                else:
                    failed += 1

            calculated += batch_calculated
            print(f"✅ {batch_calculated}/{len(batch)} calculated")

        print(f"\n📊 Levels Calculation Summary:")
        print(f"   ✅ Calculated: {calculated}")
        print(f"   ❌ Failed: {failed}")

        return {'calculated': calculated, 'failed': failed}


def main():
    """Main import workflow"""
    print("=" * 70)
    print("TradeMatrix.ai - Historical Data Import")
    print("=" * 70)

    # Load environment
    load_dotenv(Path(__file__).parent / '.env')

    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_KEY')

    if not supabase_url or not supabase_key:
        print("❌ ERROR: Missing SUPABASE_URL or SUPABASE_SERVICE_KEY")
        return 1

    # Get CSV path and symbol from user
    if len(sys.argv) < 3:
        print("\nUsage: python import_historical_data.py <csv_path> <symbol>")
        print("\nExample:")
        print("  python import_historical_data.py ../../data/historical/dax_historical.csv ^GDAXI")
        return 1

    csv_path = sys.argv[1]
    symbol = sys.argv[2]

    # Convert relative path to absolute
    if not Path(csv_path).is_absolute():
        csv_path = str((Path(__file__).parent / csv_path).resolve())

    print(f"\n📋 Import Configuration:")
    print(f"   CSV: {csv_path}")
    print(f"   Symbol: {symbol}")

    # Connect to Supabase
    print(f"\n🔌 Connecting to Supabase...")
    supabase = create_client(supabase_url, supabase_key)
    print(f"✅ Connected")

    # Initialize importer
    importer = HistoricalDataImporter(supabase)

    try:
        # Step 1: Get symbol ID
        symbol_id = importer.get_symbol_id(symbol)

        # Step 2: Read CSV
        data = importer.read_csv(csv_path)

        # Step 3: Import data
        import_result = importer.import_data(symbol_id, data)

        # Step 4: Calculate levels
        levels_result = importer.calculate_all_levels(symbol_id)

        # Final summary
        print("\n" + "=" * 70)
        print("✅ IMPORT COMPLETED SUCCESSFULLY!")
        print("=" * 70)
        print(f"\n📊 Final Summary:")
        print(f"   Records Imported: {import_result['imported']}")
        print(f"   Levels Calculated: {levels_result['calculated']}")
        print(f"   Errors: {import_result['errors'] + levels_result['failed']}")
        print("\n" + "=" * 70)

        return 0

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
