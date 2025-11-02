#!/usr/bin/env python3
"""
Quick check if EOD data exists in Supabase
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

# Load environment
load_dotenv(Path(__file__).parent / '.env')

supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_KEY')

if not supabase_url or not supabase_key:
    print("❌ ERROR: Missing SUPABASE_URL or SUPABASE_SERVICE_KEY in .env")
    exit(1)

print(f"🔌 Connecting to: {supabase_url}")
supabase = create_client(supabase_url, supabase_key)

# Check symbols
print("\n📊 Checking symbols table...")
symbols_response = supabase.table('symbols').select('*').eq('is_active', True).execute()
symbols = symbols_response.data
print(f"   Found {len(symbols)} active symbols:")
for s in symbols:
    print(f"   - {s['symbol']}: {s['name']}")

# Check EOD data count
print("\n📈 Checking eod_data table...")
eod_response = supabase.table('eod_data').select('id', count='exact').execute()
total_records = eod_response.count if hasattr(eod_response, 'count') else len(eod_response.data)
print(f"   Total EOD records: {total_records:,}")

# Check recent data per symbol
print("\n🔍 Recent data per symbol:")
for symbol in symbols:
    response = supabase.table('eod_data')\
        .select('trade_date, close')\
        .eq('symbol_id', symbol['id'])\
        .order('trade_date', desc=True)\
        .limit(1)\
        .execute()

    if response.data:
        latest = response.data[0]
        print(f"   {symbol['symbol']:10} → Latest: {latest['trade_date']} @ ${latest['close']}")
    else:
        print(f"   {symbol['symbol']:10} → ❌ NO DATA")

print("\n✅ Check complete!")
