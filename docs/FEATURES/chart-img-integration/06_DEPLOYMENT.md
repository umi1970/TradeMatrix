# Deployment Guide

## Overview

Deployment der chart-img.com Integration auf Hetzner Production Server (CX11).

**Server Details**:
- IP: 135.181.195.241
- CPU: 2 vCPU
- RAM: 4 GB
- Storage: 40 GB SSD
- OS: Ubuntu 22.04

---

## Pre-Deployment Checklist

- [ ] Database migrations ready (`016_chart_config.sql`, `017_chart_snapshots.sql`)
- [ ] Environment variables configured (`.env`)
- [ ] ChartService implemented (`chart_service.py`)
- [ ] Agent integrations tested locally
- [ ] Frontend components built and tested
- [ ] Docker images built successfully
- [ ] Backup of production database created

---

## Environment Variables

### 1. Update `.env` File

**File**: `hetzner-deploy/.env`

```bash
# Existing variables (keep as is)
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_KEY=your_service_key
REDIS_HOST=redis
REDIS_PORT=6379
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# ✅ NEW: chart-img.com API
CHART_IMG_API_KEY=3pJTrvapkk9LQ7FwaUOmf6I354fSOeWa8VJifI2l

# Optional: Chart API configuration
CHART_API_DAILY_LIMIT=1000
CHART_API_PER_SECOND_LIMIT=15
CHART_CACHE_TTL=3600  # 1 hour in seconds
```

### 2. Verify Environment Variables

```bash
# SSH into Hetzner server
ssh root@135.181.195.241

# Navigate to deployment directory
cd /root/tradematrix-agents

# Check if CHART_IMG_API_KEY is set
grep CHART_IMG_API_KEY .env

# If not set, add it
echo "CHART_IMG_API_KEY=3pJTrvapkk9LQ7FwaUOmf6I354fSOeWa8VJifI2l" >> .env
```

---

## Database Migration

### 1. Run Migrations in Supabase

**Option A: Via Supabase Dashboard**

```bash
# Open Supabase SQL Editor
# https://supabase.com/dashboard/project/YOUR_PROJECT_ID/sql

# Execute migrations in order:
```

**Migration 016**: `services/api/supabase/migrations/016_chart_config.sql`

```sql
-- Copy content from 02_DATABASE_SCHEMA.md (Migration 001)
BEGIN;

ALTER TABLE market_symbols
ADD COLUMN IF NOT EXISTS chart_config JSONB DEFAULT '{}'::JSONB;

COMMENT ON COLUMN market_symbols.chart_config
IS 'User-defined chart configuration for chart-img.com API';

CREATE INDEX IF NOT EXISTS idx_market_symbols_chart_config
ON market_symbols USING GIN (chart_config);

UPDATE market_symbols
SET chart_config = jsonb_build_object(
    'tv_symbol', CASE symbol
        WHEN '^GDAXI' THEN 'XETR:DAX'
        WHEN '^NDX' THEN 'NASDAQ:NDX'
        WHEN '^DJI' THEN 'DJCFD:DJI'
        WHEN 'EURUSD=X' THEN 'OANDA:EURUSD'
        WHEN 'EURGBP=X' THEN 'OANDA:EURGBP'
        ELSE symbol
    END,
    'timeframes', ARRAY['15', '60', 'D']::TEXT[],
    'indicators', ARRAY['RSI@tv-basicstudies']::TEXT[],
    'chart_type', 'candles',
    'theme', 'dark',
    'width', 1200,
    'height', 800,
    'show_volume', true
)
WHERE chart_config = '{}'::JSONB;

COMMIT;
```

**Migration 017**: `services/api/supabase/migrations/017_chart_snapshots.sql`

