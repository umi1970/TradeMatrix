# Testing Guide: TradingView Watchlist

**Last Updated:** 2025-11-03

---

## 🧪 Testing Checklist

### Phase 1: Database Testing ✅ (DONE)

- [x] Migration 017 executed successfully
- [x] `user_watchlist` table exists
- [x] RLS policies active
- [x] Indexes created
- [ ] `symbols.tv_symbol` column added
- [ ] Existing symbols have tv_symbol values

---

### Phase 2: Frontend - Symbol Picker

#### 2.1 Component Rendering
- [ ] Modal opens when clicking "Edit Watchlist"
- [ ] Modal shows two columns (Watchlist + Available)
- [ ] Search input filters symbols correctly
- [ ] All active symbols visible in "Available" column

#### 2.2 Adding Symbols
- [ ] Click symbol in "Available" → adds to "Watchlist"
- [ ] Symbol appears in correct position
- [ ] Symbol removed from "Available" list
- [ ] Can add up to 10 symbols
- [ ] 11th symbol shows "Maximum 10 symbols" alert

#### 2.3 Removing Symbols
- [ ] Click X button → removes symbol
- [ ] Symbol reappears in "Available" list
- [ ] Positions recalculated correctly (no gaps)

#### 2.4 Saving
- [ ] Click "Save Watchlist" → saves to database
- [ ] Modal closes after save
- [ ] Dashboard refreshes with new watchlist
- [ ] Supabase table updated correctly

#### 2.5 Edge Cases
- [ ] Empty watchlist → shows "No symbols selected"
- [ ] Search with no results → shows "No symbols found"
- [ ] Cancel button → discards changes
- [ ] Reload page → watchlist persists

---

### Phase 3: Frontend - TradingView Widgets

#### 3.1 Widget Rendering
- [ ] Each symbol displays as TradingView widget
- [ ] Widgets load without errors
- [ ] Loading state shows while widget initializes
- [ ] No console errors

#### 3.2 Live Data Display
- [ ] Current price visible
- [ ] Price change % visible
- [ ] Mini chart renders
- [ ] Price updates automatically (TradingView handles)

#### 3.3 Responsive Design
- [ ] Desktop (1920px): 3 columns
- [ ] Tablet (768px): 2 columns
- [ ] Mobile (375px): 1 column
- [ ] Widgets scale correctly

#### 3.4 Empty State
- [ ] No symbols → shows "No symbols in your watchlist"
- [ ] "Add Symbols" button visible
- [ ] Clicking button opens Symbol Picker

---

### Phase 4: Backend - Alert System

#### 4.1 Dynamic Symbol Loading
- [ ] Celery logs show: "Checking alerts for N symbols: [...]"
- [ ] Adding symbol via frontend → appears in logs within 60s
- [ ] Removing symbol → disappears from logs

#### 4.2 Price Fetching
- [ ] yfinance: Indices (^GDAXI, ^NDX, ^DJI) fetch correctly
- [ ] Twelvedata: Forex (EURUSD, EURGBP) fetch correctly
- [ ] `price_cache` table updates every 60s
- [ ] No fetch errors in logs

#### 4.3 Alerts
- [ ] Liquidity alert triggered when Yesterday High breached
- [ ] Push notification sent to browser
- [ ] Notification shows correct symbol + level
- [ ] Alert logged in database

#### 4.4 Fallback Mechanism
- [ ] Simulated DB error → uses default symbols
- [ ] No crash, Celery continues running

---

## 🚀 End-to-End Test Scenarios

### Scenario 1: New User Experience

```
1. User signs up
2. Default watchlist created (5 symbols)
3. Dashboard loads with 5 TradingView widgets
4. Live prices visible immediately
✅ Expected: User sees DAX, NASDAQ, DOW, EURUSD, EURGBP
```

### Scenario 2: Customize Watchlist

```
1. User clicks "Edit Watchlist"
2. Modal opens with current 5 symbols
3. User searches "GBPUSD"
4. Clicks to add GBPUSD
5. Clicks "Save Watchlist"
6. Dashboard refreshes with 6 widgets
✅ Expected: GBPUSD widget appears, shows live price
```

### Scenario 3: Alert Notification

```
1. User has EURUSD in watchlist
2. Yesterday High: 1.1500
3. Current price crosses 1.1501
4. Celery detects breach (within 60s)
5. Push notification sent
✅ Expected: Browser shows "EURUSD crossed Yesterday High (1.1500)"
```

---

## 🔍 Database Verification Queries

### Check Watchlist for User

