# TradeMatrix Hetzner Deployment Guide

**Server:** 135.181.195.241 (Hetzner CX11)
**Services:** Redis, Celery Worker, Celery Beat
**Repository:** `/root/tradematrix-agents`

---

## 📋 Pre-Deployment Checklist

Before deploying, ensure all of the following are completed:

- [ ] **Supabase Migration 013 executed** (chart_snapshots table exists)
- [ ] **Environment Variables prepared** (see `.env.example`)
- [ ] **API Keys validated**
  - chart-img.com API key (3pJTrvapkk9LQ7FwaUOmf6I354fSOeWa8VJifI2l)
  - OpenAI API key (for ChartWatcher Vision API)
  - Finnhub API key
  - Alpha Vantage API key
  - VAPID keys (for push notifications)
- [ ] **All code changes committed and pushed** to main branch
- [ ] **Backup created** (Redis dump.rdb, Supabase snapshot)
- [ ] **Monitoring enabled** (health check script ready)
- [ ] **Team notified** (if applicable)

---

## 🚀 Deployment Steps (Automated)

### Option 1: Using deploy.sh (Recommended)

```bash
# SSH to Hetzner
ssh root@135.181.195.241

# Navigate to project
cd /root/tradematrix-agents

# Run deployment script
chmod +x deploy.sh
./deploy.sh
```

The script will:
1. Check for `.env` file
2. Pull latest code from `main` branch
3. Stop all services
4. Rebuild Docker images
5. Start services in detached mode
6. Wait for services to initialize
7. Verify all services are running
8. Display recent logs

---

## 🔧 Deployment Steps (Manual)

### Step 1: SSH to Server

```bash
ssh root@135.181.195.241
```

### Step 2: Navigate to Project

```bash
cd /root/tradematrix-agents
```

### Step 3: Backup Current State

```bash
# Backup Redis data
docker exec tradematrix-agents-redis-1 redis-cli SAVE
cp -r ./data/redis ./backups/redis-$(date +%Y%m%d-%H%M%S)

# Backup .env
cp .env .env.backup-$(date +%Y%m%d-%H%M%S)
```

### Step 4: Pull Latest Code

```bash
git pull origin main
```

**Expected output:**
```
Updating c131818..abc1234
Fast-forward
 hetzner-deploy/src/chart_generator.py | 150 +++++++++++++++++++
 hetzner-deploy/src/chart_watcher.py   | 200 +++++++++++++++++++++++
 ...
```

### Step 5: Update Environment Variables

```bash
nano .env
```

Add/update these variables:

```bash
# ChartGenerator (NEW)
CHART_IMG_API_KEY=3pJTrvapkk9LQ7FwaUOmf6I354fSOeWa8VJifI2l
CHART_IMG_BASE_URL=https://api.chart-img.com

# ChartWatcher Vision API (NEW)
OPENAI_API_KEY=sk-...
```

**Verify all required variables:**

```bash
grep -E "SUPABASE_URL|SUPABASE_SERVICE_KEY|REDIS_URL|CHART_IMG_API_KEY|OPENAI_API_KEY" .env
```

### Step 6: Update Dependencies

```bash
# Check if requirements.txt changed
git diff HEAD~1 requirements.txt

# If changed, rebuild is required (Step 8 will handle this)
```

### Step 7: Stop Services

```bash
docker-compose down
```

**Expected output:**
```
Stopping tradematrix-agents-celery_beat_1   ... done
Stopping tradematrix-agents-celery_worker_1 ... done
Stopping tradematrix-agents-redis-1         ... done
Removing tradematrix-agents-celery_beat_1   ... done
Removing tradematrix-agents-celery_worker_1 ... done
Removing tradematrix-agents-redis-1         ... done
```

### Step 8: Rebuild Services

```bash
docker-compose build --no-cache
```

**This step takes 2-3 minutes.** Expected output:
```
Building celery_worker
Step 1/10 : FROM python:3.11-slim
...
Successfully built abc123def456
Successfully tagged tradematrix-agents-celery_worker:latest
```

### Step 9: Start Services

```bash
docker-compose up -d
```

**Expected output:**
```
Creating tradematrix-agents-redis-1         ... done
Creating tradematrix-agents-celery_worker_1 ... done
Creating tradematrix-agents-celery_beat_1   ... done
```

### Step 10: Wait for Initialization

```bash
sleep 15
```

