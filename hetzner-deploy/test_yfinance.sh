#!/bin/bash
# Test yfinance for DAX, NASDAQ 100, DOW JONES

docker-compose exec -T celery_worker python3 -c "
import yfinance as yf
import json

symbols = ['^GDAXI', '^NDX', '^DJI']

for symbol in symbols:
    print(f'=== {symbol} ===')
    ticker = yf.Ticker(symbol)
    info = ticker.history(period='1d')
    if not info.empty:
        latest = info.iloc[-1]
        print(f'Close: {latest[\"Close\"]:.2f}')
        print(f'High: {latest[\"High\"]:.2f}')
        print(f'Low: {latest[\"Low\"]:.2f}')
        print(f'Volume: {latest[\"Volume\"]:.0f}')
    else:
        print('No data')
    print()
"
