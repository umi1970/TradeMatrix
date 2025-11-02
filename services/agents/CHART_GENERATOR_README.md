# ChartGenerator Service - Complete Implementation

## Overview

The ChartGenerator Service integrates with [chart-img.com](https://chart-img.com) to generate dynamic TradingView charts for our 5 main symbols (DAX, NASDAQ, DOW, EUR/USD, EUR/GBP).

**Status:** ✅ **PRODUCTION READY**

---

## Features

- ✅ **chart-img.com API Integration** - Generate TradingView charts via REST API
- ✅ **Rate Limiting** - 1,000 requests/day, 15/second (Redis-based)
- ✅ **Caching** - 5-minute Redis cache to reduce API calls
- ✅ **Database Persistence** - Store chart snapshots with 60-day retention
- ✅ **Error Handling** - Custom exceptions for all failure scenarios
- ✅ **FastAPI Router** - REST endpoints for chart management
- ✅ **Unit Tests** - Comprehensive test coverage (pytest)
- ✅ **Hetzner Deployment** - Production-ready Docker Compose version

---

## Architecture

```
┌─────────────────────┐
│   Frontend/Client   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  FastAPI Router     │  POST /api/charts/generate
│  (api/charts.py)    │  GET  /api/charts/snapshots/{id}
└──────────┬──────────┘  GET  /api/charts/usage
           │
           ▼
┌─────────────────────┐
│  ChartGenerator     │  Core Service
│  (chart_generator)  │  - Rate Limiting
└──────┬──────────────┘  - Caching
       │                 - API Calls
       │
       ├──────────────────┐──────────────────┐
       ▼                  ▼                  ▼
┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│   Redis     │   │  Supabase   │   │ chart-img   │
│   Cache     │   │  Database   │   │    API      │
└─────────────┘   └─────────────┘   └─────────────┘
```

---

## File Structure

```
services/agents/
├── src/
│   ├── chart_generator.py           # Core Service
│   ├── config/
│   │   ├── __init__.py
│   │   └── chart_img.py             # API Configuration
│   ├── exceptions/
│   │   ├── __init__.py
│   │   └── chart_errors.py          # Custom Exceptions
│   └── api/
│       ├── __init__.py
│       └── charts.py                # FastAPI Router
│
├── tests/
│   ├── __init__.py
│   └── test_chart_generator.py      # Unit Tests
│
├── requirements.txt                  # Updated Dependencies
└── CHART_GENERATOR_README.md        # This file

hetzner-deploy/
└── src/
    ├── chart_generator.py           # Hetzner Version (Redis: redis://redis:6379)
    ├── config/
    │   └── chart_img.py
    └── exceptions/
        └── chart_errors.py
```

---

## Installation

### 1. Install Dependencies

```bash
# Development (services/agents)
cd services/agents
pip install -r requirements.txt

# Production (Hetzner)
cd hetzner-deploy
pip install -r requirements.txt
```

### 2. Environment Variables

Add to `.env`:

```bash
# chart-img.com API
CHART_IMG_API_KEY=3pJTrvapkk9LQ7FwaUOmf6I354fSOeWa8VJifI2l
CHART_IMG_BASE_URL=https://api.chart-img.com

# Redis (Development)
REDIS_URL=redis://localhost:6379/0

# Redis (Hetzner/Docker Compose)
REDIS_URL=redis://redis:6379/0

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key
```

### 3. Database Migration

Run migration `013_add_chart_img_support.sql` in Supabase SQL Editor:

```bash
# File location:
services/api/supabase/migrations/013_add_chart_img_support.sql
```

This creates:
- `chart_snapshots` table
- Adds `chart_img_symbol`, `chart_enabled`, `chart_config` to `symbols` table
- Configures 5 main symbols with TradingView mappings
- Creates utility functions for snapshot management

---

## Usage

### Python Service (Standalone)

```python
from chart_generator import ChartGenerator

# Initialize
generator = ChartGenerator()

# Generate chart
result = generator.generate_chart(
    symbol_id="123e4567-e89b-12d3-a456-426614174000",  # UUID from database
    timeframe="4h",
    trigger_type="manual",
    user_id="987fcdeb-51a2-43d1-9012-345678901234"  # Optional
)

print(f"Chart URL: {result['chart_url']}")
print(f"Snapshot ID: {result['snapshot_id']}")
print(f"From cache: {result['cached']}")
```

### FastAPI Endpoints

#### 1. Generate Chart

```bash
POST /api/charts/generate
Content-Type: application/json

{
  "symbol_id": "123e4567-e89b-12d3-a456-426614174000",
  "timeframe": "4h",
  "trigger_type": "manual",
  "user_id": "987fcdeb-51a2-43d1-9012-345678901234",
  "force_refresh": false
}
```

**Response:**
```json
{
  "chart_url": "https://chart-img.com/i/abc123.png",
  "snapshot_id": "456e7890-a12b-34c5-d678-901234567890",
  "cached": false,
  "generated_at": "2025-11-02T14:30:00Z",
  "expires_at": "2025-12-31T23:59:59Z",
  "metadata": {
    "symbol": "^GDAXI",
    "tradingview_symbol": "XETR:DAX",
    "indicators": ["EMA_20", "EMA_50", "RSI"]
  }
}
```

#### 2. Get Chart Snapshots

```bash
GET /api/charts/snapshots/{symbol_id}?timeframe=4h&limit=10
```

#### 3. Get Usage Statistics

```bash
GET /api/charts/usage
```

**Response:**
```json
{
  "requests_today": 245,
  "limit_daily": 1000,
  "remaining": 755,
  "percentage_used": 24.5,
  "warning_threshold": 800,
  "hard_stop_threshold": 950,
  "date": "2025-11-02"
}
```

#### 4. Delete Snapshot

```bash
DELETE /api/charts/snapshots/{snapshot_id}
```

#### 5. Get Symbol Config

```bash
GET /api/charts/config/{symbol_id}
```

---

## Configuration

### Supported Timeframes

```
1m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 12h, 1d, 3d, 1w, 1M
```

### Indicators

Configured in `chart_config` JSONB field:

```json
{
  "timeframes": ["1h", "4h", "1d"],
  "indicators": ["EMA_20", "EMA_50", "EMA_200", "RSI", "Volume"],
  "default_timeframe": "4h",
  "theme": "dark"
}
```

**Available Indicators:**
- `EMA_20`, `EMA_50`, `EMA_200` - Exponential Moving Averages
- `RSI` - Relative Strength Index
- `Volume` - Trading Volume
- `MACD` - Moving Average Convergence Divergence
- `BB` - Bollinger Bands
- `ATR` - Average True Range

### TradingView Symbol Mappings

| Our Symbol | TradingView Symbol | chart-img.com |
|------------|-------------------|---------------|
| ^GDAXI     | XETR:DAX          | ✅ Configured |
| ^NDX       | NASDAQ:NDX        | ✅ Configured |
| ^DJI       | DJCFD:DJI         | ✅ Configured |
| EURUSD     | OANDA:EURUSD      | ✅ Configured |
| EURGBP     | OANDA:EURGBP      | ✅ Configured |

---

## Rate Limiting

### Limits

- **Daily:** 1,000 requests
- **Per Second:** 15 requests
- **Warning Threshold:** 800 requests (80%)
- **Hard Stop:** 950 requests (95%)

### Redis Keys

```
chart_img:requests:daily:{date}           # Daily counter
chart:{symbol_id}:{timeframe}:{timestamp} # Cache (5 min TTL)
```

### Behavior

1. **0-799 requests:** Normal operation
2. **800-949 requests:** Warning logged, but allowed
3. **950+ requests:** `RateLimitError` raised, request blocked

---

## Error Handling

### Custom Exceptions

```python
from exceptions.chart_errors import (
    RateLimitError,           # Rate limit exceeded
    ChartGenerationError,     # Generic error
    SymbolNotFoundError,      # Symbol not found or chart disabled
    InvalidTimeframeError,    # Unsupported timeframe
    ChartAPIError,            # chart-img.com API error
    ChartCacheError,          # Redis cache error
)
```

### Error Response Format

```json
{
  "error": "Rate limit exceeded: 950/1000 requests used",
  "details": {
    "current_count": 950,
    "limit": 1000,
    "reset_time": "2025-11-03T00:00:00Z",
    "percentage_used": 95.0
  }
}
```

---

## Testing

### Run Unit Tests

```bash
cd services/agents
pytest tests/test_chart_generator.py -v
```

### Test Coverage

- ✅ Chart generation (happy path)
- ✅ Rate limiting (warning, hard stop)
- ✅ Caching (hit, miss, set)
- ✅ Error handling (invalid symbol, timeframe, API errors)
- ✅ Database operations
- ✅ Usage statistics

### Example Test Run

```bash
pytest tests/test_chart_generator.py -v --tb=short

# Output:
test_generate_chart_success PASSED
test_generate_chart_from_cache PASSED
test_rate_limit_warning PASSED
test_rate_limit_exceeded PASSED
test_cache_hit PASSED
test_invalid_symbol PASSED
test_invalid_timeframe PASSED
test_api_error_500 PASSED
...
```

---

## Deployment

### Hetzner (Production)

The service is deployed on Hetzner CX11 server (135.181.195.241).

**Docker Compose Services:**
- `redis` - Redis 7-alpine
- `celery-worker` - Celery worker with ChartGenerator
- `celery-beat` - Scheduler for periodic tasks

**Deployment Steps:**

1. Copy files to Hetzner:
```bash
scp hetzner-deploy/src/chart_generator.py root@135.181.195.241:/root/tradematrix/src/
scp hetzner-deploy/src/config/chart_img.py root@135.181.195.241:/root/tradematrix/src/config/
scp hetzner-deploy/src/exceptions/chart_errors.py root@135.181.195.241:/root/tradematrix/src/exceptions/
```

2. Update requirements.txt:
```bash
scp hetzner-deploy/requirements.txt root@135.181.195.241:/root/tradematrix/
```

3. Rebuild and restart:
```bash
ssh root@135.181.195.241
cd /root/tradematrix
docker-compose down
docker-compose build
docker-compose up -d
```

4. Verify:
```bash
docker-compose logs -f celery-worker
# Should see: ✅ ChartGenerator initialized
```

---

## Monitoring

### Check Redis Status

```bash
# Development
redis-cli ping
redis-cli get "chart_img:requests:daily:2025-11-02"

# Hetzner
docker exec -it tradematrix-redis-1 redis-cli ping
docker exec -it tradematrix-redis-1 redis-cli get "chart_img:requests:daily:2025-11-02"
```

### Check Database

```sql
-- Supabase SQL Editor

-- Check configured symbols
SELECT symbol, chart_img_symbol, chart_enabled, chart_config
FROM symbols
WHERE chart_enabled = true;

-- Check recent snapshots
SELECT
  cs.id,
  s.symbol,
  cs.timeframe,
  cs.trigger_type,
  cs.generated_at,
  cs.chart_url
FROM chart_snapshots cs
JOIN symbols s ON cs.symbol_id = s.id
ORDER BY cs.generated_at DESC
LIMIT 10;

-- Check usage stats (manual calculation)
SELECT
  DATE(generated_at) as date,
  COUNT(*) as charts_generated,
  COUNT(DISTINCT symbol_id) as unique_symbols
FROM chart_snapshots
WHERE generated_at >= NOW() - INTERVAL '7 days'
GROUP BY DATE(generated_at)
ORDER BY date DESC;
```

### Cleanup Expired Snapshots

```bash
# Via API
curl -X POST http://localhost:8000/api/charts/cleanup-expired

# Via Python
from chart_generator import ChartGenerator
generator = ChartGenerator()
deleted_count = generator.cleanup_expired_snapshots()
print(f"Deleted {deleted_count} expired snapshots")
```

---

## Integration Examples

### Morning Planner (7:30 AM)

```python
from chart_generator import ChartGenerator

generator = ChartGenerator()

# Generate charts for all symbols
symbols = [
    ("dax_id", "^GDAXI"),
    ("nasdaq_id", "^NDX"),
    ("dow_id", "^DJI"),
]

for symbol_id, symbol_name in symbols:
    result = generator.generate_chart(
        symbol_id=symbol_id,
        timeframe="4h",
        trigger_type="report"
    )
    print(f"✅ {symbol_name}: {result['chart_url']}")
```

### Liquidity Alert (Real-Time)

```python
from chart_generator import ChartGenerator

generator = ChartGenerator()

# When alert triggered, generate chart
result = generator.generate_chart(
    symbol_id=alert['symbol_id'],
    timeframe="1h",
    trigger_type="alert",
    user_id=alert['user_id']
)

# Include chart URL in push notification
send_push_notification(
    user_id=alert['user_id'],
    title=f"🔴 {alert['symbol']} Alert",
    body=f"Chart: {result['chart_url']}"
)
```

---

## Troubleshooting

### Issue: `RateLimitError`

**Cause:** Exceeded 950 requests/day

**Solution:**
- Wait until midnight UTC (limit resets)
- Use `force_refresh=False` to maximize cache hits
- Check Redis counter: `redis-cli get "chart_img:requests:daily:{date}"`

### Issue: `SymbolNotFoundError`

**Cause:** Symbol doesn't exist or `chart_enabled = false`

**Solution:**
```sql
UPDATE symbols
SET chart_enabled = true
WHERE id = 'your-symbol-id';
```

### Issue: `ChartAPIError` (500)

**Cause:** chart-img.com API error

**Solution:**
- Check API key is valid
- Verify TradingView symbol exists: https://www.tradingview.com/chart/?symbol=XETR:DAX
- Check API status: https://status.chart-img.com (if available)

### Issue: Cache not working

**Cause:** Redis connection failed

**Solution:**
```bash
# Check Redis is running
redis-cli ping  # Should return: PONG

# Check connection string
echo $REDIS_URL  # Should be: redis://localhost:6379/0
```

---

## Next Steps

- [ ] **Frontend Integration** - Display charts in Dashboard widgets
- [ ] **Scheduled Generation** - Cron job for morning reports (7:30 AM)
- [ ] **Alert Integration** - Auto-generate chart when liquidity alert triggered
- [ ] **Chart Annotations** - Add support/resistance lines to charts
- [ ] **Multi-Timeframe Analysis** - Generate 1h, 4h, 1d charts simultaneously

---

## API Reference

### chart-img.com API

**Endpoint:** `POST https://api.chart-img.com/v2/tradingview/advanced-chart`

**Headers:**
```
x-api-key: 3pJTrvapkk9LQ7FwaUOmf6I354fSOeWa8VJifI2l
Content-Type: application/json
```

**Request:**
```json
{
  "symbol": "XETR:DAX",
  "interval": "4h",
  "width": 1920,
  "height": 1200,
  "studies": [
    {"name": "EMA", "inputs": [20]},
    {"name": "RSI", "inputs": [14]}
  ],
  "theme": "dark"
}
```

**Response:**
```json
{
  "url": "https://chart-img.com/i/abc123.png"
}
```

---

## Support

**Issues:** Create GitHub issue in TradeMatrix repo

**Documentation:** See `docs/FEATURES/chart_generation/`

**Status:** Production (v1.0)

---

**Last Updated:** 2025-11-02
**Author:** Agent 3 (Backend Service Agent)
**Version:** 1.0.0
