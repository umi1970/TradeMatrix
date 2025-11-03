# Backend Updates: Minimal Changes

**Last Updated:** 2025-11-03

---

## 🎯 Key Insight: Backend Almost Unchanged!

**Why?** TradingView Widgets handle ALL live price display.

**Backend Role:** Only for Liquidity Alert System (existing functionality)

---

## ✅ What STAYS the Same

### Hetzner Server Configuration
- **IP:** 135.181.195.241
- **Services:** Redis + Celery Beat + Celery Worker
- **Docker Compose:** No changes
- **Deployment:** Already running 24/7

### Alert System
- **Celery Beat:** Runs every 60 seconds (unchanged)
- **Price Fetching:** yfinance (indices) + Twelvedata HTTP (forex)
- **Liquidity Checks:** Yesterday High/Low, Pivot Points
- **Push Notifications:** Web Push API

### No WebSocket!
- ❌ No WebSocket server needed
- ❌ No Socket.io setup
- ❌ No connection management
- ❌ No broadcasting logic

**Reason:** TradingView handles all real-time data!

---

## 🔧 What CHANGES (Minimal!)

### File: `hetzner-deploy/src/alert_engine.py`

**Change:** Dynamic symbol loading instead of fixed list

**OLD:**
```python
# Fixed symbol list
SYMBOLS = ['^GDAXI', '^NDX', '^DJI', 'EURUSD', 'EURGBP']

def check_all_alerts():
    for symbol in SYMBOLS:
        check_liquidity_alerts(symbol)
```

**NEW:**
```python
def get_all_watched_symbols():
    """Get unique symbols from all user watchlists"""
    try:
        result = supabase.table('user_watchlist')\
            .select('symbols(symbol, is_active)')\
            .execute()

        # Extract unique symbols that are active
        symbols = set()
        for item in result.data:
            if item['symbols'] and item['symbols']['is_active']:
                symbols.add(item['symbols']['symbol'])

        return list(symbols)
    except Exception as e:
        print(f"Error fetching watched symbols: {e}")
        # Fallback to default symbols
        return ['^GDAXI', '^NDX', '^DJI', 'EURUSD', 'EURGBP']

def check_all_alerts():
    """Check alerts for all watched symbols"""
    watched_symbols = get_all_watched_symbols()
    print(f"Checking alerts for {len(watched_symbols)} symbols: {watched_symbols}")

    for symbol in watched_symbols:
        check_liquidity_alerts(symbol)
```

**Benefits:**
- ✅ Automatically monitors new symbols users add
- ✅ Removes symbols when all users remove them
- ✅ Fallback to default symbols if DB query fails

---

## 📁 File Changes Summary

| File | Change | Lines Changed |
|------|--------|---------------|
| `alert_engine.py` | Add `get_all_watched_symbols()` | +25 lines |
| `alert_engine.py` | Update `check_all_alerts()` | ~5 lines |
| **Total** | | **~30 lines** |

---

## 🚀 Deployment Steps (Hetzner)

### Option 1: SSH + Direct Edit

```bash
# SSH into Hetzner
ssh root@135.181.195.241

# Navigate to project
cd /root/TradeMatrix/hetzner-deploy

# Edit alert_engine.py
nano src/alert_engine.py
# (Add get_all_watched_symbols function)

# Restart Celery worker
docker-compose restart celery-worker

# Check logs
docker-compose logs -f celery-worker
```

### Option 2: Git Pull (If committed)

```bash
# On local machine: Commit changes
git add hetzner-deploy/src/alert_engine.py
git commit -m "feat: Dynamic symbol loading from user_watchlist"
git push origin main

# On Hetzner server
ssh root@135.181.195.241
cd /root/TradeMatrix/hetzner-deploy
git pull origin main
docker-compose restart celery-worker
```

---

## 🧪 Testing Backend Changes

### 1. Test Dynamic Symbol Loading

**Before:** Add new symbol to user_watchlist via frontend

**Check:** Celery logs should show new symbol

```bash
# SSH into Hetzner
ssh root@135.181.195.241

# Tail Celery worker logs
docker-compose logs -f celery-worker

# Look for:
# "Checking alerts for 6 symbols: ['^GDAXI', '^NDX', '^DJI', 'EURUSD', 'EURGBP', 'GBPUSD']"
```

### 2. Test Fallback Mechanism

**Simulate DB failure:**

```python
# Temporarily break query
def get_all_watched_symbols():
    raise Exception("Simulated DB error")
    # ... rest of function
```

