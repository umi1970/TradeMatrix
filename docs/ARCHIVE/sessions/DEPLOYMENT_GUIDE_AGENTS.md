# Agent Integration Deployment Guide

## Quick Start

This guide covers deploying the newly integrated AI agents with ChartGenerator to the Hetzner production server.

---

## Prerequisites

- [x] Hetzner server running (135.181.195.241)
- [x] Docker and Docker Compose installed
- [x] Redis container running
- [x] Environment variables configured
- [x] chart-img.com API key obtained

---

## Step 1: Update Environment Variables

SSH into Hetzner server and update `.env` file:

```bash
ssh root@135.181.195.241
cd /root/tradematrix-agents

# Add ChartGenerator API key
echo "CHART_IMG_API_KEY=your-api-key-here" >> .env

# Verify all required vars exist
grep -E "CHART_IMG_API_KEY|OPENAI_API_KEY|REDIS_URL|SUPABASE" .env
```

**Required Variables:**
```bash
# ChartGenerator
CHART_IMG_API_KEY=your-chart-img-api-key

# OpenAI (for ChartWatcher and JournalBot)
OPENAI_API_KEY=your-openai-api-key

# Redis
REDIS_URL=redis://redis:6379/0

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key
```

---

## Step 2: Deploy Updated Files

### Option A: Git Push (Recommended)

```bash
# On local machine
cd /mnt/c/Users/uzobu/Documents/SaaS/TradeMatrix

# Commit changes
git add hetzner-deploy/src/chart_watcher.py
git add hetzner-deploy/src/morning_planner.py
git add hetzner-deploy/src/journal_bot.py
git add hetzner-deploy/src/tasks.py
git commit -m "feat: Integrate ChartGenerator into all AI agents

- Add chart generation to ChartWatcher (every 6h)
- Add chart generation to MorningPlanner (daily 08:25)
- Add chart generation to JournalBot (daily 21:00)
- Update Celery tasks with new schedules
- Add comprehensive error handling"

git push origin main

# On Hetzner server
cd /root/tradematrix-agents
git pull origin main
```

### Option B: Manual File Transfer

```bash
# On local machine
scp hetzner-deploy/src/chart_watcher.py root@135.181.195.241:/root/tradematrix-agents/src/
scp hetzner-deploy/src/morning_planner.py root@135.181.195.241:/root/tradematrix-agents/src/
scp hetzner-deploy/src/journal_bot.py root@135.181.195.241:/root/tradematrix-agents/src/
scp hetzner-deploy/src/tasks.py root@135.181.195.241:/root/tradematrix-agents/src/
```

---

## Step 3: Verify Database Setup

Ensure required tables exist in Supabase:

### Check chart_snapshots table:
```sql
-- Run in Supabase SQL Editor
SELECT COUNT(*) FROM chart_snapshots;

-- If table doesn't exist, create it from migration
-- File: services/api/supabase/migrations/014_chart_snapshots.sql
```

### Check symbols table has chart columns:
```sql
SELECT id, symbol, chart_enabled, chart_img_symbol, chart_config
FROM symbols
WHERE chart_enabled = true;

-- Should return symbols configured for charts
-- Example: DAX, NASDAQ, DOW, EUR/USD, EUR/GBP
```

### Enable charts for symbols (if needed):
```sql
-- Update symbols to enable charts
UPDATE symbols
SET
    chart_enabled = true,
    chart_img_symbol = 'XETR:DAX',  -- TradingView symbol format
    chart_config = '{
        "default_timeframe": "4h",
        "indicators": ["MA", "RSI", "MACD"]
    }'::jsonb
WHERE symbol = 'DAX';

-- Repeat for other symbols:
-- NASDAQ: 'NASDAQ:NDX'
-- DOW: 'DJ:DJI'
-- EUR/USD: 'FX:EURUSD'
-- EUR/GBP: 'FX:EURGBP'
```

---

## Step 4: Restart Services

