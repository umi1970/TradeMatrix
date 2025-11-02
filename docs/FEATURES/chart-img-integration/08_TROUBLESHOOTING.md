# Troubleshooting Guide

## Common Issues & Solutions

---

## 1. Rate Limit Exceeded

### Symptom
```
ERROR: Rate limit exceeded (1000/1000)
Exception: Rate limit exceeded
```

### Root Cause
- Daily API limit reached (1,000 requests/day)
- OR Per-second limit exceeded (15 requests/sec)

### Solution

**Check Current Usage**:
```bash
# SSH into server
ssh root@135.181.195.241

# Check Redis counter
docker-compose exec redis redis-cli GET chart_api:daily:$(date +%Y-%m-%d)
```

**If Daily Limit Reached**:
```python
# Option 1: Use cached charts only
chart_service.redis_client.get(cache_key)  # Returns cached URL

# Option 2: Wait until midnight UTC (reset)
# Check remaining time:
from datetime import datetime, timedelta
now = datetime.utcnow()
midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0)
wait_seconds = (midnight - now).total_seconds()
print(f"Wait {wait_seconds/3600:.1f} hours for reset")

# Option 3: Reduce chart generation frequency
# Edit Celery beat schedule to run less often
```

**If Per-Second Limit Exceeded**:
```python
# Add delay between requests
import asyncio

for symbol in symbols:
    await chart_service.generate_chart_url(symbol, "M15")
    await asyncio.sleep(0.1)  # 100ms delay = max 10/sec
```

**Emergency Reset** (Use only if necessary):
```bash
# Delete daily counter (resets to 0)
docker-compose exec redis redis-cli DEL chart_api:daily:$(date +%Y-%m-%d)

# ⚠️ WARNING: This bypasses rate limiting! Use only for debugging.
```

---

## 2. Chart URL Not Accessible

### Symptom
```
HTTPError: 404 Not Found
Image not loading in browser
```

### Root Cause
- Invalid TradingView symbol
- Chart URL expired (60 days retention)
- chart-img.com API issue

### Solution

**Verify Symbol Mapping**:
```python
from src.chart_service import ChartService

service = ChartService()
tv_symbol = service.map_symbol("^GDAXI")
print(tv_symbol)  # Should print: XETR:DAX

# If wrong, update SYMBOL_MAPPING in chart_service.py
```

**Test Chart URL Manually**:
```bash
# Replace with your actual chart URL
curl -I "https://api.chart-img.com/tradingview/advanced-chart?symbol=XETR:DAX&interval=15&theme=dark&width=800&height=600"

# Expected: HTTP/1.1 200 OK
# If 404: Symbol or parameters are wrong
```

**Check Chart Expiration**:
```sql
-- Find expired charts
SELECT id, symbol_id, created_at, expires_at
FROM chart_snapshots
WHERE expires_at < NOW();

-- Delete expired charts
DELETE FROM chart_snapshots WHERE expires_at < NOW();
```

**Regenerate Chart**:
```python
# If chart expired, regenerate
result = await chart_service.generate_chart_url(
    symbol="^GDAXI",
    timeframe="M15",
    save_snapshot=True,
    agent_name="Manual"
)
print(result["chart_url"])
```

---

## 3. Symbol Mapping Incorrect

### Symptom
```
Chart shows wrong symbol or "Symbol not found"
```

### Root Cause
- Yahoo symbol not mapped to TradingView symbol
- Typo in SYMBOL_MAPPING

### Solution

**Find Correct TradingView Symbol**:
1. Go to https://tradingview.com
2. Search for your instrument (e.g., "DAX")
3. Look at URL: `https://tradingview.com/chart/?symbol=XETR:DAX`
4. Symbol is: `XETR:DAX`

**Update SYMBOL_MAPPING**:
```python
# File: hetzner-deploy/src/chart_service.py

SYMBOL_MAPPING = {
    "^GDAXI": "XETR:DAX",        # ✅ Correct
    "^NDX": "NASDAQ:NDX",        # ✅ Correct
    "^DJI": "DJCFD:DJI",         # ✅ Correct (CFD)
    "EURUSD=X": "OANDA:EURUSD",  # ✅ Correct
    "EURGBP=X": "OANDA:EURGBP",  # ✅ Correct

    # Add new symbols:
    "GBPUSD=X": "OANDA:GBPUSD",
    "BTC-USD": "BINANCE:BTCUSDT",
    "ETH-USD": "BINANCE:ETHUSDT",
}
```

**Rebuild & Restart**:
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

---

## 4. Database Connection Failed

### Symptom
```
Error fetching chart config: connection refused
supabase.exceptions.APIError
```

### Root Cause
- Supabase credentials wrong
- RLS policies blocking access
- Network issue

### Solution

**Verify Environment Variables**:
```bash
# Check if variables are set
docker-compose exec celery-worker env | grep SUPABASE

# Should show:
# SUPABASE_URL=https://your-project.supabase.co
# SUPABASE_SERVICE_KEY=eyJhbGc...
```

**Test Supabase Connection**:
```python
# In container Python shell
from supabase import create_client
import os

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")
)

# Test query
result = supabase.table("market_symbols").select("*").limit(1).execute()
print(result.data)  # Should print 1 row
```

