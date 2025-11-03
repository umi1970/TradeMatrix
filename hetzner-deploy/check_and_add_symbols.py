#!/usr/bin/env python3
"""
Check if index symbols exist in database and add if missing
"""

import os
from supabase import create_client
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent / '.env')

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# Symbols that should exist
required_symbols = [
    {'symbol': '^GDAXI', 'name': 'DAX Performance Index', 'type': 'index'},
    {'symbol': '^NDX', 'name': 'NASDAQ 100 Index', 'type': 'index'},
    {'symbol': '^DJI', 'name': 'Dow Jones Industrial Average', 'type': 'index'},
    {'symbol': 'EURUSD', 'name': 'EUR/USD', 'type': 'forex'},
    {'symbol': 'EURGBP', 'name': 'EUR/GBP', 'type': 'forex'},
]

print("=" * 70)
print("Checking symbols table...")
print("=" * 70)

# Check existing symbols
existing = supabase.table('symbols').select('symbol, name, id').execute()
existing_symbols = {s['symbol']: s for s in existing.data}

print(f"\nFound {len(existing_symbols)} symbols in database:")
for sym in existing_symbols.keys():
    print(f"  - {sym}")

print(f"\n" + "=" * 70)
print("Checking required symbols...")
print("=" * 70)

missing = []
for req in required_symbols:
    if req['symbol'] in existing_symbols:
        print(f"✅ {req['symbol']:10} - EXISTS (ID: {existing_symbols[req['symbol']]['id'][:8]}...)")
    else:
        print(f"❌ {req['symbol']:10} - MISSING")
        missing.append(req)

if missing:
    print(f"\n" + "=" * 70)
    print(f"Adding {len(missing)} missing symbols...")
    print("=" * 70)

    for sym in missing:
        try:
            result = supabase.table('symbols').insert({
                'symbol': sym['symbol'],
                'name': sym['name'],
                'type': sym['type']
            }).execute()

            print(f"✅ Added: {sym['symbol']} ({sym['name']})")
        except Exception as e:
            print(f"❌ Failed to add {sym['symbol']}: {e}")
else:
    print(f"\n✅ All required symbols exist!")

print("\n" + "=" * 70)
print("Done!")
print("=" * 70)
