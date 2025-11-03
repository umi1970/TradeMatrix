#!/usr/bin/env python3
"""
Quick test script to verify Twelvedata symbols work correctly
Tests all 5 symbols without requiring Supabase connection
"""

import os
import requests
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent / '.env')

TWELVEDATA_API_KEY = os.getenv('TWELVEDATA_API_KEY')

if not TWELVEDATA_API_KEY:
    print("❌ TWELVEDATA_API_KEY not found in .env")
    exit(1)

print(f"✓ API Key loaded: {TWELVEDATA_API_KEY[:8]}...")
print("=" * 70)
print("Testing Twelvedata Symbol Mappings")
print("=" * 70)

# Symbol mappings from price_fetcher.py
symbols_to_test = [
    {
        'name': 'DAX (ETF Proxy)',
        'internal': '^GDAXI',
        'ticker': 'EXS1',
        'exchange': 'XETR'
    },
    {
        'name': 'NASDAQ 100 (ETF Proxy)',
        'internal': '^NDX',
        'ticker': 'QQQ',
        'exchange': 'NASDAQ'
    },
    {
        'name': 'Dow Jones (ETF Proxy)',
        'internal': '^DJI',
        'ticker': 'DIA',
        'exchange': 'NYSE'
    },
    {
        'name': 'EUR/USD (Forex)',
        'internal': 'EURUSD',
        'ticker': 'EUR/USD',
        'exchange': None
    },
    {
        'name': 'EUR/GBP (Forex)',
        'internal': 'EURGBP',
        'ticker': 'EUR/GBP',
        'exchange': None
    },
]

results = []

for symbol_info in symbols_to_test:
    print(f"\n📊 Testing: {symbol_info['name']}")
    print(f"   Internal: {symbol_info['internal']}")
    print(f"   Twelvedata: {symbol_info['ticker']} @ {symbol_info['exchange'] or 'N/A'}")

    # Build API request
    url = "https://api.twelvedata.com/quote"
    params = {
        'symbol': symbol_info['ticker'],
        'apikey': TWELVEDATA_API_KEY
    }

    if symbol_info['exchange']:
        params['exchange'] = symbol_info['exchange']

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Check for API errors
        if 'code' in data and data.get('code') != 200:
            print(f"   ❌ API Error: {data.get('message', 'Unknown error')}")
            results.append({**symbol_info, 'status': 'failed', 'error': data.get('message')})
            continue

        # Check if we got price data
        if 'close' in data:
            print(f"   ✅ SUCCESS!")
            print(f"      Name: {data.get('name', 'N/A')}")
            print(f"      Price: {data.get('close', 'N/A')} {data.get('currency', '')}")
            print(f"      Exchange: {data.get('exchange', 'N/A')}")
            results.append({**symbol_info, 'status': 'success', 'price': data['close']})
        else:
            print(f"   ⚠️  No price data returned")
            results.append({**symbol_info, 'status': 'no_data'})

    except requests.exceptions.RequestException as e:
        print(f"   ❌ Network error: {e}")
        results.append({**symbol_info, 'status': 'network_error', 'error': str(e)})
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        results.append({**symbol_info, 'status': 'error', 'error': str(e)})

# Summary
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)

success_count = sum(1 for r in results if r['status'] == 'success')
total_count = len(results)

for result in results:
    status_emoji = "✅" if result['status'] == 'success' else "❌"
    print(f"{status_emoji} {result['name']:30} {result['internal']:10} → {result['ticker']}")

print(f"\n{success_count}/{total_count} symbols working correctly")

if success_count == total_count:
    print("\n🎉 All symbols verified! Ready for production.")
    exit(0)
else:
    print(f"\n⚠️  {total_count - success_count} symbol(s) failed verification")
    exit(1)
