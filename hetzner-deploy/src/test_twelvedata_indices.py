#!/usr/bin/env python3
"""
Test Twelvedata API for Index Data (DAX, NASDAQ, DOW)
"""

import os
import requests
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

TWELVEDATA_API_KEY = os.getenv('TWELVEDATA_API_KEY')

# Test verschiedene Symbol-Varianten für DAX
TEST_SYMBOLS = {
    'DAX': ['^GDAXI', 'GER40', 'DAX40', 'DE40', 'DAX', 'GDAXI'],
    'NASDAQ': ['^NDX', 'NDX', 'NAS100', 'US100', 'NASDAQ'],
    'DOW': ['^DJI', 'DJI', 'US30', 'DOW'],
}

def test_twelvedata_quote(symbol: str, exchange: str = None):
    """Test Twelvedata quote API"""
    url = "https://api.twelvedata.com/quote"
    params = {
        'symbol': symbol,
        'apikey': TWELVEDATA_API_KEY,
    }

    if exchange:
        params['exchange'] = exchange

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if 'code' in data:
            return {'error': data.get('message', 'Unknown error')}

        if 'close' in data:
            timestamp = data.get('timestamp', 'N/A')
            return {
                'price': data['close'],
                'timestamp': timestamp,
                'data': data
            }

        return {'error': 'No price data'}

    except Exception as e:
        return {'error': str(e)}


print("=" * 80)
print("TWELVEDATA INDEX TEST")
print("=" * 80)

for index_name, symbols in TEST_SYMBOLS.items():
    print(f"\n{'=' * 80}")
    print(f"Testing {index_name}")
    print("=" * 80)

    for symbol in symbols:
        print(f"\n📊 Testing symbol: {symbol}")
        result = test_twelvedata_quote(symbol)

        if 'error' in result:
            print(f"   ❌ Error: {result['error']}")
        else:
            print(f"   ✅ SUCCESS!")
            print(f"   Price: {result['price']}")
            print(f"   Timestamp: {result['timestamp']}")

            # Calculate age
            if result['timestamp'] != 'N/A':
                try:
                    price_time = datetime.fromisoformat(result['timestamp'].replace('Z', '+00:00'))
                    now = datetime.utcnow()
                    age_seconds = (now - price_time).total_seconds()
                    print(f"   Age: {age_seconds:.0f} seconds ({age_seconds/60:.1f} minutes)")
                except:
                    print(f"   Age: Could not calculate")

print("\n" + "=" * 80)
print("TEST COMPLETE")
print("=" * 80)
