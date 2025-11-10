#!/usr/bin/env python3
"""
Find correct Twelvedata symbols for DAX, NASDAQ, DOW
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

TWELVEDATA_API_KEY = os.getenv('TWELVEDATA_API_KEY')

def search_symbol(query: str):
    """Search Twelvedata symbol database"""
    url = "https://api.twelvedata.com/symbol_search"
    params = {
        'symbol': query,
        'apikey': TWELVEDATA_API_KEY,
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get('data', [])
    except Exception as e:
        return []


def test_quote(symbol: str, exchange: str = None):
    """Test quote for symbol"""
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
            return None

        if 'close' in data:
            return {
                'price': data['close'],
                'timestamp': data.get('timestamp'),
                'name': data.get('name', ''),
            }
        return None
    except:
        return None


print("=" * 80)
print("TWELVEDATA SYMBOL SEARCH & TEST")
print("=" * 80)

# Search for each index
searches = {
    'DAX': ['DAX', 'GDAXI', 'German', 'Germany 40'],
    'NASDAQ': ['NASDAQ', 'NDX', 'IXIC', 'NASDAQ 100'],
    'DOW': ['DOW', 'DJIA', 'DJI', 'Dow Jones'],
}

for index_name, queries in searches.items():
    print(f"\n{'=' * 80}")
    print(f"SEARCHING: {index_name}")
    print("=" * 80)

    all_results = []

    for query in queries:
        results = search_symbol(query)
        for result in results:
            symbol = result.get('symbol')
            exchange = result.get('exchange')
            name = result.get('instrument_name', '')
            instrument_type = result.get('instrument_type', '')

            # Filter for indices only
            if 'index' in instrument_type.lower() or 'indice' in instrument_type.lower():
                all_results.append({
                    'symbol': symbol,
                    'exchange': exchange,
                    'name': name,
                    'type': instrument_type,
                })

    # Remove duplicates
    seen = set()
    unique_results = []
    for r in all_results:
        key = (r['symbol'], r['exchange'])
        if key not in seen:
            seen.add(key)
            unique_results.append(r)

    # Test each result
    print(f"\nFound {len(unique_results)} index symbols:")
    for result in unique_results[:10]:  # Limit to 10 per index
        print(f"\n📊 {result['symbol']} @ {result['exchange']}")
        print(f"   Name: {result['name']}")
        print(f"   Type: {result['type']}")

        # Test quote
        quote = test_quote(result['symbol'], result['exchange'])
        if quote:
            print(f"   ✅ QUOTE WORKS!")
            print(f"   Price: {quote['price']}")
            print(f"   Timestamp: {quote['timestamp']}")
        else:
            print(f"   ❌ No quote available")

print("\n" + "=" * 80)
print("SEARCH COMPLETE")
print("=" * 80)
