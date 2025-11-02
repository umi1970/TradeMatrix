# TradeMatrix Deployment Quick Reference

One-page reference for common deployment operations.

**Server:** 135.181.195.241 | **Location:** `/root/tradematrix-agents`

---

## 🚀 Deployment Commands

```bash
# Deploy latest code
./deploy.sh

# Check system health
./health_check.sh

# Live monitoring dashboard
python3 monitor_dashboard.py

# Rollback to previous version
./rollback.sh

# Rollback to specific commit
./rollback.sh abc1234
```

---

## 🐳 Docker Commands

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# Restart services
docker-compose restart

# View service status
docker-compose ps

# View logs (real-time)
docker-compose logs -f celery_worker

# View last 100 log lines
docker-compose logs celery_worker --tail=100

# Rebuild services
docker-compose build --no-cache
docker-compose up -d
```

---

## 🔍 Debugging Commands

```bash
# Check Redis
docker exec tradematrix_redis redis-cli ping

# Check API usage today
docker exec tradematrix_redis redis-cli GET "chart_img:requests:daily:$(date +%Y-%m-%d)"

# Test ChartGenerator
docker exec -it tradematrix_celery_worker python3 << EOF
from src.chart_generator import ChartGenerator
gen = ChartGenerator()
print("✅ OK")
EOF

# Test Supabase connection
docker exec -it tradematrix_celery_worker python3 << EOF
from src.config.supabase_client import get_supabase_client
supabase = get_supabase_client()
result = supabase.table('chart_snapshots').select('*').limit(1).execute()
print(f"✅ {len(result.data)} rows")
EOF

# Check environment variables
docker exec tradematrix_celery_worker env | grep -E "SUPABASE|REDIS|CHART_IMG"

# Check for errors in logs
docker-compose logs celery_worker | grep ERROR
```

---

## 📊 Monitoring Commands

```bash
# Disk space
df -h

# Memory usage
free -h

# Docker stats
docker stats --no-stream

# System load
top -bn1 | head -10

# Redis memory
docker exec tradematrix_redis redis-cli INFO memory | grep used_memory_human

# Count Redis keys
docker exec tradematrix_redis redis-cli DBSIZE
```

---

## 🔧 Maintenance Commands

```bash
# Update code only (no restart)
git pull origin main

# Restart without rebuild
docker-compose restart

# Clean Docker system
docker system prune -a

# Clear Redis cache
docker exec tradematrix_redis redis-cli FLUSHDB

# View active Celery tasks
docker exec tradematrix_celery_worker celery -A src.tasks inspect active

# View scheduled tasks
docker exec tradematrix_celery_beat celery -A src.tasks inspect scheduled
```

---

## 🐛 Troubleshooting Quick Fixes

### Services won't start
```bash
docker-compose down
docker system prune -a
docker-compose build --no-cache
docker-compose up -d
```

### Redis not responding
```bash
docker-compose restart redis
docker exec tradematrix_redis redis-cli ping
```

### High memory usage
```bash
docker-compose restart celery_worker
docker exec tradematrix_redis redis-cli FLUSHDB
```

### Database connection issues
```bash
# Check environment variables
docker exec tradematrix_celery_worker env | grep SUPABASE
```

### Chart generation failing
```bash
# Check API key
docker exec tradematrix_celery_worker env | grep CHART_IMG

# Check API usage
docker exec tradematrix_redis redis-cli GET "chart_img:requests:daily:$(date +%Y-%m-%d)"
```

---

## 📝 File Locations

```
/root/tradematrix-agents/
├── .env                    # Environment variables (DO NOT commit!)
├── docker-compose.yml      # Service configuration
├── deploy.sh               # Deployment script
├── health_check.sh         # Health monitoring
├── rollback.sh             # Rollback script
├── monitor_dashboard.py    # Monitoring dashboard
├── src/                    # Application code
├── logs/                   # Application logs
└── backups/                # Backups (created by scripts)
```

---

## 🔐 Important Files

```bash
# View environment variables
cat .env

# Edit environment variables
nano .env

# View Docker configuration
cat docker-compose.yml

# View Python dependencies
cat requirements.txt
```

---

## 📈 Scheduled Tasks

| Task | Frequency | Time (CET) |
|------|-----------|------------|
| Liquidity Alerts | Every 60s | - |
| Chart Watcher | Every 4h | - |
| Morning Planner | Daily | 7:00 AM |
| Journal Bot | Daily | 5:00 PM |

---

## ⚠️ API Limits

- **chart-img.com:** 1,000 requests/month
- **Warning at:** 800 requests
- **Check usage:** `python3 monitor_dashboard.py`

---

## 📞 Emergency Contacts

- **Documentation:** See [README.md](./README.md)
- **Deployment Guide:** See [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)
- **Testing:** See [TESTING_CHECKLIST.md](./TESTING_CHECKLIST.md)

---

## ✅ Pre-Deployment Checklist

- [ ] Code tested locally
- [ ] Git commit & push
- [ ] Migration applied (if needed)
- [ ] `.env` updated
- [ ] Backup created
- [ ] Run `./deploy.sh`
- [ ] Run `./health_check.sh`
- [ ] Monitor for 30 minutes

---

## 🎯 Post-Deployment Checklist

- [ ] All services running (`docker-compose ps`)
- [ ] No errors in logs
- [ ] Redis responding
- [ ] ChartGenerator working
- [ ] Supabase connection OK
- [ ] API usage tracked
- [ ] Scheduled tasks running

---

**Quick Reference Version:** 1.0
**Last Updated:** 2025-11-02
