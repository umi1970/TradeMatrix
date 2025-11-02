# Post-Deployment Testing Checklist

This checklist ensures all TradeMatrix services are working correctly after deployment.

**Server:** 135.191.195.241 (Hetzner CX11)
**Date:** _______________
**Deployed By:** _______________
**Git Commit:** _______________

---

## 🎯 Quick Start

```bash
# SSH to server
ssh root@135.191.195.241

# Navigate to project
cd /root/tradematrix-agents

# Run health check
./health_check.sh

# Run monitoring dashboard
python3 monitor_dashboard.py
```

---

## ✅ Phase 1: Infrastructure Tests

### 1.1 Docker Services

- [ ] **All services running**
  ```bash
  docker-compose ps
  ```
  Expected: 3 services with status "Up"
  - [ ] `tradematrix_redis`
  - [ ] `tradematrix_celery_worker`
  - [ ] `tradematrix_celery_beat`

- [ ] **No container restarts**
  ```bash
  docker-compose ps | grep "Restarting"
  ```
  Expected: Empty output (no restarts)

### 1.2 Redis Health

- [ ] **Redis responding**
  ```bash
  docker exec tradematrix_redis redis-cli ping
  ```
  Expected: `PONG`

- [ ] **Redis memory usage < 100MB**
  ```bash
  docker exec tradematrix_redis redis-cli INFO memory | grep used_memory_human
  ```
  Expected: Under 100MB

- [ ] **Redis has keys**
  ```bash
  docker exec tradematrix_redis redis-cli DBSIZE
  ```
  Expected: > 0 keys

### 1.3 Environment Variables

- [ ] **All required variables set**
  ```bash
  docker exec tradematrix_celery_worker env | grep -E "SUPABASE|REDIS|CHART_IMG|OPENAI"
  ```
  Expected: All variables present (URLs/keys should not be empty)

---

## ✅ Phase 2: Service Tests

### 2.1 Celery Worker

- [ ] **Worker logs show no errors**
  ```bash
  docker-compose logs celery_worker --tail=100 | grep ERROR
  ```
  Expected: Empty output (no errors)

- [ ] **Worker initialized ChartGenerator**
  ```bash
  docker-compose logs celery_worker | grep "ChartGenerator initialized"
  ```
  Expected: `✅ ChartGenerator initialized successfully`

- [ ] **Worker connected to Redis**
  ```bash
  docker-compose logs celery_worker | grep "Connected to redis"
  ```
  Expected: `Connected to redis://redis:6379/0`

### 2.2 Celery Beat

- [ ] **Beat logs show scheduled tasks**
  ```bash
  docker-compose logs celery_beat --tail=50 | grep "Scheduler: Sending"
  ```
  Expected: Tasks being scheduled (chart_watcher_task, morning_planner_task, etc.)

- [ ] **Beat schedule includes all tasks**
  ```bash
  docker-compose logs celery_beat | grep -E "chart_watcher|morning_planner|journal_bot"
  ```
  Expected: All 3 task types mentioned

---

## ✅ Phase 3: Database Tests

### 3.1 Supabase Connection

- [ ] **Python can connect to Supabase**
  ```bash
  docker exec -it tradematrix_celery_worker python3 << EOF
  from src.config.supabase_client import get_supabase_client
  supabase = get_supabase_client()
  print("✅ Supabase connection OK")
  EOF
  ```
  Expected: `✅ Supabase connection OK`

### 3.2 Table Access

- [ ] **chart_snapshots table exists**
  ```bash
  docker exec -it tradematrix_celery_worker python3 << EOF
  from src.config.supabase_client import get_supabase_client
  supabase = get_supabase_client()
  result = supabase.table('chart_snapshots').select('*').limit(1).execute()
  print(f"✅ Table accessible, {len(result.data)} rows")
  EOF
  ```
  Expected: No errors (0 rows is OK if first deployment)

- [ ] **liquidity_alerts table exists**
  ```bash
  docker exec -it tradematrix_celery_worker python3 << EOF
  from src.config.supabase_client import get_supabase_client
  supabase = get_supabase_client()
  result = supabase.table('liquidity_alerts').select('*').limit(1).execute()
  print(f"✅ Table accessible")
  EOF
  ```
  Expected: No errors