```sql
-- Copy full content from 02_DATABASE_SCHEMA.md (Migration 002)
BEGIN;

CREATE TABLE IF NOT EXISTS chart_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    symbol_id UUID NOT NULL REFERENCES market_symbols(id) ON DELETE CASCADE,
    chart_url TEXT NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    created_by_agent VARCHAR(50) NOT NULL,
    metadata JSONB DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '60 days')
);

-- Comments
COMMENT ON TABLE chart_snapshots IS 'Stores generated chart URLs from chart-img.com API';
COMMENT ON COLUMN chart_snapshots.symbol_id IS 'Reference to market_symbols table';
COMMENT ON COLUMN chart_snapshots.chart_url IS 'Full URL to chart image';
COMMENT ON COLUMN chart_snapshots.timeframe IS 'Timeframe used for this chart (e.g., M15, H1, D1)';
COMMENT ON COLUMN chart_snapshots.created_by_agent IS 'Agent that requested this chart (e.g., ChartWatcher, MorningPlanner)';
COMMENT ON COLUMN chart_snapshots.metadata IS 'Additional metadata (indicators, dimensions, etc.)';
COMMENT ON COLUMN chart_snapshots.expires_at IS 'Chart URL expires after 60 days (chart-img.com retention)';

-- Indexes
CREATE INDEX idx_chart_snapshots_symbol_id ON chart_snapshots(symbol_id);
CREATE INDEX idx_chart_snapshots_agent ON chart_snapshots(created_by_agent);
CREATE INDEX idx_chart_snapshots_symbol_created ON chart_snapshots(symbol_id, created_at DESC);
CREATE INDEX idx_chart_snapshots_agent_created ON chart_snapshots(created_by_agent, created_at DESC);
CREATE INDEX idx_chart_snapshots_expires_at ON chart_snapshots(expires_at);
CREATE INDEX idx_chart_snapshots_metadata ON chart_snapshots USING GIN (metadata);

-- Enable RLS
ALTER TABLE chart_snapshots ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY "Users can read own chart snapshots"
ON chart_snapshots FOR SELECT
USING (
    symbol_id IN (
        SELECT id FROM market_symbols WHERE user_id = auth.uid()
    )
);

CREATE POLICY "Users can insert own chart snapshots"
ON chart_snapshots FOR INSERT
WITH CHECK (
    symbol_id IN (
        SELECT id FROM market_symbols WHERE user_id = auth.uid()
    )
);

CREATE POLICY "Users can delete own chart snapshots"
ON chart_snapshots FOR DELETE
USING (
    symbol_id IN (
        SELECT id FROM market_symbols WHERE user_id = auth.uid()
    )
);

CREATE POLICY "Service role has full access"
ON chart_snapshots FOR ALL
USING (auth.jwt()->>'role' = 'service_role');

COMMIT;
```

**Migration 018**: `services/api/supabase/migrations/018_chart_snapshots_cleanup.sql`

```sql
-- Copy from 02_DATABASE_SCHEMA.md (Migration 003)
BEGIN;

CREATE OR REPLACE FUNCTION cleanup_expired_chart_snapshots()
RETURNS INTEGER
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM chart_snapshots
    WHERE expires_at < NOW();

    GET DIAGNOSTICS deleted_count = ROW_COUNT;

    RAISE NOTICE 'Deleted % expired chart snapshots', deleted_count;

    RETURN deleted_count;
END;
$$;

COMMIT;
```

### 2. Verify Migrations

```sql
-- Check if chart_config column exists
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'market_symbols' AND column_name = 'chart_config';

-- Check if chart_snapshots table exists
SELECT table_name
FROM information_schema.tables
WHERE table_name = 'chart_snapshots';

-- Check RLS policies
SELECT schemaname, tablename, policyname
FROM pg_policies
WHERE tablename IN ('market_symbols', 'chart_snapshots');
```

---

## Code Deployment

### 1. Deploy ChartService

**File**: `hetzner-deploy/src/chart_service.py`

```bash
# SSH into server
ssh root@135.181.195.241

# Navigate to deployment directory
cd /root/tradematrix-agents

# Create chart_service.py
nano src/chart_service.py

# Paste full ChartService implementation from 05_AGENT_INTEGRATION.md
# Save and exit (Ctrl+O, Enter, Ctrl+X)
```

### 2. Update Agent Files

**Update ChartWatcher** (`hetzner-deploy/src/chart_watcher.py`):

```python
# Add import at top
from src.chart_service import ChartService

# Fix lines 554-560 (see 05_AGENT_INTEGRATION.md)
```

**Update MorningPlanner** (`hetzner-deploy/src/morning_planner.py`):

```python
# Add ChartService integration (see 05_AGENT_INTEGRATION.md)
```

**Update JournalBot** (`hetzner-deploy/src/journal_bot.py`):

```python
# Add ChartService integration (see 05_AGENT_INTEGRATION.md)
```

### 3. Update requirements.txt

**File**: `hetzner-deploy/requirements.txt`

```bash
# Check if httpx is already installed
grep httpx requirements.txt

# If not, add it
echo "httpx==0.25.0" >> requirements.txt
```

### 4. Update Docker Compose

**File**: `hetzner-deploy/docker-compose.yml`

