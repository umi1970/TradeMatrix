#!/usr/bin/env python3
"""
Test PriceFetcher Symbol Mapping
"""

from src.price_fetcher import PriceFetcher

# Initialize PriceFetcher
pf = PriceFetcher()

# Get symbol config
config = pf.get_all_watched_symbols()

print('='*60)
print('SYMBOL MAPPING TEST')
print('='*60)
print(f'\nDAX config: {config.get("DAX")}')
print(f'\nAll symbols in config:')
for symbol, conf in config.items():
    print(f'  {symbol}: {conf}')

print('\n' + '='*60)
print('TESTING FETCH_PRICE FOR DAX')
print('='*60)

# Test fetch_price for DAX
result = pf.fetch_price('DAX')
if result:
    print(f'\n✅ Success!')
    print(f'Current Price: {result["current_price"]}')
    print(f'Data Source: {result["data_source"]}')
    print(f'Timestamp: {result.get("timestamp", "N/A")}')

    # Calculate age
    if result.get('timestamp'):
        from datetime import datetime
        try:
            price_time = datetime.fromisoformat(result['timestamp'].replace('Z', '+00:00'))
            now = datetime.now()
            age_seconds = (now - price_time).total_seconds()
            print(f'Price Age: {age_seconds:.0f} seconds ({age_seconds/60:.1f} minutes)')
        except:
            print('Price Age: Could not calculate')
else:
    print('\n❌ Failed to fetch price for DAX')