```sql
SELECT
  uw.position,
  s.symbol,
  s.name,
  s.tv_symbol,
  uw.created_at
FROM user_watchlist uw
JOIN symbols s ON s.id = uw.symbol_id
WHERE uw.user_id = 'YOUR_USER_ID'
ORDER BY uw.position;
```

**Expected Output:**
```
position | symbol  | name                       | tv_symbol   | created_at
---------|---------|----------------------------|-------------|-------------------
1        | ^GDAXI  | DAX Performance Index      | XETR:DAX    | 2025-11-03 ...
2        | ^NDX    | NASDAQ 100 Index           | NASDAQ:NDX  | 2025-11-03 ...
...
```

### Check Symbol Popularity (For Backend)

```sql
SELECT
  s.symbol,
  COUNT(uw.id) AS user_count
FROM user_watchlist uw
JOIN symbols s ON s.id = uw.symbol_id
GROUP BY s.symbol
ORDER BY user_count DESC
LIMIT 20;
```

**Use Case:** If too many unique symbols, prioritize most popular

---

## 🐛 Known Issues & Workarounds

### Issue 1: TradingView Widget Not Loading

**Symptom:** Widget shows "Loading..." forever

**Causes:**
- Ad blocker blocking `s3.tradingview.com`
- Incorrect `tv_symbol` format
- Internet connection issue

**Debug:**
1. Check browser console for errors
2. Verify `tv_symbol` in database (should be "XETR:DAX", not "^GDAXI")
3. Disable ad blocker
4. Try different browser

### Issue 2: Duplicate Symbols in Watchlist

**Symptom:** Same symbol appears twice

**Cause:** Frontend bug or RLS bypass

**Fix:**
```sql
-- Find duplicates
SELECT user_id, symbol_id, COUNT(*)
FROM user_watchlist
GROUP BY user_id, symbol_id
HAVING COUNT(*) > 1;

-- Delete duplicates (keep lowest ID)
DELETE FROM user_watchlist a
USING user_watchlist b
WHERE a.id > b.id
  AND a.user_id = b.user_id
  AND a.symbol_id = b.symbol_id;
```

### Issue 3: Celery Not Monitoring New Symbols

**Symptom:** Added symbol via frontend, but Celery logs don't show it

**Debug:**
1. Check if symbol in database: `SELECT * FROM user_watchlist WHERE symbol_id = '...'`
2. Check Celery logs: `docker-compose logs -f celery-worker`
3. Restart Celery: `docker-compose restart celery-worker`

**Common Cause:** `symbol.is_active = false`

---

## 📊 Performance Testing

### Load Test: 100 Concurrent Users

**Setup:**
```bash
# Using Apache Bench
ab -n 1000 -c 100 https://tradematrix.netlify.app/dashboard
```

**Expected:**
- Dashboard loads < 2s (95th percentile)
- TradingView widgets load < 1s each
- Database queries < 100ms
- No 500 errors

### Backend Load: 100 Unique Symbols

**Scenario:** 100 users, each with different 10 symbols = 1,000 unique symbols

**Issue:** Twelvedata limit (55 calls/min)

**Solution:** Implement Top-N prioritization (see 04_BACKEND_UPDATES.md)

---

## ✅ Pre-Deployment Checklist

### Frontend (Netlify)
- [ ] All components in `components/dashboard/` exist
- [ ] No TypeScript errors: `npm run type-check`
- [ ] No ESLint errors: `npm run lint`
- [ ] Build succeeds: `npm run build`
- [ ] Test on localhost:3000

### Database (Supabase)
- [ ] Migration 017 executed
- [ ] RLS policies active: `SELECT * FROM pg_policies WHERE tablename = 'user_watchlist'`
- [ ] Indexes exist: `SELECT * FROM pg_indexes WHERE tablename = 'user_watchlist'`
- [ ] `symbols.tv_symbol` populated

### Backend (Hetzner)
- [ ] `alert_engine.py` updated with `get_all_watched_symbols()`
- [ ] Code deployed to server
- [ ] Celery worker restarted
- [ ] Logs show new symbols

---

## 🎯 Success Criteria

**Feature is complete when:**

1. ✅ User can add/remove up to 10 symbols
2. ✅ Dashboard shows TradingView widgets with live prices
3. ✅ Symbol Picker modal intuitive & bug-free
4. ✅ Backend monitors all unique symbols
5. ✅ Alerts still work (unchanged)
6. ✅ No regressions in existing features
7. ✅ Responsive on all screen sizes
8. ✅ No console errors
9. ✅ Documentation complete
10. ✅ Tests passing

---

**Next:** [IMPLEMENTATION_CHECKLIST.md](./IMPLEMENTATION_CHECKLIST.md)
