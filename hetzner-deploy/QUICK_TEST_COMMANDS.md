# Quick Test Commands - Chart Storage Fix

## Local Testing

### 1. Run Full Test Suite
```bash
cd /mnt/c/Users/uzobu/Documents/SaaS/TradeMatrix/hetzner-deploy
python3 test_chart_storage.py
```

**Expected Output:**
```
✅ ALL TESTS PASSED!
```

---

### 2. Check Environment Variables
```bash
cd /mnt/c/Users/uzobu/Documents/SaaS/TradeMatrix/hetzner-deploy
grep -E "SUPABASE_URL|SUPABASE_SERVICE_KEY|CHART_IMG_API_KEY|REDIS_URL" .env
```

**Expected:**
```
SUPABASE_URL=https://htnlhazqzpwfyhnngfsn.supabase.co
SUPABASE_SERVICE_KEY=eyJhb...
CHART_IMG_API_KEY=...
REDIS_URL=redis://localhost:6379/0
```

---

### 3. Test Redis Connection
```bash
redis-cli ping
```

**Expected:** `PONG`

---

### 4. Quick Python Test
```bash
cd /mnt/c/Users/uzobu/Documents/SaaS/TradeMatrix/hetzner-deploy
python3 << 'EOF'
import asyncio
from src.chart_service import ChartService

async def test():
    service = ChartService()
    url = await service.generate_chart_url(
        symbol="DAX",
        timeframe="1h",
        agent_name="TestAgent"
    )
    print(f"Chart URL: {url}")
    assert url.startswith("https://htnlhazqzpwfyhnngfsn.supabase.co/storage/")
    print("✅ Test passed!")

asyncio.run(test())
EOF
```

---

## Supabase Dashboard Checks

### 1. Verify Storage Bucket Exists
**URL:** https://supabase.com/dashboard/project/htnlhazqzpwfyhnngfsn/storage/buckets

**Check:**
- ✅ Bucket `chart-snapshots` exists
- ✅ Public access enabled
- ✅ Allowed MIME: `image/png`

---

### 2. View Uploaded Charts
**URL:** https://supabase.com/dashboard/project/htnlhazqzpwfyhnngfsn/storage/buckets/chart-snapshots

**Check:**
- ✅ Folder structure: `TestAgent/2025/11/06/`
- ✅ Files: `DAX_1h_YYYYMMDD_HHMMSS.png`
- ✅ Files are viewable (click to preview)

---

### 3. Check Database Records
**SQL Editor:**
```sql
-- Check recent snapshots
SELECT
  id,
  timeframe,
  chart_url,
  generated_at
FROM chart_snapshots
ORDER BY generated_at DESC
LIMIT 10;

-- Verify all URLs are Supabase Storage URLs
SELECT
  COUNT(*) AS total,
  COUNT(*) FILTER (WHERE chart_url LIKE '%supabase.co/storage%') AS storage_urls,
  COUNT(*) FILTER (WHERE chart_url LIKE '%chart-img.com%') AS old_urls
FROM chart_snapshots;
```

**Expected:**
- `storage_urls = total`
- `old_urls = 0`

---

## Server Deployment

### 1. SSH into Server
```bash
ssh root@135.181.195.241
```

---

### 2. Pull Latest Code
```bash
cd /opt/tradematrix
git pull origin main
```

**Expected:**
```
Updating 6ca8754..abcd123
Fast-forward
 hetzner-deploy/src/chart_service.py | 75 ++++++++++++++++++++++++++----------
 1 file changed, 75 insertions(+), 15 deletions(-)
```

---

### 3. Restart Services
```bash
docker-compose restart celery-worker
```

**Expected:**
```
Restarting celery-worker ... done
```

---

### 4. Check Logs (Live)
```bash
docker-compose logs -f celery-worker
```

