# Core Module - MarketDataFetcher

This module provides the `MarketDataFetcher` class for integrating with the Twelve Data API to fetch market data and store it in Supabase.

## Features

- ✅ Fetch OHLCV time series data from Twelve Data API
- ✅ Fetch current quotes for symbols
- ✅ Automatic rate limiting (respects 800 req/day free tier limit)
- ✅ Retry logic with exponential backoff for failed requests
- ✅ Save data to Supabase with duplicate handling
- ✅ Type-safe with proper error handling
- ✅ Custom exceptions for different error scenarios

## Installation

Make sure you have the required dependencies:

```bash
cd services/api
pip install -r requirements.txt
```

## Configuration

Set the following environment variables in `services/api/.env`:

```bash
# Twelve Data API
TWELVE_DATA_API_KEY=your-twelve-data-api-key

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key
```

## Database Setup

Make sure you've run the market data schema migration:

```sql
-- Run in Supabase SQL Editor
-- File: services/api/supabase/migrations/003_market_data_schema.sql
```

This creates the following tables:
- `market_symbols` - Stores symbol information (DAX, NASDAQ, etc.)
- `ohlc` - Stores OHLCV candle data
- `levels_daily` - Stores daily levels (Pivot Points, etc.)
- `setups` - Stores trading setups
- `alerts` - Stores trading alerts

## Usage

### Basic Usage

```python
from core.market_data_fetcher import MarketDataFetcher

# Initialize fetcher
fetcher = MarketDataFetcher()

# Fetch time series data
candles = fetcher.fetch_time_series(
    symbol="DAX",
    interval="1h",
    outputsize=100
)

# Save to database
count = fetcher.save_to_database("DAX", "1h", candles)
print(f"Saved {count} candles")
```

### Fetch Current Quote

```python
# Get current quote
quote = fetcher.fetch_quote("DAX")

print(f"Symbol: {quote['symbol']}")
print(f"Close: {quote['close']}")
print(f"Change: {quote['percent_change']}%")
```

### Convenience Function

```python
from core.market_data_fetcher import fetch_and_save

# Fetch and save in one call
count = fetch_and_save("DAX", "1h", 100)
print(f"Saved {count} candles")
```

### Historical Data with Date Range

```python
candles = fetcher.fetch_time_series(
    symbol="EUR/USD",
    interval="1day",
    start_date="2025-01-01",
    end_date="2025-10-29",
    outputsize=5000
)
```

### Check API Usage

```python
usage = fetcher.get_api_usage()

print(f"Used: {usage['current_usage']}/{usage['plan_limit']} requests")
print(f"Plan: {usage['plan_name']}")
```

### Batch Fetch Multiple Symbols

```python
symbols = ["DAX", "NDX", "DJI"]
results = fetcher.batch_fetch_symbols(
    symbols=symbols,
    interval="1h",
    outputsize=50
)

for symbol, candles in results.items():
    print(f"{symbol}: {len(candles)} candles")
```

## Error Handling

The module provides custom exceptions for different error scenarios:

```python
from core.market_data_fetcher import (
    MarketDataFetcherError,
    RateLimitError,
    SymbolNotFoundError,
    APIError
)

try:
    candles = fetcher.fetch_time_series("DAX", "1h", 100)
    fetcher.save_to_database("DAX", "1h", candles)

except RateLimitError as e:
    print(f"Rate limit exceeded: {e}")
    # Wait or upgrade plan

except SymbolNotFoundError as e:
    print(f"Symbol not in database: {e}")
    # Add symbol to market_symbols table

except APIError as e:
    print(f"API error: {e}")
    # Check API key or symbol validity

except MarketDataFetcherError as e:
    print(f"General error: {e}")
```

## Rate Limiting

The fetcher automatically handles rate limiting:

- **Minimum 1 second between requests** to avoid spamming the API
- **Automatic retry on 429 errors** (rate limit exceeded)
- **60 second wait** after rate limit is hit
- **Maximum 3 retries** before raising RateLimitError

Free tier limit: **800 requests/day**

## Supported Intervals

- `1min`, `5min`, `15min`, `30min` - Intraday intervals
- `1h`, `4h` - Hourly intervals
- `1day`, `1week`, `1month` - Daily and longer

## Supported Symbols

The following symbols are pre-seeded in the database (from migration 003):

- `DAX` - DAX 40 (German index)
- `NDX` - NASDAQ 100
- `DJI` - Dow Jones 30
- `EUR/USD` - Euro / US Dollar
- `XAG/USD` - Silver Spot

To add more symbols, insert them into the `market_symbols` table:

```sql
INSERT INTO market_symbols (vendor, symbol, alias, tick_size, timezone, active)
VALUES ('twelve_data', 'AAPL', 'Apple Inc.', 0.01, 'America/New_York', true);
```

## Testing

Run the test suite to verify everything works:

```bash
cd services/api/src/core
python test_fetcher.py
```

The test suite includes:
- Fetch time series data
- Fetch current quote
- Save to database
- Convenience function
- API usage check
- Error handling

## API Documentation

For full Twelve Data API documentation, see:
- `docs/API_TwelveData.md` - Complete API reference (German)
- [Twelve Data Official Docs](https://twelvedata.com/docs)

## Architecture

```
┌─────────────────────┐
│  MarketDataFetcher  │
├─────────────────────┤
│ + fetch_time_series()│  ← Fetch OHLCV data
│ + fetch_quote()      │  ← Get current quote
│ + save_to_database() │  ← Save to Supabase
│ + get_api_usage()    │  ← Check rate limits
└──────────┬──────────┘
           │
      ┌────┴─────┐
      │          │
┌─────▼──────┐   │
│ Twelve Data│   │
│    API     │   │
└────────────┘   │
                 │
            ┌────▼─────┐
            │ Supabase │
            │──────────│
            │  ohlc    │  ← OHLCV candles
            │  symbols │  ← Symbol metadata
            └──────────┘
```

## Best Practices

1. **Cache data locally** - Don't re-fetch data you already have
2. **Use appropriate intervals** - Don't use 1min for historical backtests
3. **Respect rate limits** - 800 requests/day on free tier
4. **Handle errors gracefully** - Use try/except blocks
5. **Set timezone to Europe/Berlin** - Default for DAX trading hours
6. **Use upsert for duplicates** - Already handled by `save_to_database()`

## Troubleshooting

### "TWELVE_DATA_API_KEY not set in environment"

Make sure you've set the API key in your `.env` file:

```bash
TWELVE_DATA_API_KEY=your-api-key-here
```

### "Symbol not found in market_symbols table"

Add the symbol to the database first:

```sql
INSERT INTO market_symbols (vendor, symbol, alias, tick_size, timezone, active)
VALUES ('twelve_data', 'YOUR_SYMBOL', 'Display Name', 0.01, 'Europe/Berlin', true);
```

### "Rate limit exceeded"

You've hit the 800 requests/day limit. Either:
- Wait until tomorrow
- Upgrade to a paid Twelve Data plan
- Use cached data instead of fetching new data

### "Database connection failed"

Check your Supabase credentials in `.env`:

```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key
```

## Contributing

When modifying this module:

1. Update type hints
2. Add docstrings
3. Update tests
4. Update this README
5. Follow Python best practices

## License

© 2025 TradeMatrix.ai - All rights reserved
