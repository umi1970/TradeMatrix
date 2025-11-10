#!/usr/bin/env python3
"""
Test Alpha Vantage + Finnhub for Real-Time Index Data
"""

import os
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

ALPHA_VANTAGE_KEY = os.getenv('ALPHA_VANTAGE_API_KEY', 'demo')
FINNHUB_KEY = os.getenv('FINNHUB_API_KEY', 'demo')

print("=" * 80)
print("ALPHA VANTAGE + FINNHUB INDEX TEST")
print("=" * 80)

# Test symbols
test_symbols = {
    'DAX': {
        'alphavantage': 'DAX',
        'finnhub': 'OANDA:DE30EUR',  # DAX via Oanda
    },
    'NASDAQ': {
        'alphavantage': 'NDX',
        'finnhub': 'OANDA:NAS100USD',
    },
    'DOW': {
        'alphavantage': 'DJI',
        'finnhub': 'OANDA:US30USD',
    },
}

def test_alpha_vantage(symbol: str):
    """Test Alpha Vantage Global Quote"""
    url = "https://www.alphavantage.co/query"
    params = {
        'function': 'GLOBAL_QUOTE',
        'symbol': symbol,
        'apikey': ALPHA_VANTAGE_KEY,
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if 'Global Quote' in data and data['Global Quote']:
            quote = data['Global Quote']
            price = quote.get('05. price')
            timestamp = quote.get('07. latest trading day')

            if price:
                return {
                    'price': float(price),
                    'timestamp': timestamp,
                    'raw': quote
                }

        # Check for error
        if 'Error Message' in data:
            return {'error': data['Error Message']}

        if 'Note' in data:
            return {'error': 'Rate limit exceeded'}

        return {'error': 'No data'}

    except Exception as e:
        return {'error': str(e)}


def test_finnhub(symbol: str):
    """Test Finnhub Quote"""
    url = f"https://finnhub.io/api/v1/quote"
    params = {
        'symbol': symbol,
        'token': FINNHUB_KEY,
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if 'c' in data and data['c'] > 0:  # 'c' = current price
            timestamp = data.get('t', 0)  # Unix timestamp

            # Convert Unix to ISO
            if timestamp:
                dt = datetime.fromtimestamp(timestamp)
                timestamp_iso = dt.isoformat()
            else:
                timestamp_iso = 'N/A'

            return {
                'price': data['c'],
                'timestamp': timestamp_iso,
                'raw': data
            }

        return {'error': 'No data or price is 0'}

    except Exception as e:
        return {'error': str(e)}


# Test each index
for index_name, symbols in test_symbols.items():
    print(f"\n{'=' * 80}")
    print(f"Testing {index_name}")
    print("=" * 80)

    # Test Alpha Vantage
    print(f"\n📊 Alpha Vantage: {symbols['alphavantage']}")
    av_result = test_alpha_vantage(symbols['alphavantage'])

    if 'error' in av_result:
        print(f"   ❌ Error: {av_result['error']}")
    else:
        print(f"   ✅ SUCCESS!")
        print(f"   Price: {av_result['price']}")
        print(f"   Timestamp: {av_result['timestamp']}")

    # Test Finnhub
    print(f"\n📊 Finnhub: {symbols['finnhub']}")
    fh_result = test_finnhub(symbols['finnhub'])

    if 'error' in fh_result:
        print(f"   ❌ Error: {fh_result['error']}")
    else:
        print(f"   ✅ SUCCESS!")
        print(f"   Price: {fh_result['price']}")
        print(f"   Timestamp: {fh_result['timestamp']}")

        # Calculate age
        try:
            price_time = datetime.fromisoformat(fh_result['timestamp'])
            now = datetime.now()
            age_seconds = (now - price_time).total_seconds()
            print(f"   Age: {age_seconds:.0f} seconds ({age_seconds/60:.1f} minutes)")
        except:
            pass

print("\n" + "=" * 80)
print("TEST COMPLETE")
print("=" * 80)
print("\nNEXT STEPS:")
print("1. If Alpha Vantage works → Get API key ($49.99/mo)")
print("2. If Finnhub works → Get API key (FREE tier or $59.99/mo)")
print("3. If both work → Choose based on price/performance")