**Expected:** Celery should use fallback symbols, not crash

---

## 🔍 Code Diff (Complete)

### `hetzner-deploy/src/alert_engine.py`

```diff
+ def get_all_watched_symbols():
+     """
+     Get unique symbols from all user watchlists (dynamic)
+
+     Returns:
+         List of symbol strings (e.g., ['^GDAXI', 'EURUSD'])
+
+     Fallback to default symbols if query fails
+     """
+     try:
+         result = supabase.table('user_watchlist')\
+             .select('symbols(symbol, is_active)')\
+             .execute()
+
+         # Extract unique active symbols
+         symbols = set()
+         for item in result.data:
+             if item['symbols'] and item['symbols']['is_active']:
+                 symbols.add(item['symbols']['symbol'])
+
+         if not symbols:
+             print("⚠️  No symbols in any watchlist, using defaults")
+             return ['^GDAXI', '^NDX', '^DJI', 'EURUSD', 'EURGBP']
+
+         return list(symbols)
+     except Exception as e:
+         print(f"❌ Error fetching watched symbols: {e}")
+         print("   Using fallback symbols")
+         return ['^GDAXI', '^NDX', '^DJI', 'EURUSD', 'EURGBP']

  def check_all_alerts():
-     """Check liquidity alerts for all configured symbols"""
-     SYMBOLS = ['^GDAXI', '^NDX', '^DJI', 'EURUSD', 'EURGBP']
-
-     for symbol in SYMBOLS:
+     """Check liquidity alerts for all watched symbols (dynamic)"""
+     watched_symbols = get_all_watched_symbols()
+     print(f"📊 Checking alerts for {len(watched_symbols)} symbols: {watched_symbols}")
+
+     for symbol in watched_symbols:
          check_liquidity_alerts(symbol)
```

---

## ⚙️ Environment Variables

**No new variables needed!**

Existing `.env` already has:
- ✅ `SUPABASE_URL`
- ✅ `SUPABASE_SERVICE_KEY`
- ✅ `TWELVEDATA_API_KEY`

---

## 📊 Performance Impact

### Before (Fixed Symbols)
- Monitored: 5 symbols
- Price fetches per hour: 5 × 60 = 300
- DB queries: 0 (hardcoded list)

### After (Dynamic Symbols)
- Monitored: Variable (depends on users)
- Price fetches per hour: N × 60 (N = unique symbols)
- DB queries: 1 per minute (get watched symbols)

**Example with 100 users:**
- Each adds 10 symbols
- ~30 unique symbols total (overlap)
- Fetches: 30 × 60 = 1,800 per hour
- Cost: Still €0 (yfinance free, Twelvedata has 55 calls/min limit = 3,300/hour) ✅

---

## 🚨 Potential Issues & Solutions

### Issue 1: Too Many Unique Symbols

**Scenario:** 1,000 users add 1,000 different exotic symbols

**Problem:** Twelvedata HTTP rate limit (55 calls/min = 3,300/hour)

**Solution:**
```python
def get_all_watched_symbols():
    # ... existing code ...

    # Limit to top N most popular symbols
    MAX_SYMBOLS = 50
    if len(symbols) > MAX_SYMBOLS:
        # Get symbol popularity (count users watching each)
        popularity = {}
        for item in result.data:
            sym = item['symbols']['symbol']
            popularity[sym] = popularity.get(sym, 0) + 1

        # Return top 50 most watched
        return sorted(popularity, key=popularity.get, reverse=True)[:MAX_SYMBOLS]

    return list(symbols)
```

### Issue 2: Database Connection Failure

**Problem:** Supabase temporarily unavailable

**Solution:** Already implemented! Fallback to default symbols

```python
except Exception as e:
    print(f"❌ Error: {e}")
    return ['^GDAXI', '^NDX', '^DJI', 'EURUSD', 'EURGBP']  # Fallback
```

---

## 📋 Deployment Checklist

- [ ] Update `alert_engine.py` with `get_all_watched_symbols()`
- [ ] Test locally (if possible)
- [ ] Commit and push to git
- [ ] SSH into Hetzner server
- [ ] Pull latest code OR edit file directly
- [ ] Restart Celery worker: `docker-compose restart celery-worker`
- [ ] Monitor logs: `docker-compose logs -f celery-worker`
- [ ] Verify: New symbols appear in logs
- [ ] Test: Add symbol via frontend, check if monitored within 60s

---

**Next:** [05_TESTING_GUIDE.md](./05_TESTING_GUIDE.md)
