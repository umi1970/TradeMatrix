# Celery Tasks Quick Start

Get up and running with TradeMatrix.ai background tasks in 5 minutes.

## Prerequisites

- ✅ Supabase project created (with migrations 001, 002, 003 applied)
- ✅ Twelve Data API key ([get one here](https://twelvedata.com/))
- ✅ Redis server (Docker or local)
- ✅ Python 3.11+

## Step 1: Install Dependencies

```bash
cd services/agents
pip install -r ../api/requirements.txt
```

## Step 2: Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and set:

```bash
# Required
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key
TWELVEDATA_API_KEY=your-api-key

# Redis (default is fine for local)
REDIS_URL=redis://localhost:6379
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

## Step 3: Start Redis

### Option A: Docker (Recommended)

```bash
docker run -d -p 6379:6379 --name redis redis:7-alpine
```

### Option B: Local Installation

```bash
# Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis

# macOS
brew install redis
brew services start redis

# Verify
redis-cli ping  # Should return "PONG"
```

## Step 4: Verify Database Schema

Make sure migration `003_market_data_schema.sql` is applied in Supabase:

1. Go to Supabase SQL Editor
2. Run the migration from `services/api/supabase/migrations/003_market_data_schema.sql`
3. Verify tables exist: `market_symbols`, `ohlc`, `levels_daily`, `setups`, `alerts`

## Step 5: Start Celery Worker

### Development (Worker + Scheduler)

```bash
./start_worker.sh
# or
cd src && celery -A tasks worker --beat --loglevel=info
```

### Production (Separate Processes)

Terminal 1 - Worker:
```bash
cd src && celery -A tasks worker --loglevel=info
```

Terminal 2 - Beat Scheduler:
```bash
cd src && celery -A tasks beat --loglevel=info
```

## Step 6: Test Tasks

```bash
# Run all tests
python test_tasks.py

# Or test individually
python test_tasks.py connection  # Test Celery connection
python test_tasks.py seed        # Test historical data fetch
python test_tasks.py realtime    # Test real-time pull
python test_tasks.py daily       # Test daily close calculation
python test_tasks.py pivots      # Test pivot calculation
```

## Step 7: Seed Historical Data (Optional)

```python
# In Python REPL or script
from src.tasks import historical_seed_task

# Fetch 30 days of hourly data for DAX
result = historical_seed_task.delay("DAX", "1h", 30)
print(result.get())  # Wait for completion

# For all symbols
symbols = ["DAX", "NDX", "DJI", "EUR/USD", "XAG/USD"]
for symbol in symbols:
    historical_seed_task.delay(symbol, "1h", 30)
```

## Automated Tasks (Celery Beat)

Once running, these tasks execute automatically:

| Task | Schedule | Purpose |
|------|----------|---------|
| `realtime_pull_task` | Every 60 seconds | Fetch latest candles (1m, 5m, 15m, 1h) |
| `daily_close_task` | 20:59 MEZ Mon-Fri | Calculate Y-High/Low/Close |
| `calculate_pivots_task` | 07:55 MEZ Tue-Sat | Calculate PP, R1, R2, S1, S2 |

## Monitoring

### View Active Tasks

```bash
celery -A tasks inspect active
```

### View Scheduled Tasks

```bash
celery -A tasks inspect scheduled
```

### Web UI (Flower)

```bash
pip install flower
celery -A tasks flower

# Open http://localhost:5555
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'config'"

Make sure to run from the correct directory:
```bash
cd services/agents/src
celery -A tasks worker --beat --loglevel=info
```

### "ConnectionError: Redis connection failed"

Check if Redis is running:
```bash
redis-cli ping  # Should return "PONG"
```

If not running:
```bash
docker run -d -p 6379:6379 --name redis redis:7-alpine
```

### "SymbolNotFoundError: Symbol DAX not found"

The migration seeds default symbols. Verify they exist:
```sql
SELECT * FROM market_symbols WHERE active = true;
```

If empty, run the seed data from `003_market_data_schema.sql`.

### "Rate limit exceeded" (Twelve Data)

Free tier: 800 requests/day

Reduce frequency or upgrade:
- Edit `celery.conf.beat_schedule` in `tasks.py`
- Change `realtime_pull_task` schedule to 120s or 300s

## Next Steps

✅ **Monitor Logs**: Watch for any errors or rate limit warnings
✅ **Check Database**: Verify `ohlc` table is being populated
✅ **Set Up Alerts**: Configure email/SMS alerts (optional)
✅ **Deploy to Production**: Use Railway, Fly.io, or Docker

## Production Deployment

### Railway

```bash
# Create Procfile
echo "worker: celery -A tasks worker --loglevel=info" > Procfile
echo "beat: celery -A tasks beat --loglevel=info" >> Procfile

# Deploy
railway up
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

## Support

- 📖 Full docs: `README.md`
- 🐛 Issues: Create GitHub issue
- 💬 Questions: Contact team

---

**Happy Trading! 📈**