- [ ] **eod_levels table has data**
  ```bash
  docker exec -it tradematrix_celery_worker python3 << EOF
  from src.config.supabase_client import get_supabase_client
  supabase = get_supabase_client()
  result = supabase.table('eod_levels').select('id', count='exact').execute()
  print(f"✅ EOD levels: {result.count} records")
  EOF
  ```
  Expected: > 0 records

---

## ✅ Phase 4: ChartGenerator Tests

### 4.1 ChartGenerator Initialization

- [ ] **ChartGenerator can be imported**
  ```bash
  docker exec -it tradematrix_celery_worker python3 << EOF
  from src.chart_generator import ChartGenerator
  print("✅ Import OK")
  EOF
  ```
  Expected: `✅ Import OK`

- [ ] **ChartGenerator can be instantiated**
  ```bash
  docker exec -it tradematrix_celery_worker python3 << EOF
  from src.chart_generator import ChartGenerator
  gen = ChartGenerator()
  print("✅ Instantiation OK")
  EOF
  ```
  Expected: `✅ Instantiation OK`

### 4.2 API Usage Tracking

- [ ] **API usage key exists in Redis**
  ```bash
  TODAY=$(date +%Y-%m-%d)
  docker exec tradematrix_redis redis-cli EXISTS "chart_img:requests:daily:$TODAY"
  ```
  Expected: `1` (exists) or `0` (not yet created - OK)

- [ ] **API usage counter working**
  ```bash
  TODAY=$(date +%Y-%m-%d)
  docker exec tradematrix_redis redis-cli GET "chart_img:requests:daily:$TODAY"
  ```
  Expected: Number or `(nil)` (if no charts generated yet)

---

## ✅ Phase 5: Scheduled Task Tests

### 5.1 ChartWatcher Task

- [ ] **ChartWatcher task scheduled**
  ```bash
  docker-compose logs celery_beat | grep "chart_watcher_task"
  ```
  Expected: Task scheduled (every 4 hours)

- [ ] **ChartWatcher can run manually**
  ```bash
  docker exec -it tradematrix_celery_worker python3 << EOF
  from src.tasks import chart_watcher_task
  try:
      result = chart_watcher_task()
      print(f"✅ ChartWatcher executed: {result}")
  except Exception as e:
      print(f"❌ Error: {e}")
  EOF
  ```
  Expected: Task completes without errors

### 5.2 MorningPlanner Task

- [ ] **MorningPlanner task scheduled**
  ```bash
  docker-compose logs celery_beat | grep "morning_planner_task"
  ```
  Expected: Task scheduled (daily at 7:00 AM CET)

- [ ] **MorningPlanner can run manually**
  ```bash
  docker exec -it tradematrix_celery_worker python3 << EOF
  from src.tasks import morning_planner_task
  try:
      result = morning_planner_task()
      print(f"✅ MorningPlanner executed: {result}")
  except Exception as e:
      print(f"❌ Error: {e}")
  EOF
  ```
  Expected: Task completes without errors

### 5.3 JournalBot Task

- [ ] **JournalBot task scheduled**
  ```bash
  docker-compose logs celery_beat | grep "journal_bot_task"
  ```
  Expected: Task scheduled (daily at 5:00 PM CET)

- [ ] **JournalBot can run manually**
  ```bash
  docker exec -it tradematrix_celery_worker python3 << EOF
  from src.tasks import journal_bot_task
  try:
      result = journal_bot_task()
      print(f"✅ JournalBot executed: {result}")
  except Exception as e:
      print(f"❌ Error: {e}")
  EOF
  ```
  Expected: Task completes without errors

---

## ✅ Phase 6: Integration Tests

### 6.1 LiquidityAlertEngine

- [ ] **LiquidityAlertEngine still working**
  ```bash
  docker exec -it tradematrix_celery_worker python3 << EOF
  from src.liquidity_alert_engine import LiquidityAlertEngine
  engine = LiquidityAlertEngine()
  print("✅ LiquidityAlertEngine OK")
  EOF
  ```
  Expected: No errors

