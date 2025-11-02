# TradeMatrix Hetzner Deployment

Complete deployment system for TradeMatrix on Hetzner CX11 server.

**Server:** 135.181.195.241
**Services:** Redis, Celery Worker, Celery Beat
**Location:** `/root/tradematrix-agents`

---

## 📁 Repository Structure

```
hetzner-deploy/
├── README.md                      # This file
├── DEPLOYMENT_GUIDE.md            # Complete deployment guide
├── MIGRATION_GUIDE.md             # Supabase migration instructions
├── TESTING_CHECKLIST.md           # Post-deployment testing
│
├── .env.example                   # Environment variables template
├── docker-compose.yml             # Docker services configuration
├── Dockerfile                     # Container build instructions
├── requirements.txt               # Python dependencies
│
├── deploy.sh                      # Automated deployment script
├── health_check.sh                # Health monitoring script
├── rollback.sh                    # Rollback script
├── monitor_dashboard.py           # Live monitoring dashboard
│
└── src/                           # Application source code
    ├── tasks.py                   # Celery tasks
    ├── chart_generator.py         # Chart generation service
    ├── chart_watcher.py           # AI chart analysis agent
    ├── morning_planner.py         # Daily market preparation agent
    ├── journal_bot.py             # Trading journal agent
    ├── liquidity_alert_engine.py  # Price alert system
    ├── price_fetcher.py           # Market data fetcher
    ├── push_notification_service.py  # Web push notifications
    └── config/
        └── supabase_client.py     # Supabase connection
```

---

## 🚀 Quick Start

### First-Time Setup

```bash
# 1. SSH to Hetzner server
ssh root@135.181.195.241

# 2. Navigate to project
cd /root/tradematrix-agents

# 3. Copy environment variables
cp .env.example .env
nano .env  # Fill in your actual values

# 4. Deploy
./deploy.sh
```

### Regular Deployment

```bash
# Pull latest code and restart services
./deploy.sh
```

---

## 📚 Documentation

### 1. [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)

**Complete deployment instructions including:**
- Pre-deployment checklist
- Step-by-step deployment (automated & manual)
- Post-deployment verification
- Troubleshooting common issues
- Rollback procedures
- Monitoring guidelines

**When to use:**
- First-time deployment
- Understanding the deployment process
- Troubleshooting deployment issues
- Manual deployment (if automated script fails)

### 2. [MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md)

**Supabase database migration instructions:**
- How to apply migrations (3 methods)
- Migration verification steps
- Rollback procedures
- Migration history tracking

**When to use:**
- Before first deployment (apply migration 013)
- When database schema changes
- Troubleshooting database access issues

### 3. [TESTING_CHECKLIST.md](./TESTING_CHECKLIST.md)

**Comprehensive post-deployment testing:**
- 12 phases, 45+ individual tests
- Infrastructure, services, database tests
- Chart generation verification
- 24-hour stability testing
- Test results tracking

**When to use:**
- After every deployment
- Before marking deployment as successful
- Diagnosing production issues
- Quality assurance

---

## 🛠️ Deployment Scripts

### deploy.sh - Automated Deployment

**What it does:**
1. Checks environment configuration
2. Creates backup (code + data)
3. Pulls latest code from Git
4. Stops services
5. Rebuilds Docker images
6. Starts services
7. Verifies all services are healthy

**Usage:**
```bash
./deploy.sh
```

**Output:**
- Colored status messages (✅ success, ⚠️ warning, ❌ error)
- Backup location
- Recent logs
- Service status

### health_check.sh - Health Monitoring

**What it checks:**
1. Docker service status
2. Redis health & memory usage
3. Celery Worker status & error logs
4. Celery Beat scheduling
5. chart-img.com API usage
6. Disk space & memory usage
7. Recent activity logs

**Usage:**
```bash
./health_check.sh
```

**When to run:**
- After deployment
- Daily monitoring
- When investigating issues
- Before making changes

### rollback.sh - Emergency Rollback