**Look for:**
```
✅ Chart generated and uploaded: DAX 1h
📊 Storage URL: https://htnlhazqzpwfyhnngfsn.supabase.co/storage/v1/object/public/chart-snapshots/...
✅ Chart uploaded to storage: ChartWatcher/2025/11/06/DAX_1h_20251106_143000.png
```

**Stop logs:** Press `Ctrl+C`

---

### 5. Check Recent Logs (Last 100 Lines)
```bash
docker-compose logs --tail=100 celery-worker | grep -E "Chart|Storage|403"
```

**Expected:**
- ✅ "Chart generated and uploaded" messages
- ✅ "Chart uploaded to storage" messages
- ❌ No "403 Forbidden" errors

---

### 6. Test Chart Generation on Server
```bash
docker-compose exec celery-worker python3 /app/test_chart_storage.py
```

**Expected:**
```
✅ ALL TESTS PASSED!
```

---

## Monitoring (24 Hours)

### 1. Watch for Errors
```bash
ssh root@135.181.195.241
docker-compose logs -f celery-worker | grep -E "ERROR|403|Failed"
```

**Expected:** No errors

---

### 2. Count Successful Chart Uploads
```bash
ssh root@135.181.195.241
docker-compose logs celery-worker | grep "Chart uploaded to storage" | wc -l
```

**Expected:** Increasing number over time

---

### 3. Check Storage Bucket Size
**Supabase Dashboard → Storage → chart-snapshots**

**Expected:** Files accumulating in organized folders

---

### 4. Verify ChartWatcher Analyses
```sql
-- Check recent chart analyses
SELECT
  COUNT(*) AS total_analyses,
  MAX(created_at) AS latest_analysis
FROM chart_analyses
WHERE created_at > NOW() - INTERVAL '1 day';
```

**Expected:** `total_analyses > 0`

---

## Troubleshooting Quick Fixes

### Error: "bucket chart-snapshots not found"

```bash
# Fix: Create bucket in Supabase Dashboard
# URL: https://supabase.com/dashboard/project/htnlhazqzpwfyhnngfsn/storage/buckets
# Click "Create bucket" → Name: chart-snapshots → Public: ✅
```

---

### Error: "403 Forbidden" on Storage URL

```bash
# Fix: Enable public access on bucket
# Supabase Dashboard → Storage → chart-snapshots → Settings → Public: ✅
```

---

### Error: "Permission denied for storage upload"

```bash
# Fix: Verify SUPABASE_SERVICE_KEY (not anon key)
ssh root@135.181.195.241
grep SUPABASE_SERVICE_KEY /opt/tradematrix/.env
# Should start with: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

### Error: "Redis connection failed"

```bash
# Check Redis is running
docker-compose ps redis

# Restart Redis
docker-compose restart redis

# Test connection
docker-compose exec redis redis-cli ping
# Expected: PONG
```

---

## Rollback (If Needed)

### Quick Rollback
```bash
ssh root@135.181.195.241
cd /opt/tradematrix

# Revert to previous version
git checkout HEAD~1 -- hetzner-deploy/src/chart_service.py

# Commit rollback
git add hetzner-deploy/src/chart_service.py
git commit -m "Rollback: Chart storage upload (temporarily)"

# Restart
docker-compose restart celery-worker
```

---

## Success Indicators

✅ **All Green:**
- Test script passes
- No 403 errors in logs
- Storage bucket has files
- chart_snapshots table has new records
- ChartWatcher analyses succeed

❌ **Issues:**
- 403 errors persist
- Storage uploads fail
- chart_analyses table empty

---

## Quick Links

- **Supabase Dashboard:** https://supabase.com/dashboard/project/htnlhazqzpwfyhnngfsn
- **Storage Buckets:** https://supabase.com/dashboard/project/htnlhazqzpwfyhnngfsn/storage/buckets
- **SQL Editor:** https://supabase.com/dashboard/project/htnlhazqzpwfyhnngfsn/editor
- **Server:** ssh root@135.181.195.241

---

**Last Updated:** 2025-11-06
**Status:** Ready for Testing