```bash
# On Hetzner server
cd /root/tradematrix-agents

# Stop current services
docker-compose down

# Rebuild (if Dockerfile changed)
docker-compose build

# Start services
docker-compose up -d

# Verify services are running
docker-compose ps

# Should show:
# - redis (running)
# - celery-worker (running)
# - celery-beat (running)
```

---

## Step 5: Monitor Logs

### Watch Celery Worker logs:
```bash
docker-compose logs -f celery-worker
```

**Look for:**
- ✅ "ChartWatcher initialized with ChartGenerator"
- ✅ "MorningPlanner initialized with ChartGenerator"
- ✅ "JournalBot initialized with ChartGenerator"

### Watch Celery Beat logs:
```bash
docker-compose logs -f celery-beat
```

**Look for scheduled tasks:**
```
Scheduler: Sending due task chart-analysis-6h (run_chart_analysis)
Scheduler: Sending due task morning-planner-daily (run_morning_planner)
Scheduler: Sending due task journal-bot-daily (run_journal_bot)
```

---

## Step 6: Test Agent Execution

### Manually trigger tasks (testing):

```bash
# Enter worker container
docker exec -it tradematrix-celery-worker bash

# Trigger ChartWatcher
celery -A src.tasks call run_chart_analysis

# Trigger MorningPlanner
celery -A src.tasks call run_morning_planner

# Trigger JournalBot
celery -A src.tasks call run_journal_bot

# Exit container
exit
```

### Check task results:
```bash
docker-compose logs celery-worker | grep "completed"

# Should show:
# ✅ ChartWatcher completed: X analyses created
# ✅ MorningPlanner completed: X setups generated
# ✅ JournalBot completed: X reports generated
```

---

## Step 7: Verify Chart Generation

### Check chart_snapshots in database:
```sql
SELECT
    id,
    symbol_id,
    timeframe,
    trigger_type,
    chart_url,
    generated_at
FROM chart_snapshots
ORDER BY generated_at DESC
LIMIT 10;

-- Should show recent chart snapshots
-- trigger_type: 'analysis', 'setup', or 'report'
```

### Check chart URLs are accessible:
```bash
# Copy a chart_url from database and test
curl -I "https://chart-img.com/..."

# Should return 200 OK
```

### Check API usage:
```bash
# Enter worker container
docker exec -it tradematrix-celery-worker python

>>> from src.chart_generator import ChartGenerator
>>> generator = ChartGenerator()
>>> stats = generator.get_usage_stats()
>>> print(stats)
{'requests_today': 42, 'limit_daily': 1000, 'percentage_used': 4.2, ...}
>>> exit()
```

---

## Step 8: Monitor Production

### Set up monitoring alerts:

1. **Rate Limit Warnings:**
   - Watch for "Rate limit warning" in logs
   - Should appear at 80% usage (800/1000)

2. **Chart Generation Failures:**
   - Watch for "Chart generation failed" errors
   - Check Supabase connectivity
   - Verify API key validity

3. **Celery Task Failures:**
   - Monitor task execution times
   - Check for stuck tasks
   - Verify Beat schedule is correct

### Useful monitoring commands:

```bash
# Check Redis connection
docker exec -it tradematrix-redis redis-cli ping
# Should return: PONG

# Check Celery worker health
docker exec -it tradematrix-celery-worker celery -A src.tasks inspect active

# Check scheduled tasks
docker exec -it tradematrix-celery-worker celery -A src.tasks inspect scheduled

# Check task history
docker exec -it tradematrix-celery-worker celery -A src.tasks inspect registered
```

---

## Troubleshooting

### Issue: "ChartGenerator not initialized"

**Cause:** Missing import or initialization in agent
**Fix:**
```python
from chart_generator import ChartGenerator

class AgentName:
    def __init__(self):
        self.chart_generator = ChartGenerator()
```

### Issue: "Rate limit exceeded"

**Cause:** Too many API calls (>1000/day)
**Fix:**
- Check cache is working (Redis running)
- Review task schedules (reduce frequency)
- Increase cache TTL (currently 5 min)