**What it does:**
1. Shows recent commits
2. Creates emergency backup
3. Stops services
4. Reverts code to specified commit
5. Rebuilds and restarts services
6. Verifies services are running

**Usage:**
```bash
# Interactive (prompts for commit)
./rollback.sh

# Direct rollback to specific commit
./rollback.sh abc1234
```

**When to use:**
- Deployment caused issues
- New code has bugs
- Need to revert quickly

### monitor_dashboard.py - Live Dashboard

**What it shows:**
1. Redis status & memory
2. chart-img.com API usage (today + 7-day history)
3. Recent chart snapshots (last 10)
4. Recent liquidity alerts (last 5)
5. Active alert subscriptions count
6. System information

**Usage:**
```bash
python3 monitor_dashboard.py
```

**When to use:**
- Daily monitoring
- Checking API usage before deployment
- Verifying data flow
- Debugging chart generation

---

## ⚙️ Configuration

### Environment Variables (.env)

**Required variables:**

```bash
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Redis
REDIS_URL=redis://redis:6379/0

# chart-img.com (TradingView charts)
CHART_IMG_API_KEY=3pJTrvapkk9LQ7FwaUOmf6I354fSOeWa8VJifI2l
CHART_IMG_BASE_URL=https://api.chart-img.com

# OpenAI (ChartWatcher Vision API)
OPENAI_API_KEY=sk-proj-...

# Market Data
FINNHUB_API_KEY=your-finnhub-key
ALPHA_VANTAGE_API_KEY=your-alpha-vantage-key

# Push Notifications
VAPID_PUBLIC_KEY=your-vapid-public-key
VAPID_PRIVATE_KEY=your-vapid-private-key
```

**See [.env.example](./.env.example) for complete list.**

---

## 🐳 Docker Services

### Service Overview

```yaml
services:
  redis:          # Key-value store for Celery & caching
  celery_worker:  # Background task executor
  celery_beat:    # Task scheduler
```

### Managing Services

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# Restart specific service
docker-compose restart celery_worker

# View logs
docker-compose logs -f celery_worker

# Check status
docker-compose ps

# Rebuild without cache
docker-compose build --no-cache
```

---

## 📊 Monitoring

### Daily Checks

```bash
# Quick health check
./health_check.sh

# Detailed monitoring
python3 monitor_dashboard.py

# Check API usage
docker exec tradematrix_redis redis-cli GET "chart_img:requests:daily:$(date +%Y-%m-%d)"
```

### Log Monitoring

```bash
# Worker logs (real-time)
docker-compose logs -f celery_worker

# Beat logs (real-time)
docker-compose logs -f celery_beat

# Last 100 lines
docker-compose logs celery_worker --tail=100

# Search for errors
docker-compose logs celery_worker | grep ERROR
```

### System Resources

```bash
# Disk space
df -h

# Memory usage
free -h

# Docker stats
docker stats --no-stream

# Process list
top -bn1 | head -20
```

---

## 🔄 Common Operations

### Update Code (No Deployment)

```bash
git pull origin main
```

### Restart Services (No Rebuild)

```bash
docker-compose restart
```

### Clear Redis Cache

```bash
docker exec tradematrix_redis redis-cli FLUSHDB
```

### View Celery Tasks

```bash
docker exec tradematrix_celery_worker celery -A src.tasks inspect active
```

### Test Chart Generation

```bash
docker exec -it tradematrix_celery_worker python3 << EOF
from src.chart_generator import ChartGenerator
gen = ChartGenerator()
url = gen.generate_chart('DAX', '4H', 'manual_test')
print(f"Chart URL: {url}")
EOF
```

---

## 🐛 Troubleshooting

### Services Won't Start

```bash
# Check logs
docker-compose logs

# Check disk space
df -h

# Clean up Docker
docker system prune -a
```

### ChartGenerator Errors

```bash
# Check API key
docker exec tradematrix_celery_worker env | grep CHART_IMG