Services need time to:
- Connect to Redis
- Initialize Supabase client
- Load ChartGenerator
- Register Celery tasks

### Step 11: Verify Services

```bash
docker-compose ps
```

**Expected output:**
```
NAME                                  COMMAND                  SERVICE          STATUS
tradematrix-agents-celery_beat_1      "celery -A tasks bea…"   celery_beat      Up 15 seconds
tradematrix-agents-celery_worker_1    "celery -A tasks wor…"   celery_worker    Up 15 seconds
tradematrix-agents-redis-1            "docker-entrypoint.s…"   redis            Up 15 seconds
```

All services must show **STATUS: Up**.

### Step 12: Check Logs

```bash
# Check worker logs
docker-compose logs celery_worker --tail=50

# Check beat logs
docker-compose logs celery_beat --tail=50

# Check Redis logs
docker-compose logs redis --tail=20
```

**Look for:**
- ✅ `[INFO/MainProcess] Connected to redis://redis:6379/0`
- ✅ `✅ ChartGenerator initialized successfully`
- ✅ `[INFO/Beat] Scheduler: Sending due task chart_watcher_task`
- ❌ No `ERROR` or `CRITICAL` logs

---

## ✅ Post-Deployment Verification

### 1. Service Health Check

```bash
# Run health check script
chmod +x health_check.sh
./health_check.sh
```

**Expected output:**
```
🔍 TradeMatrix Health Check
==========================
📦 Docker Services:
  celery_worker    Up
  celery_beat      Up
  redis            Up

🔴 Redis:
  PONG

🐝 Celery Worker:
  [INFO] Task chart_watcher_task started
  [INFO] ChartGenerator initialized

✅ Health check complete!
```

### 2. Verify ChartGenerator

```bash
# Test chart generation (manual)
docker exec -it tradematrix-agents-celery_worker-1 python3 << EOF
from src.chart_generator import ChartGenerator
gen = ChartGenerator()
print("✅ ChartGenerator OK")
EOF
```

### 3. Check API Usage Tracking

```bash
# Check today's API usage
docker exec tradematrix-agents-redis-1 redis-cli GET "chart_img:requests:daily:$(date +%Y-%m-%d)"
```

**Expected:** `(nil)` or `0-10` (if charts already generated)

### 4. Verify Database Connection

```bash
docker exec -it tradematrix-agents-celery_worker-1 python3 << EOF
from src.config.supabase_client import get_supabase_client
supabase = get_supabase_client()
result = supabase.table('chart_snapshots').select('*').limit(1).execute()
print(f"✅ Database OK, {len(result.data)} rows")
EOF
```

### 5. Monitor for 30 Minutes

```bash
# Watch logs in real-time
docker-compose logs -f celery_worker celery_beat

# OR use watch command
watch -n 60 'docker-compose logs celery_worker --tail=10'
```

**Look for:**
- ChartWatcher tasks executing (every 4 hours)
- MorningPlanner tasks executing (7:00 AM CET)
- JournalBot tasks executing (5:00 PM CET)
- No errors or exceptions

### 6. Test Push Notifications

```bash
# Trigger a test alert manually
docker exec -it tradematrix-agents-celery_worker-1 python3 << EOF
from src.liquidity_alert_engine import LiquidityAlertEngine
engine = LiquidityAlertEngine()
# This will check current prices and trigger alerts if conditions met
engine.check_all_alerts()
print("✅ Alert check complete")
EOF
```

### 7. Verify Chart Snapshots in Supabase

Log into Supabase Dashboard:
1. Go to Table Editor → `chart_snapshots`
2. Verify recent entries (within last 4 hours)
3. Check `chart_url` is accessible
4. Verify `generated_at` timestamps

---

## 🐛 Troubleshooting

### Issue: Services won't start

```bash
# Check Docker logs
docker-compose logs

# Check disk space
df -h

# Check memory
free -h
```

**Solution:** If disk full, clean old Docker images:
```bash
docker system prune -a
```

### Issue: ChartGenerator initialization fails

```bash
# Check logs
docker-compose logs celery_worker | grep ChartGenerator

# Verify API key
docker exec tradematrix-agents-celery_worker-1 env | grep CHART_IMG
```

**Solution:** Verify `.env` has correct `CHART_IMG_API_KEY`

### Issue: Database connection fails

```bash
# Test Supabase connection
docker exec -it tradematrix-agents-celery_worker-1 python3 -c "from src.config.supabase_client import get_supabase_client; print(get_supabase_client())"
```