- [ ] **Alert checking works**
  ```bash
  docker exec -it tradematrix_celery_worker python3 << EOF
  from src.liquidity_alert_engine import LiquidityAlertEngine
  engine = LiquidityAlertEngine()
  result = engine.check_all_alerts()
  print(f"✅ Checked alerts: {result}")
  EOF
  ```
  Expected: Task completes (may trigger alerts if conditions met)

### 6.2 PriceFetcher

- [ ] **PriceFetcher works**
  ```bash
  docker exec -it tradematrix_celery_worker python3 << EOF
  from src.price_fetcher import PriceFetcher
  fetcher = PriceFetcher()
  price = fetcher.fetch_price('DAX')
  print(f"✅ DAX price: {price}")
  EOF
  ```
  Expected: Valid DAX price (number > 0)

---

## ✅ Phase 7: Chart Generation Tests

### 7.1 Generate Test Chart

- [ ] **Generate chart manually**
  ```bash
  docker exec -it tradematrix_celery_worker python3 << EOF
  from src.chart_generator import ChartGenerator
  gen = ChartGenerator()
  url = gen.generate_chart('DAX', '4H', 'manual_test')
  print(f"✅ Chart generated: {url}")
  EOF
  ```
  Expected: Valid URL (https://chart-img.com/... or TradingView fallback)

### 7.2 Verify Chart in Supabase

- [ ] **Chart saved to database**
  ```bash
  docker exec -it tradematrix_celery_worker python3 << EOF
  from src.config.supabase_client import get_supabase_client
  supabase = get_supabase_client()
  result = supabase.table('chart_snapshots').select('*').order('generated_at', desc=True).limit(1).execute()
  if result.data:
      chart = result.data[0]
      print(f"✅ Latest chart: {chart['symbol']} {chart['timeframe']} at {chart['generated_at']}")
  else:
      print("⚠️ No charts in database yet")
  EOF
  ```
  Expected: Chart entry exists with correct metadata

### 7.3 Verify Chart URL Accessible

- [ ] **Chart URL returns image**
  ```bash
  docker exec -it tradematrix_celery_worker python3 << EOF
  from src.config.supabase_client import get_supabase_client
  import httpx

  supabase = get_supabase_client()
  result = supabase.table('chart_snapshots').select('chart_url').order('generated_at', desc=True).limit(1).execute()

  if result.data:
      url = result.data[0]['chart_url']
      response = httpx.get(url, timeout=10)
      if response.status_code == 200:
          print(f"✅ Chart URL accessible: {url}")
      else:
          print(f"❌ Chart URL failed: {response.status_code}")
  else:
      print("⚠️ No charts to test")
  EOF
  ```
  Expected: 200 OK response

---

## ✅ Phase 8: Push Notification Tests

### 8.1 Push Service

- [ ] **PushNotificationService works**
  ```bash
  docker exec -it tradematrix_celery_worker python3 << EOF
  from src.push_notification_service import PushNotificationService
  service = PushNotificationService()
  print("✅ Push service OK")
  EOF
  ```
  Expected: No errors

- [ ] **VAPID keys configured**
  ```bash
  docker exec tradematrix_celery_worker env | grep VAPID
  ```
  Expected: VAPID_PUBLIC_KEY and VAPID_PRIVATE_KEY set

---

## ✅ Phase 9: Monitoring Tests

### 9.1 Health Check Script

- [ ] **Health check runs successfully**
  ```bash
  ./health_check.sh
  ```
  Expected: All checks pass, no errors

### 9.2 Monitoring Dashboard

- [ ] **Dashboard displays data**
  ```bash
  python3 monitor_dashboard.py
  ```
  Expected: Dashboard shows:
  - Redis status
  - API usage
  - Recent chart snapshots
  - Recent liquidity alerts
  - Active subscriptions

---

## ✅ Phase 10: System Resources

### 10.1 Disk Space

- [ ] **Disk usage < 80%**
  ```bash
  df -h /
  ```
  Expected: Used < 80%

### 10.2 Memory Usage

- [ ] **Memory usage < 80%**
  ```bash
  free -h
  ```
  Expected: Used < 3.2GB (of 4GB total)

### 10.3 CPU Load

- [ ] **CPU load reasonable**
  ```bash
  top -bn1 | head -5
  ```
  Expected: Load average < 2.0

---

## ✅ Phase 11: Log Analysis

### 11.1 No Critical Errors

- [ ] **No CRITICAL errors in worker logs**
  ```bash
  docker-compose logs celery_worker | grep CRITICAL
  ```
  Expected: Empty output

- [ ] **No ERROR in last 100 lines**
  ```bash
  docker-compose logs celery_worker --tail=100 | grep ERROR
  ```
  Expected: Empty output (or only harmless errors)

### 11.2 Task Execution

- [ ] **Tasks completing successfully**
  ```bash
  docker-compose logs celery_worker | grep "Task.*succeeded"
  ```
  Expected: Multiple successful task completions

---

## ✅ Phase 12: 24-Hour Stability Test

**After 24 hours of deployment:**

- [ ] **No service restarts**
  ```bash
  docker-compose ps
  ```
  Expected: All services still "Up", no restart counts

- [ ] **Memory leak check**
  ```bash
  docker stats --no-stream
  ```
  Expected: Memory usage stable (not growing continuously)

- [ ] **API usage within limits**
  ```bash
  python3 monitor_dashboard.py
  ```
  Expected: Daily API usage < 1,000 requests

- [ ] **Charts generated on schedule**
  - Check Supabase dashboard for chart_snapshots entries
  - Expected: Charts generated every 4 hours

- [ ] **Alerts triggered correctly**
  - Check Supabase dashboard for liquidity_alerts entries
  - Expected: Alerts triggered when price crosses levels

---

## 📊 Test Results Summary

**Deployment Date:** _______________
**Testing Completed:** _______________

| Phase | Tests Passed | Tests Failed | Status |
|-------|--------------|--------------|--------|
| Phase 1: Infrastructure | ___ / 8 | ___ | ☐ Pass ☐ Fail |
| Phase 2: Services | ___ / 5 | ___ | ☐ Pass ☐ Fail |
| Phase 3: Database | ___ / 3 | ___ | ☐ Pass ☐ Fail |
| Phase 4: ChartGenerator | ___ / 3 | ___ | ☐ Pass ☐ Fail |
| Phase 5: Scheduled Tasks | ___ / 6 | ___ | ☐ Pass ☐ Fail |
| Phase 6: Integration | ___ / 3 | ___ | ☐ Pass ☐ Fail |
| Phase 7: Chart Generation | ___ / 3 | ___ | ☐ Pass ☐ Fail |
| Phase 8: Push Notifications | ___ / 2 | ___ | ☐ Pass ☐ Fail |
| Phase 9: Monitoring | ___ / 2 | ___ | ☐ Pass ☐ Fail |
| Phase 10: System Resources | ___ / 3 | ___ | ☐ Pass ☐ Fail |
| Phase 11: Log Analysis | ___ / 2 | ___ | ☐ Pass ☐ Fail |
| Phase 12: 24-Hour Stability | ___ / 5 | ___ | ☐ Pass ☐ Fail |
| **TOTAL** | **___ / 45** | **___** | **☐ Pass ☐ Fail** |

---

## 🐛 Issues Found

| Issue | Severity | Description | Resolution | Status |
|-------|----------|-------------|------------|--------|
| 1. | ☐ Critical ☐ High ☐ Medium ☐ Low | | | ☐ Fixed ☐ Open |
| 2. | ☐ Critical ☐ High ☐ Medium ☐ Low | | | ☐ Fixed ☐ Open |
| 3. | ☐ Critical ☐ High ☐ Medium ☐ Low | | | ☐ Fixed ☐ Open |

---

## ✅ Sign-Off

**Deployment Successful:** ☐ Yes ☐ No

**Tested By:** _______________
**Date:** _______________
**Signature:** _______________

**Notes:**
_______________________________________________________________________
_______________________________________________________________________
_______________________________________________________________________

---

**Testing Checklist Version:** 1.0
**Last Updated:** 2025-11-02
**Maintainer:** umi1970
