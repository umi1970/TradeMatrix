# Deployment Guide: Twelvedata Integration

## 📋 Changes Summary

### Code Changes (Committed: 8a38a44)
- ✅ Updated `price_fetcher.py` with ETF proxy symbols:
  - **DAX**: `EXS1` (iShares Core DAX) on `XETR`
  - **NASDAQ 100**: `QQQ` (Invesco QQQ) on `NASDAQ`
  - **DOW JONES**: `DIA` (SPDR DIA) on `NYSE`
  - **EUR/USD**: `EUR/USD` (unchanged)
  - **EUR/GBP**: `EUR/GBP` (unchanged)
- ✅ All 5 symbols verified working (test_twelvedata_symbols.py)

### Required Actions

## Step 1: Execute Database Migration 🗄️

**Run this SQL in Supabase SQL Editor:**

1. Go to: https://supabase.com/dashboard/project/htnlhazqzpwfyhnngfsn/sql
2. Paste this SQL:

```sql
-- Migration 016: Allow 'twelvedata' in price_cache.data_source
ALTER TABLE public.price_cache DROP CONSTRAINT IF EXISTS price_cache_data_source_check;

ALTER TABLE public.price_cache
ADD CONSTRAINT price_cache_data_source_check
CHECK (data_source IN ('finnhub', 'alpha_vantage', 'twelvedata', 'yfinance', 'manual'));

COMMENT ON CONSTRAINT price_cache_data_source_check ON public.price_cache IS 'Allowed data sources: finnhub, alpha_vantage, twelvedata, yfinance, manual';
```

3. Click "Run"
4. ✅ Should see: "Success. No rows returned"

---

## Step 2: Deploy to Hetzner Server 🚀

### 2.1 SSH to Hetzner
```bash
ssh root@135.181.195.241
```

### 2.2 Navigate to project directory
```bash
cd /root/tradematrix
```

### 2.3 Pull latest code
```bash
git pull origin main
```

Expected output:
```
Updating 6f952fb..8a38a44
Fast-forward
 hetzner-deploy/src/price_fetcher.py           | 16 ++--
 hetzner-deploy/test_twelvedata_symbols.py     | 136 ++++++++++++++++++++++++++
 2 files changed, 136 insertions(+), 8 deletions(-)
```

### 2.4 Fix environment variable in .env
```bash
cd hetzner-deploy

# Update TWELVE_DATA_API_KEY to TWELVEDATA_API_KEY
sed -i 's/TWELVE_DATA_API_KEY=/TWELVEDATA_API_KEY=/' .env

# Verify the change
grep "TWELVEDATA_API_KEY" .env
```

Expected output:
```
TWELVEDATA_API_KEY=c25b65a4f77c488ca9b318faf5b21ef7
```

### 2.5 Test the new symbols (optional but recommended)
```bash
python3 test_twelvedata_symbols.py
```

Expected output:
```
🎉 All symbols verified! Ready for production.
5/5 symbols working correctly
```

### 2.6 Restart Docker services
```bash
docker-compose down
docker-compose up -d
```

### 2.7 Verify services are running
```bash
docker-compose ps
```

Expected output: All services should be "Up"

### 2.8 Check Celery logs
```bash
docker-compose logs -f celery-worker --tail=50
```

Look for:
- ✅ No import errors
- ✅ Successful Twelvedata API calls
- ✅ Price updates for all 5 symbols

---

## Step 3: Verify Dashboard 🎯

1. Open: https://tradematrix.netlify.app
2. Login
3. Check dashboard widgets:
   - **EOD Levels Today** should show current data
   - **Market Overview** should show updated prices
   - Prices should be from today, not Friday

---

## Troubleshooting 🔧

### If Celery shows "API key incorrect":
```bash
# Check .env has correct variable name
grep "TWELVEDATA_API_KEY" .env

# Should output:
# TWELVEDATA_API_KEY=c25b65a4f77c488ca9b318faf5b21ef7
```

### If price fetching fails for a symbol:
```bash
# Run test script to see which symbol is failing
python3 test_twelvedata_symbols.py

# Check API key is valid at Twelvedata dashboard:
# https://twelvedata.com/account/api-keys
```

### If database constraint error occurs:
- Migration 016 was not executed in Supabase
- Go back to Step 1 and run the migration SQL

---

## Success Criteria ✅

- [ ] Migration 016 executed in Supabase (no errors)
- [ ] Git pull successful on Hetzner
- [ ] .env updated with TWELVEDATA_API_KEY
- [ ] Test script shows 5/5 symbols working
- [ ] Docker services restarted successfully
- [ ] Celery logs show successful price updates
- [ ] Dashboard displays current prices (not Friday's EOD data)

---

## Next Steps 🚀

After successful deployment:
1. **WebSocket Integration** - For true real-time updates
2. **Rate Limit Monitoring** - Track Twelvedata API usage (55 calls/min limit)
3. **Alert Latency Optimization** - Consider reducing polling from 60s to 30s

---

**Generated:** 2025-11-03
**Commit:** 8a38a44
**Migration:** 016_allow_twelvedata.sql
