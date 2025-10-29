# TradeMatrix.ai - Celery Background Agents

This module contains Celery background tasks for automated market data ingestion, analysis, and trading operations.

## Features

- **Historical Data Seeding**: One-time fetch of historical OHLCV data
- **Real-time Data Ingestion**: Continuous updates every 60 seconds
- **Daily Levels Calculation**: Calculate Yesterday's High/Low/Close at market close
- **Pivot Points**: Automatic calculation of PP, R1, R2, S1, S2 before market open
- **AI Agents**: (Planned) ChartWatcher, SignalBot, RiskManager, JournalBot

## Architecture

```
┌─────────────────────────────────────────────┐
│         Celery Beat (Scheduler)             │
│  - realtime_pull_task: Every 60s            │
│  - daily_close_task: 20:59 MEZ Mon-Fri      │
│  - calculate_pivots_task: 07:55 MEZ Tue-Sat │
└──────────────┬──────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────┐
│         Celery Workers                       │
│  - Process background tasks                 │
│  - Fetch data from Twelve Data API          │
│  - Store in Supabase                        │
└──────────────┬──────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────┐
│         Redis (Message Broker)              │
│  - Task queue                               │
│  - Result backend                           │
│  - Caching                                  │
└─────────────────────────────────────────────┘
```

## Prerequisites

1. **Redis Server** (for Celery broker)
2. **Supabase Project** (database & auth)
3. **Twelve Data API Key** (for market data)
4. **Python 3.11+**

## Setup

### 1. Install Dependencies

```bash
cd services/agents
pip install -r ../api/requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your API keys
```

Required environment variables:
- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_SERVICE_KEY`: Service role key (admin access)
- `TWELVEDATA_API_KEY`: Twelve Data API key
- `REDIS_URL`: Redis connection string
- `CELERY_BROKER_URL`: Celery broker URL
- `CELERY_RESULT_BACKEND`: Celery result backend URL

### 3. Start Redis (Docker)

```bash
docker run -d -p 6379:6379 --name redis redis:7-alpine
```

Or install locally:
```bash
# Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis

# macOS
brew install redis
brew services start redis
```

### 4. Run Database Migrations

Make sure the market data schema is applied to Supabase:

```sql
-- In Supabase SQL Editor, run:
-- services/api/supabase/migrations/003_market_data_schema.sql
```

## Running the Workers

### Start Celery Worker

```bash
cd services/agents/src
celery -A tasks worker --loglevel=info
```

### Start Celery Beat (Scheduler)

```bash
cd services/agents/src
celery -A tasks beat --loglevel=info
```

### Start Both (Development)

```bash
cd services/agents/src
celery -A tasks worker --beat --loglevel=info
```

## Available Tasks

### 1. Historical Seed Task

Fetch historical data for a symbol (one-time):

```python
from tasks import historical_seed_task

# Fetch 30 days of 1h data for DAX
result = historical_seed_task.delay("DAX", "1h", 30)
print(result.get())  # Wait for completion
```

**Parameters:**
- `symbol`: Trading symbol (e.g., "DAX", "NDX", "EUR/USD")
- `interval`: Timeframe (1m, 5m, 15m, 1h, 1d)
- `days`: Number of days to fetch (max 365)

### 2. Real-time Pull Task

Fetch latest candles for all active symbols (automatic):

```python
from tasks import realtime_pull_task

# Manually trigger (runs automatically every 60s)
result = realtime_pull_task.delay()
print(result.get())
```

**Schedule:** Every 60 seconds
**Timeframes:** 1m, 5m, 15m, 1h

### 3. Daily Close Task

Calculate yesterday's H/L/C levels (automatic):

```python
from tasks import daily_close_task

# Manually trigger (runs automatically at 20:59 MEZ)
result = daily_close_task.delay()
print(result.get())
```

**Schedule:** 20:59 MEZ, Monday-Friday
**Purpose:** Save Y-High, Y-Low, Y-Close to `levels_daily` table

### 4. Calculate Pivots Task

Calculate pivot points for today (automatic):

```python
from tasks import calculate_pivots_task