Verify environment variables are passed to containers:

```yaml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

  celery-worker:
    build: .
    command: celery -A src.tasks worker --loglevel=info
    volumes:
      - ./src:/app/src
    environment:
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_SERVICE_KEY=${SUPABASE_SERVICE_KEY}
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
      - CHART_IMG_API_KEY=${CHART_IMG_API_KEY}  # ✅ NEW
    depends_on:
      - redis
    restart: unless-stopped

  celery-beat:
    build: .
    command: celery -A src.tasks beat --loglevel=info
    volumes:
      - ./src:/app/src
    environment:
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_SERVICE_KEY=${SUPABASE_SERVICE_KEY}
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
      - CHART_IMG_API_KEY=${CHART_IMG_API_KEY}  # ✅ NEW
    depends_on:
      - redis
    restart: unless-stopped

volumes:
  redis_data:
```

---

## Build & Deploy

### 1. Rebuild Docker Images

```bash
# SSH into server
ssh root@135.181.195.241

# Navigate to deployment directory
cd /root/tradematrix-agents

# Stop running containers
docker-compose down

# Rebuild images (include new chart_service.py)
docker-compose build --no-cache

# Start containers
docker-compose up -d

# Verify containers are running
docker-compose ps
```

Expected output:
```
NAME                     COMMAND                  SERVICE         STATUS
tradematrix-redis-1      "docker-entrypoint.s…"   redis           Up 10 seconds
tradematrix-worker-1     "celery -A src.tasks…"   celery-worker   Up 8 seconds
tradematrix-beat-1       "celery -A src.tasks…"   celery-beat     Up 8 seconds
```

### 2. Verify Deployment

```bash
# Check logs for errors
docker-compose logs -f celery-worker

# Look for successful startup messages:
# [INFO] Connected to redis://redis:6379/0
# [INFO] mingle: all alone
# [INFO] celery@worker ready

# Test chart service (Python shell inside container)
docker-compose exec celery-worker python
```

```python
>>> from src.chart_service import ChartService
>>> import asyncio
>>>
>>> service = ChartService()
>>> result = asyncio.run(service.generate_chart_url(
...     symbol="^GDAXI",
...     timeframe="M15",
...     agent_name="TestAgent"
... ))
>>>
>>> print(result["chart_url"])
# Should print: https://api.chart-img.com/tradingview/advanced-chart?symbol=XETR:DAX&interval=15&...
>>>
>>> exit()
```

---

## Frontend Deployment (Netlify)

### 1. Update Frontend Code

**Local Machine**:

```bash
# Navigate to frontend
cd /mnt/c/Users/uzobu/Documents/SaaS/TradeMatrix/apps/web

# Copy chart components from 04_FRONTEND_COMPONENTS.md
# - src/components/charts/ChartConfigModal.tsx
# - src/components/charts/TimeframeSelector.tsx
# - src/components/charts/IndicatorSelector.tsx
# - src/components/charts/ChartPreview.tsx
# - src/components/charts/ChartSnapshotGallery.tsx
# - src/components/charts/ChartSnapshotCard.tsx
# - src/components/charts/ChartConfigButton.tsx

# Build frontend
npm run build

# Test locally
npm run dev
# Open http://localhost:3000
```

### 2. Deploy to Netlify

```bash
# Commit changes
git add .
git commit -m "feat: Add chart-img.com integration frontend"

# Push to GitHub
git push origin main

# Netlify auto-deploys from GitHub
# Wait for build to complete (~2 min)

# Verify deployment
# https://tradematrix.netlify.app
```

### 3. Verify Frontend

- [ ] Navigate to Dashboard → Market Symbols
- [ ] Click "Chart Config" button
- [ ] Configure symbol (select timeframes, indicators)
- [ ] Save configuration
- [ ] Check Supabase database (market_symbols.chart_config updated)

---

## Post-Deployment Testing

### 1. Test ChartWatcher

```bash
# SSH into server
ssh root@135.181.195.241

# Trigger ChartWatcher task manually
docker-compose exec celery-worker celery -A src.tasks call chart_watcher.analyze_all_symbols

# Check logs
docker-compose logs -f celery-worker | grep ChartWatcher
```

Expected output:
```
ChartWatcher analyzed ^GDAXI M15: Chart analysis placeholder
ChartWatcher analyzed ^GDAXI H1: Chart analysis placeholder
```

### 2. Test MorningPlanner