# Test manually
docker exec -it tradematrix_celery_worker python3
>>> from src.chart_generator import ChartGenerator
>>> gen = ChartGenerator()
```

### Database Connection Issues

```bash
# Test connection
docker exec -it tradematrix_celery_worker python3
>>> from src.config.supabase_client import get_supabase_client
>>> supabase = get_supabase_client()
>>> result = supabase.table('chart_snapshots').select('*').limit(1).execute()
```

### Redis Issues

```bash
# Restart Redis
docker-compose restart redis

# Check Redis logs
docker-compose logs redis

# Test connection
docker exec tradematrix_redis redis-cli ping
```

---

## 📝 Development Workflow

### Making Changes

1. **Develop locally** (test changes)
2. **Commit & push** to main branch
3. **Deploy to Hetzner**
   ```bash
   ./deploy.sh
   ```
4. **Verify deployment**
   ```bash
   ./health_check.sh
   ```
5. **Run tests**
   - Follow [TESTING_CHECKLIST.md](./TESTING_CHECKLIST.md)
6. **Monitor for 30 minutes**
   ```bash
   docker-compose logs -f celery_worker
   ```

### Emergency Rollback

If deployment causes issues:

```bash
./rollback.sh
```

---

## 🎯 Scheduled Tasks

### Task Schedule

| Task | Schedule | Purpose |
|------|----------|---------|
| `liquidity_alert_task` | Every 60 seconds | Check price alerts |
| `chart_watcher_task` | Every 4 hours | Generate & analyze charts |
| `morning_planner_task` | Daily 7:00 AM CET | Morning market preparation |
| `journal_bot_task` | Daily 5:00 PM CET | End-of-day trading summary |

### Verify Tasks Are Running

```bash
# Check Celery Beat logs
docker-compose logs celery_beat | grep "Scheduler: Sending"

# Check task execution
docker-compose logs celery_worker | grep "succeeded"
```

---

## 📈 API Usage Limits

### chart-img.com

- **Limit:** 1,000 requests/month (Free plan)
- **Current usage:** Check with `python3 monitor_dashboard.py`
- **Warning threshold:** 800 requests
- **Fallback:** External TradingView charts (no API call)

### Monitoring API Usage

```bash
# Today's usage
docker exec tradematrix_redis redis-cli GET "chart_img:requests:daily:$(date +%Y-%m-%d)"

# Last 7 days
python3 monitor_dashboard.py
```

---

## 🔐 Security

### Environment Variables

- Never commit `.env` to Git
- Use `.env.example` as template
- Rotate API keys every 90 days

### Server Access

- SSH key-based authentication only
- Disable password login
- Keep server updated: `apt update && apt upgrade`

### Docker

- Use trusted base images only
- Keep Docker updated
- Regular security scans

---

## 📞 Support

### Documentation

1. [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) - Deployment instructions
2. [MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md) - Database migrations
3. [TESTING_CHECKLIST.md](./TESTING_CHECKLIST.md) - Testing procedures

### Logs

```bash
# Application logs
docker-compose logs -f

# System logs
journalctl -u docker
```

### Monitoring

```bash
# Health check
./health_check.sh

# Dashboard
python3 monitor_dashboard.py
```

---

## 🎉 Deployment Checklist

### Before Deployment

- [ ] Code tested locally
- [ ] Git commit & push
- [ ] Supabase migration applied (if needed)
- [ ] Environment variables updated
- [ ] Backup created

### During Deployment

- [ ] Run `./deploy.sh`
- [ ] No errors in output
- [ ] All services started

### After Deployment

- [ ] Run `./health_check.sh` - all checks pass
- [ ] Run `python3 monitor_dashboard.py` - data showing
- [ ] Follow [TESTING_CHECKLIST.md](./TESTING_CHECKLIST.md)
- [ ] Monitor logs for 30 minutes
- [ ] Verify scheduled tasks running

---

**Deployment System Version:** 1.0
**Last Updated:** 2025-11-02
**Maintainer:** umi1970
**Server:** Hetzner CX11 (135.181.195.241)