**Solution:** Verify `.env` has correct `SUPABASE_URL` and `SUPABASE_SERVICE_KEY`

### Issue: Redis connection fails

```bash
# Check Redis is running
docker-compose ps redis

# Test Redis connection
docker exec tradematrix-agents-redis-1 redis-cli ping
```

**Solution:** Restart Redis:
```bash
docker-compose restart redis
```

### Issue: API limit exceeded

```bash
# Check daily usage
docker exec tradematrix-agents-redis-1 redis-cli GET "chart_img:requests:daily:$(date +%Y-%m-%d)"
```

**Solution:** If >800, charts will use fallback (external TradingView). Wait until next day or upgrade chart-img.com plan.

### Issue: Tasks not executing

```bash
# Check Celery Beat schedule
docker-compose logs celery_beat | grep "Scheduler: Sending"
```

**Solution:** Restart Celery Beat:
```bash
docker-compose restart celery_beat
```

---

## 🔄 Rollback Procedure

If deployment fails or causes issues:

### Option 1: Automated Rollback

```bash
chmod +x rollback.sh
./rollback.sh
```

### Option 2: Manual Rollback

```bash
# Stop services
docker-compose down

# Revert to previous commit
git log --oneline -5
git reset --hard <previous-commit-hash>

# Restore .env backup
cp .env.backup-<timestamp> .env

# Restart with old version
docker-compose build
docker-compose up -d

# Verify
docker-compose ps
docker-compose logs celery_worker --tail=50
```

### Option 3: Restore from Backup

```bash
# Stop services
docker-compose down

# Restore Redis data
cp -r ./backups/redis-<timestamp>/* ./data/redis/

# Restart
docker-compose up -d
```

---

## 📊 Monitoring

### Daily Monitoring Tasks

1. **Check service status** (once per day)
   ```bash
   ./health_check.sh
   ```

2. **Check API usage** (once per day)
   ```bash
   docker exec tradematrix-agents-redis-1 redis-cli GET "chart_img:requests:daily:$(date +%Y-%m-%d)"
   ```

3. **Review logs** (once per day)
   ```bash
   docker-compose logs celery_worker --since 24h | grep ERROR
   docker-compose logs celery_beat --since 24h | grep ERROR
   ```

4. **Verify chart snapshots** (once per day)
   - Log into Supabase
   - Check `chart_snapshots` table
   - Verify recent entries

### Weekly Monitoring Tasks

1. **Check disk space**
   ```bash
   df -h
   ```

2. **Clean old Docker images**
   ```bash
   docker system df
   docker system prune
   ```

3. **Review Redis memory usage**
   ```bash
   docker exec tradematrix-agents-redis-1 redis-cli INFO memory
   ```

### Monthly Monitoring Tasks

1. **Review API costs**
   - chart-img.com usage (1,000 requests/month limit)
   - OpenAI API usage (Vision API for ChartWatcher)

2. **Update dependencies**
   ```bash
   pip list --outdated
   ```

3. **Security updates**
   ```bash
   apt update && apt upgrade
   ```

---

## 🔐 Security Checklist

- [ ] `.env` file has correct permissions (`chmod 600 .env`)
- [ ] No sensitive data committed to Git
- [ ] Supabase RLS policies enabled
- [ ] API keys rotated every 90 days
- [ ] SSH key-based authentication only (no password)
- [ ] Firewall configured (UFW)
- [ ] Docker images from trusted sources only
- [ ] Regular backups automated

---

## 📞 Support

If you encounter issues not covered in this guide:

1. **Check logs first**
   ```bash
   docker-compose logs --tail=100
   ```

2. **Search known issues** in Git repository

3. **Create new issue** with:
   - Deployment date/time
   - Git commit hash
   - Error logs
   - Steps to reproduce

---

## 🎯 Next Steps After Deployment

1. **Monitor for 24 hours** - Watch for any errors or unexpected behavior
2. **Verify all scheduled tasks** - Check ChartWatcher, MorningPlanner, JournalBot
3. **Test push notifications** - Ensure alerts are being sent
4. **Review chart quality** - Check TradingView charts are rendering correctly
5. **Update documentation** - Document any deployment-specific issues or solutions

---

**Deployment Guide Version:** 1.0
**Last Updated:** 2025-11-02
**Maintainer:** umi1970