```bash
# Trigger MorningPlanner task manually
docker-compose exec celery-worker celery -A src.tasks call morning_planner.generate_report

# Check logs
docker-compose logs -f celery-worker | grep MorningPlanner
```

### 3. Verify Database

```sql
-- Connect to Supabase SQL Editor

-- Check if chart_snapshots are being created
SELECT
    cs.id,
    ms.symbol,
    cs.timeframe,
    cs.created_by_agent,
    cs.created_at
FROM chart_snapshots cs
JOIN market_symbols ms ON cs.symbol_id = ms.id
ORDER BY cs.created_at DESC
LIMIT 10;
```

### 4. Check Rate Limits

```bash
# Connect to Redis
docker-compose exec redis redis-cli

# Check daily counter
GET chart_api:daily:2025-11-02

# Should return number between 0 and 1000
# Example: "15" (15 requests made today)

# Exit Redis
exit
```

---

## Monitoring & Alerts

### 1. Daily Usage Tracking

**File**: `hetzner-deploy/src/monitor_chart_usage.py`

```python
import redis
from datetime import datetime

redis_client = redis.Redis(host="localhost", port=6379, decode_responses=True)

def check_daily_usage():
    today = datetime.now().date().isoformat()
    daily_key = f"chart_api:daily:{today}"
    count = redis_client.get(daily_key)
    used = int(count) if count else 0
    remaining = 1000 - used

    print(f"Chart API Usage: {used}/1000 ({remaining} remaining)")

    if used > 900:
        print("⚠️ WARNING: Approaching daily limit!")

    return used, remaining

if __name__ == "__main__":
    check_daily_usage()
```

Run daily:
```bash
docker-compose exec celery-worker python src/monitor_chart_usage.py
```

### 2. Celery Beat Schedule (Add Monitoring Task)

**File**: `hetzner-deploy/src/tasks.py`

```python
from celery.schedules import crontab

app.conf.beat_schedule = {
    # Existing tasks...

    "monitor-chart-usage-daily": {
        "task": "monitor.check_chart_usage",
        "schedule": crontab(hour=23, minute=0),  # 23:00 UTC daily
    },
}

@shared_task(name="monitor.check_chart_usage")
def check_chart_usage():
    """Check daily chart API usage and alert if high."""
    from src.monitor_chart_usage import check_daily_usage

    used, remaining = check_daily_usage()

    if used > 900:
        # TODO: Send alert via email/Slack
        print(f"ALERT: Chart API usage high ({used}/1000)")

    return {"used": used, "remaining": remaining}
```

---

## Rollback Plan

If deployment fails:

```bash
# 1. Stop new containers
docker-compose down

# 2. Checkout previous commit
git checkout HEAD~1

# 3. Rebuild with old code
docker-compose build --no-cache
docker-compose up -d

# 4. Verify services
docker-compose ps

# 5. Roll back database migrations (if needed)
# Run in Supabase SQL Editor:
# DROP TABLE IF EXISTS chart_snapshots;
# ALTER TABLE market_symbols DROP COLUMN IF EXISTS chart_config;
```

---

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose logs celery-worker

# Common issues:
# - Missing environment variable → Check .env
# - Import error → Rebuild image with --no-cache
# - Redis connection failed → Check Redis container status
```

### Chart Generation Fails

```bash
# Test API key manually
curl "https://api.chart-img.com/tradingview/advanced-chart?symbol=XETR:DAX&interval=15&theme=dark&width=800&height=600"

# Check response (should return PNG image or URL)
```

### Rate Limit Issues

```bash
# Check Redis counters
docker-compose exec redis redis-cli
GET chart_api:daily:2025-11-02

# Reset counter (EMERGENCY ONLY!)
DEL chart_api:daily:2025-11-02
```

---

## Security Checklist

- [ ] API key stored in `.env` (not committed to Git)
- [ ] `.env` file permissions set to 600 (`chmod 600 .env`)
- [ ] Supabase RLS policies enabled on `chart_snapshots`
- [ ] Service role key used only in backend (not exposed to frontend)
- [ ] HTTPS enabled for all API calls
- [ ] Docker containers running with limited privileges

---

## Next Steps

1. Monitor production for 24 hours
2. Review [Testing Checklist](./07_TESTING.md)
3. Read [Troubleshooting Guide](./08_TROUBLESHOOTING.md)
4. Set up automated monitoring/alerts

---

**Last Updated**: 2025-11-02
**Deployment Status**: Ready for production
**Server**: Hetzner CX11 (135.181.195.241)
