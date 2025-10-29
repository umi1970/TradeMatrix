# Market Data Workers - Quick Start Guide

**Background workers for fetching live market data from Twelve Data API**

---

## Overview

This directory contains Celery workers that fetch and store market data:

- **Realtime prices** - Updated every 1 minute
- **Historical OHLCV data** - Multiple timeframes (1m, 5m, 15m, 1h, 4h, 1d)
- **Daily data refresh** - Complete data sync at 2:00 AM UTC
- **API usage monitoring** - Track rate limits

---

## Quick Start

### 1. Prerequisites

**Install Redis:**

```bash
# Docker (recommended)
docker run -d -p 6379:6379 --name redis redis:7-alpine

# OR macOS
brew install redis && brew services start redis

# OR Ubuntu/Debian
sudo apt-get install redis-server && sudo systemctl start redis
```

**Install Python dependencies:**

```bash
cd services/agents
pip install -r ../api/requirements.txt
```

### 2. Configuration

**Create `.env` file:**

```bash
cp .env.example .env
```

**Edit `.env` and add:**

```bash
# Twelve Data API
TWELVE_DATA_API_KEY=your_api_key_here

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key

# Redis
REDIS_URL=redis://localhost:6379
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### 3. Start Workers

**Terminal 1 - Celery Worker:**

```bash
./start_market_data_worker.sh
```

**Terminal 2 - Celery Beat Scheduler:**

```bash
./start_beat_scheduler.sh
```

### 4. Verify

**Check worker status:**

```bash
celery -A src.market_data_tasks inspect active
```

**Trigger manual fetch:**

```bash
python -c "
from src.market_data_tasks import fetch_realtime_prices
result = fetch_realtime_prices.delay()
print('Task ID:', result.id)
print('Result:', result.get(timeout=30))
"
```

---

## Scheduled Tasks

| Task | Schedule | Description |
|------|----------|-------------|
| `fetch_realtime_prices` | Every 1 minute | Fetch current prices for all symbols |
| `daily_data_refresh` | 2:00 AM UTC | Full data refresh for all symbols/timeframes |
| `check_api_usage` | Every hour | Monitor Twelve Data API usage |

---

## Manual Task Execution

### Fetch Historical Data

```python
from src.market_data_tasks import fetch_historical_data

# Fetch 500 hourly candles for DAX
result = fetch_historical_data.delay('DAX', '1h', 500)
print(result.get(timeout=60))
```

### Update Single Symbol

```python
from src.market_data_tasks import update_symbol_data

# Update DAX across all timeframes
result = update_symbol_data.delay('DAX')
print(result.get(timeout=120))
```

### Trigger Full Refresh

```python
from src.market_data_tasks import daily_data_refresh

# Refresh all symbols
result = daily_data_refresh.delay()
print(result.get(timeout=300))
```

---

## Testing

### Run Unit Tests

```bash
cd services/agents
pytest test_market_data_integration.py -v
```

### Run Integration Tests (requires API key)

```bash
pytest test_market_data_integration.py -v --markers=integration
```

---

## Monitoring

### View Worker Logs

```bash
tail -f logs/market_data_worker.log
```

### View Beat Scheduler Logs

```bash
tail -f logs/beat_scheduler.log
```

### Check Redis Queue

```bash
redis-cli -h localhost -p 6379
> KEYS celery*
> LLEN celery
```

---

## Troubleshooting

### Worker Not Starting

**Problem:** Permission denied

```bash
chmod +x start_market_data_worker.sh
chmod +x start_beat_scheduler.sh
```

**Problem:** Redis connection failed

```bash
# Check Redis is running
redis-cli ping
# Should return: PONG
```

### No Data in Database

**Check migration 009 is applied:**

```sql
SELECT EXISTS (
  SELECT 1 FROM information_schema.tables
  WHERE table_name = 'current_prices'
);
```

**Manually trigger data fetch:**

```python
from src.market_data_tasks import daily_data_refresh
result = daily_data_refresh.delay()
```

### Rate Limit Errors

**Reduce fetch frequency in `market_data_tasks.py`:**

```python
celery_app.conf.beat_schedule = {
    'fetch-realtime-prices-every-minute': {
        'task': 'market_data.fetch_realtime_prices',
        'schedule': 120.0,  # Every 2 minutes instead of 1
    }
}
```

---

## Production Deployment

### Using Supervisor (Linux)

**Install Supervisor:**

```bash
sudo apt-get install supervisor
```

**Create config:** `/etc/supervisor/conf.d/tradematrix_workers.conf`

```ini
[program:tradematrix_worker]
command=/path/to/venv/bin/celery -A src.market_data_tasks worker --loglevel=info
directory=/path/to/TradeMatrix/services/agents
user=tradematrix
autostart=true
autorestart=true
stopwaitsecs=600
stdout_logfile=/var/log/tradematrix/worker.log
stderr_logfile=/var/log/tradematrix/worker_err.log

[program:tradematrix_beat]
command=/path/to/venv/bin/celery -A src.market_data_tasks beat --loglevel=info
directory=/path/to/TradeMatrix/services/agents
user=tradematrix
autostart=true
autorestart=true
stdout_logfile=/var/log/tradematrix/beat.log
stderr_logfile=/var/log/tradematrix/beat_err.log
```

**Start services:**

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start tradematrix_worker
sudo supervisorctl start tradematrix_beat
```

### Using Docker

**Create `docker-compose.yml`:**

```yaml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  worker:
    build: .
    command: celery -A src.market_data_tasks worker --loglevel=info
    depends_on:
      - redis
    env_file:
      - .env

  beat:
    build: .
    command: celery -A src.market_data_tasks beat --loglevel=info
    depends_on:
      - redis
    env_file:
      - .env
```

**Start:**

```bash
docker-compose up -d
```

---

## Files Overview

```
services/agents/
├── src/
│   ├── market_data_tasks.py      # Celery tasks
│   └── __init__.py
├── test_market_data_integration.py  # Test suite
├── start_market_data_worker.sh    # Worker startup script
├── start_beat_scheduler.sh        # Beat scheduler script
├── .env.example                   # Environment template
├── README_MARKET_DATA.md          # This file
└── logs/                          # Worker logs (created on first run)
```

---

## Support

- **Documentation:** [/docs/TWELVE_DATA_SETUP.md](../../docs/TWELVE_DATA_SETUP.md)
- **Issues:** Report bugs in GitHub Issues
- **Community:** Join our Discord

---

**Last Updated:** 2025-10-29