# Manually trigger (runs automatically at 07:55 MEZ)
result = calculate_pivots_task.delay()
print(result.get())
```

**Schedule:** 07:55 MEZ, Tuesday-Saturday
**Purpose:** Calculate PP, R1, R2, S1, S2 based on yesterday's data

**Formula:**
```
PP = (High + Low + Close) / 3
R1 = (2 * PP) - Low
R2 = PP + (High - Low)
S1 = (2 * PP) - High
S2 = PP - (High - Low)
```

### 5. Test Connection

Verify Celery is working:

```python
from tasks import test_connection

result = test_connection.delay()
print(result.get())  # {'status': 'success', 'message': 'Celery is working!'}
```

## Monitoring

### Check Task Status

```python
from celery.result import AsyncResult

# Get task result
task = AsyncResult('task-id-here')
print(task.state)  # PENDING, STARTED, SUCCESS, FAILURE
print(task.result)
```

### View Active Tasks

```bash
celery -A tasks inspect active
```

### View Scheduled Tasks

```bash
celery -A tasks inspect scheduled
```

### Flower (Web UI)

Install Flower for a web-based monitoring interface:

```bash
pip install flower
celery -A tasks flower
```

Access at: http://localhost:5555

## Database Schema

### market_symbols

Stores tradable symbols:

```sql
id, vendor, symbol, alias, tick_size, timezone, active
```

### ohlc

Stores OHLCV candles:

```sql
id, ts, symbol_id, timeframe, open, high, low, close, volume
```

### levels_daily

Stores daily levels and pivots:

```sql
id, trade_date, symbol_id, pivot, r1, r2, s1, s2, y_high, y_low, y_close
```

## Error Handling

All tasks include:
- ✅ Automatic retry on failure (max 3 retries)
- ✅ Exponential backoff
- ✅ Comprehensive logging
- ✅ Error tracking in `agent_logs` table

## Rate Limiting

**Twelve Data Free Tier:** 800 requests/day

**Strategy:**
- Real-time pulls: 4 timeframes × 5 symbols × 1440 min/day = ~28,800 candles/day
- Actual API calls: ~1440 calls/day (within limit)
- Use `outputsize=2` for real-time to minimize calls

## Production Deployment

### Railway/Fly.io

1. Create `Procfile`:
```
worker: celery -A tasks worker --loglevel=info
beat: celery -A tasks beat --loglevel=info
```

2. Deploy:
```bash
railway up
# or
fly deploy
```

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY services/agents/src .

CMD celery -A tasks worker --beat --loglevel=info
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'config'"

Make sure you're running from the correct directory:
```bash
cd services/agents/src
```

### "ConnectionError: Redis connection failed"

Start Redis:
```bash
docker run -d -p 6379:6379 redis:7-alpine
```

### "Rate limit exceeded"

Wait for the rate limit to reset (24 hours) or upgrade your Twelve Data plan.

### "No active symbols found"

Ensure symbols are seeded in `market_symbols` table:
```sql
INSERT INTO market_symbols (vendor, symbol, alias, active) VALUES
  ('twelve_data', 'DAX', 'DAX 40', true);
```

## Development

### Add New Task

1. Define task in `tasks.py`:
```python
@celery.task(name='my_custom_task')
def my_custom_task(param):
    logger.info(f"Running custom task with {param}")
    return {"result": "success"}
```

2. Add to beat schedule (if periodic):
```python
celery.conf.beat_schedule = {
    'my-custom-task': {
        'task': 'my_custom_task',
        'schedule': crontab(hour=9, minute=0),
    }
}
```

3. Test manually:
```python
from tasks import my_custom_task
result = my_custom_task.delay("test")
print(result.get())
```

## Contributing

When adding new tasks:
1. Add proper error handling
2. Include logging statements
3. Update this README
4. Add type hints
5. Write tests

## License

© 2025 TradeMatrix.ai - All Rights Reserved