**Check RLS Policies**:
```sql
-- Verify service role has access
SELECT schemaname, tablename, policyname
FROM pg_policies
WHERE tablename IN ('market_symbols', 'chart_snapshots');

-- Ensure "Service role has full access" policy exists
```

**Regenerate Service Key** (if compromised):
1. Go to Supabase Dashboard → Settings → API
2. Click "Regenerate" for Service Role Key
3. Update `.env` with new key
4. Restart containers

---

## 5. Redis Connection Failed

### Symptom
```
redis.exceptions.ConnectionError: Error connecting to Redis
```

### Root Cause
- Redis container not running
- Wrong Redis host/port
- Redis out of memory

### Solution

**Check Redis Container**:
```bash
docker-compose ps redis

# If not running:
docker-compose up -d redis
```

**Test Redis Connection**:
```bash
docker-compose exec redis redis-cli PING
# Expected: PONG

# Check memory usage
docker-compose exec redis redis-cli INFO memory | grep used_memory_human
```

**Verify Redis Configuration**:
```bash
# Check environment variables
docker-compose exec celery-worker env | grep REDIS

# Should show:
# REDIS_HOST=redis
# REDIS_PORT=6379
```

**Clear Redis Cache** (if corrupted):
```bash
docker-compose exec redis redis-cli FLUSHDB
# ⚠️ WARNING: This deletes all cached data!
```

---

## 6. Chart Generation Slow

### Symptom
```
Chart generation takes > 5 seconds
Timeout errors
```

### Root Cause
- No caching enabled
- Large chart dimensions
- Slow network to chart-img.com

### Solution

**Enable/Verify Caching**:
```python
# Check if cache is working
cache_key = chart_service.get_cache_key("^GDAXI", "M15", [])
cached = chart_service.redis_client.get(cache_key)

if cached:
    print("Cache working!")
else:
    print("Cache miss - first request or expired")
```

**Reduce Chart Dimensions**:
```python
# Instead of 1920x1600 (max), use smaller size
config["width"] = 1200
config["height"] = 800

# Faster download & processing
```

**Increase Timeouts**:
```python
# In chart_service.py
async with httpx.AsyncClient(timeout=30.0) as client:  # Increase from 10s
    response = await client.get(chart_url)
```

**Use Async Requests**:
```python
# Generate multiple charts in parallel
tasks = [
    chart_service.generate_chart_url("^GDAXI", "M15"),
    chart_service.generate_chart_url("^NDX", "M15"),
    chart_service.generate_chart_url("^DJI", "M15"),
]
results = await asyncio.gather(*tasks)
```

---

## 7. Frontend Modal Not Opening

### Symptom
```
Click "Chart Config" button → Nothing happens
Console error: "ChartConfigModal is not defined"
```

### Root Cause
- Component not imported
- Build error
- TypeScript error

### Solution

**Check Console Errors**:
```bash
# Open browser console (F12)
# Look for errors like:
# - Module not found
# - TypeScript error
# - Component rendering error
```

**Verify Import**:
```typescript
// In MarketSymbolsCard.tsx
import ChartConfigButton from "@/components/charts/ChartConfigButton";

// Check path is correct
```

**Rebuild Frontend**:
```bash
cd apps/web
npm run build

# If errors, fix them first
npm run dev  # Check error messages
```

**Clear Next.js Cache**:
```bash
rm -rf .next
npm run dev
```

---

## 8. Snapshot Not Saving to Database

### Symptom
```
Chart URL generated successfully
But snapshot_id is None
No entry in chart_snapshots table
```

### Root Cause
- RLS policy blocking insert
- Symbol not found in market_symbols
- Database error

### Solution

**Check Logs**:
```python
# Look for error message
print(f"Error saving chart snapshot: {e}")
```

**Verify Symbol Exists**:
```sql
SELECT id, symbol FROM market_symbols WHERE symbol = '^GDAXI';
-- Should return 1 row
```

**Check RLS Policies**:
```sql
-- Temporarily disable RLS (for debugging only!)
ALTER TABLE chart_snapshots DISABLE ROW LEVEL SECURITY;

-- Try saving snapshot
-- ...

-- Re-enable RLS
ALTER TABLE chart_snapshots ENABLE ROW LEVEL SECURITY;
```

**Use Service Role Key**:
```python
# Ensure using service_role key (not anon key)
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")  # NOT SUPABASE_ANON_KEY
)
```

---

## 9. Celery Task Not Running

### Symptom
```
Chart generation task scheduled but never executes
No logs from ChartWatcher/MorningPlanner
```

### Root Cause
- Celery worker not running
- Task not registered
- Celery beat not running

### Solution

**Check Celery Worker**:
```bash
docker-compose ps celery-worker

# If not running:
docker-compose up -d celery-worker

# Check logs
docker-compose logs -f celery-worker
```

**Check Celery Beat** (scheduler):
```bash
docker-compose ps celery-beat

# If not running:
docker-compose up -d celery-beat

# Check logs
docker-compose logs -f celery-beat | grep -i schedule
```

