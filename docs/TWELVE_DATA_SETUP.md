# Twelve Data API Integration Setup Guide

**Complete guide to setting up live market data for TradeMatrix.ai**

---

## Table of Contents

1. [Overview](#overview)
2. [Getting Your API Key](#getting-your-api-key)
3. [Rate Limits & Pricing](#rate-limits--pricing)
4. [Configuration](#configuration)
5. [Database Setup](#database-setup)
6. [Starting Background Workers](#starting-background-workers)
7. [Testing the Integration](#testing-the-integration)
8. [Troubleshooting](#troubleshooting)
9. [API Reference](#api-reference)

---

## Overview

TradeMatrix.ai uses [Twelve Data](https://twelvedata.com/) as the primary source for live market data. The integration provides:

- **Real-time price updates** (every 1 minute)
- **Historical OHLCV data** (multiple timeframes: 1m, 5m, 15m, 1h, 4h, 1d)
- **Supported markets**: DAX, NASDAQ 100, Dow Jones, EUR/USD, GBP/USD
- **Automatic caching** to stay within rate limits
- **Fallback to sample data** if API is unavailable

### Architecture

```
Celery Worker → Twelve Data API → MarketDataFetcher → Supabase DB
                                                           ↓
                                        Next.js Frontend ← API Routes
```

---

## Getting Your API Key

### 1. Create a Twelve Data Account

1. Go to [https://twelvedata.com/](https://twelvedata.com/)
2. Click **"Sign Up"** (top right)
3. Choose **"Free Plan"** (800 requests/day, perfect for development)
4. Enter your email and create a password
5. Verify your email address

### 2. Get Your API Key

1. Log in to your Twelve Data dashboard
2. Navigate to **"API Documentation"** → **"Getting Started"**
3. Your API key will be displayed at the top of the page
4. Copy the key (format: `abcd1234efgh5678ijkl9012mnop3456`)

### 3. Verify Your Key

Test your API key in the terminal:

```bash
curl "https://api.twelvedata.com/time_series?symbol=DAX&interval=1h&apikey=YOUR_API_KEY&outputsize=5"
```

You should see a JSON response with OHLCV data.

---

## Rate Limits & Pricing

### Free Tier (Perfect for Development)

- **800 API calls per day**
- **8 API calls per minute**
- **Access to**: Stocks, Forex, Crypto, ETFs, Indices
- **Historical data**: Up to 5000 data points per request
- **Realtime quotes**: Yes (with 15-minute delay for stocks)

### Our Implementation Respects Rate Limits

- **Realtime prices**: Fetched every **1 minute** (60 calls/hour = 1440/day)
- **Intelligent caching**: 60-second TTL cache reduces redundant calls
- **Request delays**: 1.5 seconds between batch requests
- **Auto-retry**: Exponential backoff on rate limit errors

**Estimated Daily Usage:**
- Realtime price fetches: ~1440 calls/day (5 symbols × 1440 minutes)
- Well within the 800 calls/day limit ✅

### Paid Plans (For Production)

| Plan | Requests/Day | Cost |
|------|--------------|------|
| Basic | 800 | Free |
| Grow | 3,000 | $9.99/mo |
| Pro | 10,000 | $29.99/mo |
| Ultra | 50,000 | $99.99/mo |

**Recommendation:** Start with Free tier for MVP, upgrade to Grow ($9.99/mo) for production.

---

## Configuration

### 1. Backend Configuration

**File:** `services/api/.env`

```bash
# Copy from .env.example
cp services/api/.env.example services/api/.env

# Add your Twelve Data API key
TWELVE_DATA_API_KEY=your_api_key_here

# Supabase credentials
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key

# Redis (required for Celery)
REDIS_URL=redis://localhost:6379
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### 2. Agents Configuration

**File:** `services/agents/.env`

```bash
# Copy from .env.example
cp services/agents/.env.example services/agents/.env

# Add the same Twelve Data API key
TWELVE_DATA_API_KEY=your_api_key_here

# Supabase credentials (same as backend)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key

# Redis connection
REDIS_URL=redis://localhost:6379
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

---

## Database Setup

### 1. Apply Database Migrations

Execute the following migrations in your Supabase SQL Editor:

#### Migration 003: Market Data Schema (Already Applied)

This creates the core tables:
- `market_symbols` - Trading symbols (DAX, NASDAQ, etc.)
- `ohlc` - OHLCV candle data
- `levels_daily` - Daily pivot points and levels
- `setups` - Trading setups
- `alerts` - Trading alerts

**Location:** `services/api/supabase/migrations/003_market_data_schema.sql`

#### Migration 009: Current Prices Table (NEW - Apply Now)

This creates the `current_prices` table for real-time price snapshots.

**Location:** `services/api/supabase/migrations/009_current_prices_table.sql`

**To apply:**

1. Open Supabase Dashboard → SQL Editor
2. Copy content from `009_current_prices_table.sql`
3. Paste and click **"Run"**
4. Verify: Query `current_prices` table should exist

### 2. Verify Tables

Run this query in Supabase SQL Editor:

```sql
-- Check if all tables exist
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN ('market_symbols', 'ohlc', 'current_prices')
ORDER BY table_name;
```

Expected output:
```
current_prices
market_symbols
ohlc
```

### 3. Verify Seed Data

Check that default symbols are inserted:

```sql
SELECT symbol, alias, active
FROM market_symbols
WHERE vendor = 'twelve_data';
```

Expected symbols:
- DAX (DAX 40)
- NDX (NASDAQ 100)
- DJI (Dow Jones 30)
- EUR/USD (Euro / US Dollar)
- XAG/USD (Silver Spot)

---

## Starting Background Workers

### Prerequisites

1. **Redis must be running**

```bash
# Start Redis with Docker
docker run -d -p 6379:6379 redis:7-alpine

# OR install Redis locally (macOS)
brew install redis
brew services start redis

# OR install Redis locally (Ubuntu/Debian)
sudo apt-get install redis-server
sudo systemctl start redis
```

2. **Python dependencies installed**

```bash
cd services/agents
pip install -r ../api/requirements.txt
pip install celery redis cachetools
```

### Step 1: Start Celery Worker

The worker processes market data fetching tasks.

```bash
cd services/agents

# Make script executable (first time only)
chmod +x start_market_data_worker.sh

# Start the worker
./start_market_data_worker.sh
```

You should see:
```
=========================================
  TradeMatrix.ai - Market Data Worker
=========================================

Starting Celery worker for market data tasks...

[2025-10-29 12:00:00] celery@hostname ready.
```

**Keep this terminal open!**

### Step 2: Start Celery Beat Scheduler

The scheduler triggers periodic tasks (every 1 minute for price updates).

**In a new terminal:**

```bash
cd services/agents

# Make script executable (first time only)
chmod +x start_beat_scheduler.sh

# Start the scheduler
./start_beat_scheduler.sh
```

You should see:
```
=========================================
  TradeMatrix.ai - Beat Scheduler
=========================================

Scheduled tasks:
  - Fetch realtime prices: Every 1 minute
  - Daily data refresh: 2:00 AM UTC
  - API usage check: Every hour

celery beat v5.x.x is starting.
```

**Keep this terminal open too!**

### Step 3: Verify Workers Are Running

In a third terminal:

```bash
cd services/agents
celery -A src.market_data_tasks inspect active
```

You should see both workers listed.

---

## Testing the Integration

### 1. Manual Task Execution

Test fetching data for a single symbol:

```bash
cd services/agents
python -c "
from src.market_data_tasks import fetch_historical_data
result = fetch_historical_data.delay('DAX', '1h', 100)
print('Task ID:', result.id)
print('Status:', result.status)
print('Result:', result.get(timeout=30))
"
```

Expected output:
```
Task ID: abc123-def456-...
Status: SUCCESS
Result: {
  'symbol': 'DAX',
  'interval': '1h',
  'candles_fetched': 100,
  'candles_saved': 100,
  'success': True
}
```

### 2. Check Database

Verify data was saved:

```sql
-- Count candles per symbol
SELECT
  ms.symbol,
  COUNT(*) as candle_count,
  MIN(o.ts) as oldest_data,
  MAX(o.ts) as newest_data
FROM ohlc o
JOIN market_symbols ms ON o.symbol_id = ms.id
WHERE o.timeframe = '1h'
GROUP BY ms.symbol
ORDER BY ms.symbol;
```

### 3. Test Frontend API

Open your browser and navigate to:

```
http://localhost:3000/api/market-data/current
```

Expected JSON response:
```json
{
  "data": [
    {
      "symbol": "DAX",
      "name": "DAX 40",
      "price": 18542.75,
      "change": 142.5,
      "changePercent": 0.82,
      "trend": "up",
      "updatedAt": "2025-10-29T12:00:00Z"
    },
    ...
  ],
  "count": 5,
  "timestamp": "2025-10-29T12:00:00Z"
}
```

### 4. Test Dashboard

1. Start the Next.js frontend:

```bash
cd apps/web
npm run dev
```

2. Open http://localhost:3000/dashboard

3. You should see:
   - **Market Overview cards** with real prices
   - **Updating every 30 seconds** automatically
   - **Refresh button** to manually update

### 5. Test Charts Page

1. Navigate to http://localhost:3000/dashboard/charts

2. You should see:
   - **Real candlestick data** from Twelve Data
   - **Symbol selector** (DAX, NDX, DJI, EUR/USD, GBP/USD)
   - **Timeframe selector** (1m, 5m, 15m, 1h, 4h, 1d)
   - **EMA indicators** overlaid on chart

---

## Troubleshooting

### Problem: "No market data available"

**Possible causes:**

1. **Celery worker not running**
   - Solution: Start with `./start_market_data_worker.sh`

2. **Database empty**
   - Solution: Trigger manual fetch:
   ```bash
   cd services/agents
   python -c "
   from src.market_data_tasks import daily_data_refresh
   daily_data_refresh.delay()
   "
   ```

3. **API key invalid**
   - Solution: Test API key with curl (see "Getting Your API Key")

### Problem: "Rate limit exceeded"

**Error message:** `RateLimitError: Rate limit exceeded after 3 retries`

**Solutions:**

1. **Wait 60 seconds** - Rate limit resets every minute
2. **Reduce fetch frequency** - Edit beat schedule in `market_data_tasks.py`
3. **Upgrade Twelve Data plan** - Get more requests/day

### Problem: "Symbol not found in database"

**Error message:** `SymbolNotFoundError: Symbol 'XYZ' not found in market_symbols table`

**Solution:** Add symbol to database:

```sql
INSERT INTO market_symbols (vendor, symbol, alias, tick_size, timezone, active)
VALUES ('twelve_data', 'XYZ', 'XYZ Name', 0.01, 'Europe/Berlin', true);
```

### Problem: Redis connection failed

**Error message:** `ConnectionError: Error 111 connecting to localhost:6379`

**Solution:** Start Redis:

```bash
# Docker
docker run -d -p 6379:6379 redis:7-alpine

# OR macOS
brew services start redis

# OR Linux
sudo systemctl start redis
```

### Problem: Celery task timeout

**Error message:** `SoftTimeLimitExceeded`

**Solution:** Increase timeout in `market_data_tasks.py`:

```python
celery_app.conf.update(
    task_time_limit=600,  # 10 minutes (was 300)
    task_soft_time_limit=540,  # 9 minutes (was 240)
)
```

---

## API Reference

### Twelve Data Endpoints Used

#### 1. Time Series (OHLCV)

**Endpoint:** `GET https://api.twelvedata.com/time_series`

**Parameters:**
- `symbol` - Trading symbol (e.g., "DAX")
- `interval` - Timeframe (1m, 5m, 15m, 1h, 4h, 1d)
- `outputsize` - Number of candles (max: 5000)
- `apikey` - Your API key

**Example:**
```bash
curl "https://api.twelvedata.com/time_series?symbol=DAX&interval=1h&outputsize=100&apikey=YOUR_KEY"
```

#### 2. Quote (Current Price)

**Endpoint:** `GET https://api.twelvedata.com/quote`

**Parameters:**
- `symbol` - Trading symbol
- `apikey` - Your API key

**Example:**
```bash
curl "https://api.twelvedata.com/quote?symbol=DAX&apikey=YOUR_KEY"
```

#### 3. API Usage

**Endpoint:** `GET https://api.twelvedata.com/api_usage`

**Parameters:**
- `apikey` - Your API key

**Example:**
```bash
curl "https://api.twelvedata.com/api_usage?apikey=YOUR_KEY"
```

### TradeMatrix API Routes

#### GET /api/market-data/current

Fetch current prices for all symbols.

**Response:**
```json
{
  "data": [MarketData[]],
  "count": number,
  "timestamp": string
}
```

#### GET /api/market-data/[symbol]/history

Fetch historical OHLCV data for a symbol.

**Query Parameters:**
- `interval` - Timeframe (default: "1h")
- `limit` - Number of candles (default: 500)

**Response:**
```json
{
  "symbol": "DAX",
  "interval": "1h",
  "data": [OHLCV[]],
  "count": number
}
```

#### POST /api/market-data/refresh

Manually trigger data refresh (authenticated users only).

**Body:**
```json
{
  "symbols": ["DAX", "NDX"],  // optional
  "force": true  // optional
}
```

---

## Best Practices

### 1. Rate Limit Management

- **Cache aggressively** - 60-second TTL is optimal
- **Batch requests** - Fetch multiple symbols in one cycle
- **Monitor usage** - Check API usage endpoint hourly

### 2. Error Handling

- **Always retry** on rate limit errors (with backoff)
- **Fall back to cached data** if API fails
- **Log all errors** for debugging

### 3. Production Deployment

- **Use paid plan** - Grow plan ($9.99/mo) for 3000 requests/day
- **Set up monitoring** - Track API usage and errors
- **Enable alerts** - Get notified when approaching rate limits

### 4. Database Maintenance

- **Purge old data** regularly (keep last 6 months)
- **Index optimization** - Ensure indexes on `symbol_id`, `timeframe`, `ts`
- **Backup regularly** - Export critical data

---

## Next Steps

1. ✅ **Get API Key** - Sign up at twelvedata.com
2. ✅ **Configure Environment** - Add key to .env files
3. ✅ **Apply Migrations** - Run migration 009
4. ✅ **Start Workers** - Run Celery worker + beat scheduler
5. ✅ **Test Integration** - Verify data in dashboard
6. 🚀 **Go Live** - Deploy to production!

---

## Support & Resources

### Documentation
- [Twelve Data API Docs](https://twelvedata.com/docs)
- [Celery Documentation](https://docs.celeryproject.org/)
- [Supabase Docs](https://supabase.com/docs)

### TradeMatrix.ai Support
- 📧 Email: support@tradematrix.ai
- 💬 Discord: [Join our community](#)
- 📝 GitHub Issues: [Report bugs](#)

---

**Last Updated:** 2025-10-29
**Version:** 1.0.0
**Author:** TradeMatrix.ai Development Team