### Issue: "Symbol not found"

**Cause:** Symbol not configured with `chart_enabled=true`
**Fix:**
```sql
UPDATE symbols
SET chart_enabled = true,
    chart_img_symbol = 'XETR:DAX'
WHERE symbol = 'DAX';
```

### Issue: "Chart URL returns 404"

**Cause:** Chart-img.com API issue or expired URL
**Fix:**
- Verify API key is valid
- Check chart_img.com service status
- Regenerate chart with `force_refresh=True`

### Issue: "Celery tasks not running"

**Cause:** Beat scheduler not running or incorrect timezone
**Fix:**
```bash
# Check Beat is running
docker-compose ps | grep beat

# Check timezone in Celery config
grep "timezone" src/tasks.py
# Should be: timezone='UTC'

# Restart Beat
docker-compose restart celery-beat
```

---

## Rollback Plan

If issues occur, rollback to previous version:

```bash
# On Hetzner server
cd /root/tradematrix-agents

# Stop services
docker-compose down

# Revert to previous commit
git log --oneline | head -5  # Find previous commit hash
git checkout <previous-commit-hash>

# Restart services
docker-compose up -d

# Verify rollback
docker-compose logs -f celery-worker
```

---

## Performance Monitoring

### Daily Checks:

1. **API Usage:**
   - Should stay below 1000 requests/day
   - Warning at 800/day (80%)
   - Current estimation: ~42-43 charts/day

2. **Chart Generation Success Rate:**
   ```sql
   SELECT
       trigger_type,
       COUNT(*) as total,
       COUNT(*) FILTER (WHERE chart_url IS NOT NULL) as successful,
       ROUND(100.0 * COUNT(*) FILTER (WHERE chart_url IS NOT NULL) / COUNT(*), 2) as success_rate
   FROM chart_snapshots
   WHERE generated_at > NOW() - INTERVAL '24 hours'
   GROUP BY trigger_type;
   ```

3. **Agent Execution Times:**
   ```bash
   docker-compose logs celery-worker | grep "execution_duration_ms"
   ```

### Weekly Maintenance:

1. **Clean expired snapshots:**
   ```python
   from src.chart_generator import ChartGenerator
   generator = ChartGenerator()
   deleted = generator.cleanup_expired_snapshots()
   ```

2. **Review error logs:**
   ```bash
   docker-compose logs celery-worker | grep "ERROR" | tail -50
   ```

3. **Check disk space:**
   ```bash
   df -h
   docker system df
   ```

---

## Success Criteria

Deployment is successful when:

- [x] All 3 new Celery tasks are registered
- [x] ChartWatcher runs every 6 hours
- [x] MorningPlanner runs daily at 08:25
- [x] JournalBot runs daily at 21:00
- [x] Charts are being generated and stored
- [x] API usage stays below 1000/day
- [x] No critical errors in logs
- [x] Redis cache is working
- [x] Supabase connections are stable

---

## Next Steps After Deployment

1. **Monitor for 24 hours**
   - Check all scheduled tasks execute
   - Verify chart generation works
   - Monitor API usage

2. **Frontend Integration**
   - Display charts in dashboard
   - Show chart URLs from setups
   - Add chart viewer component

3. **Optional: TradeMonitor Agent**
   - Implement trade monitoring (30 min interval)
   - Add pattern change alerts
   - Generate 15m timeframe charts

4. **Documentation Updates**
   - Update PROJECT_OVERVIEW.md status
   - Update MASTER_ROADMAP.md
   - Create user guide for chart features

---

## Support

If you encounter issues:

1. Check logs: `docker-compose logs -f celery-worker`
2. Verify environment variables: `grep CHART_IMG .env`
3. Test database connectivity: Check Supabase dashboard
4. Review this guide's troubleshooting section
5. Check AGENT_INTEGRATION_SUMMARY.md for implementation details

---

**Deployment Date:** 2025-11-02
**Status:** Ready for Production ✅
**Estimated Deployment Time:** 15-30 minutes