**Verify Task Registration**:
```bash
# List registered tasks
docker-compose exec celery-worker celery -A src.tasks inspect registered

# Should show:
# chart_watcher.analyze_all_symbols
# morning_planner.generate_report
# etc.
```

**Trigger Task Manually**:
```bash
# Test if task works
docker-compose exec celery-worker celery -A src.tasks call chart_watcher.analyze_all_symbols

# Check output for errors
```

---

## 10. API Key Invalid

### Symptom
```
HTTPError: 401 Unauthorized
Invalid API key
```

### Root Cause
- API key typo in .env
- API key expired/revoked
- API key not activated

### Solution

**Verify API Key**:
```bash
# Check .env file
cat .env | grep CHART_IMG_API_KEY

# Should be:
# CHART_IMG_API_KEY=3pJTrvapkk9LQ7FwaUOmf6I354fSOeWa8VJifI2l
```

**Test API Key Manually**:
```bash
curl "https://api.chart-img.com/tradingview/advanced-chart?symbol=XETR:DAX&interval=15&theme=dark&width=800&height=600" \
  -H "X-API-Key: 3pJTrvapkk9LQ7FwaUOmf6I354fSOeWa8VJifI2l"

# Expected: Image or success response
# If 401: Key is invalid
```

**Regenerate API Key**:
1. Login to chart-img.com dashboard
2. Navigate to API Keys
3. Regenerate key
4. Update `.env` file
5. Restart containers

---

## Debug Commands

### Check Service Health

```bash
# All containers running?
docker-compose ps

# Redis accessible?
docker-compose exec redis redis-cli PING

# Supabase accessible?
docker-compose exec celery-worker python -c "from supabase import create_client; import os; print(create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_KEY')).table('market_symbols').select('*').limit(1).execute())"

# Chart API accessible?
curl -I https://api.chart-img.com
```

### Check Logs

```bash
# All logs
docker-compose logs -f

# Specific service
docker-compose logs -f celery-worker
docker-compose logs -f celery-beat
docker-compose logs -f redis

# Filter logs
docker-compose logs celery-worker | grep -i error
docker-compose logs celery-worker | grep -i chart
```

### Check Resource Usage

```bash
# Docker stats
docker stats

# Redis memory
docker-compose exec redis redis-cli INFO memory

# Disk space
df -h
```

### Reset Everything (Emergency)

```bash
# ⚠️ WARNING: This will delete all data!

# Stop containers
docker-compose down

# Remove volumes
docker volume rm tradematrix-agents_redis_data

# Rebuild
docker-compose build --no-cache

# Start
docker-compose up -d

# Verify
docker-compose ps
```

---

## Monitoring Best Practices

### Daily Checks

```bash
# Check rate limit usage
docker-compose exec redis redis-cli GET chart_api:daily:$(date +%Y-%m-%d)

# Check chart snapshot count
docker-compose exec celery-worker python -c "from supabase import create_client; import os; print(create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_KEY')).table('chart_snapshots').select('count').execute())"

# Check for errors in logs
docker-compose logs --since 24h celery-worker | grep -i error
```

### Weekly Checks

```bash
# Cleanup expired snapshots
docker-compose exec celery-worker python -c "from supabase import create_client; import os; client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_KEY')); print(client.rpc('cleanup_expired_chart_snapshots').execute())"

# Check disk space
df -h

# Review API usage trend
# (Check chart-img.com dashboard)
```

---

## Getting Help

### Information to Include

When asking for help, provide:

1. **Error Message**: Full error traceback
2. **Logs**: Relevant logs from `docker-compose logs`
3. **Environment**: OS, Docker version, environment variables (sanitized)
4. **Steps to Reproduce**: What you did before the error
5. **Expected vs Actual**: What should happen vs what happens
6. **Troubleshooting Tried**: What you already tried

### Example Issue Report

```markdown
## Issue: Chart Generation Fails with 404

**Error Message**:
```
HTTPError: 404 Not Found
Chart URL: https://api.chart-img.com/tradingview/advanced-chart?symbol=XETR:GDAXI&interval=15
```

**Logs**:
```
[2025-11-02 10:30:15] ERROR: Chart generation failed for ^GDAXI: 404
```

**Environment**:
- OS: Ubuntu 22.04
- Docker: 24.0.5
- chart-img.com Plan: MEGA

**Steps to Reproduce**:
1. Trigger ChartWatcher task
2. Error occurs for DAX symbol

**Expected**: Chart URL generated successfully
**Actual**: 404 error

**Troubleshooting Tried**:
- Verified API key (correct)
- Checked symbol mapping (XETR:DAX)
- Tested URL manually (still 404)

**Question**: Is "XETR:GDAXI" the wrong format? Should it be "XETR:DAX"?
```

---

## Next Steps

1. Review [Implementation Checklist](./IMPLEMENTATION_CHECKLIST.md)
2. Check [Session Context](./SESSION_CONTEXT.md) for quick start
3. Consult [Architecture](./01_ARCHITECTURE.md) for design details

---

**Last Updated**: 2025-11-02
**Support**: Check CLAUDE.md for project overview
