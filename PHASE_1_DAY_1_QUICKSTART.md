# Phase 1 Day 1: Database Setup - Quick Execution Guide

**Time Required:** 10-15 minutes
**Status:** READY TO EXECUTE
**Last Updated:** 2025-10-31

---

## What You're About to Do

Deploy the EOD Data Layer to your Supabase database:
- 4 tables (symbols, eod_data, eod_levels, eod_fetch_log)
- 7 utility functions
- 1 quality metrics view
- 5 default market symbols
- Complete data security (RLS)

---

## Quick 5-Step Execution

### Step 1: Get Credentials (2 min)

1. Open https://supabase.com in browser
2. Log in and select "tradematrix-dev" project
3. Go to **Settings → API** (left sidebar)
4. Copy these 3 values:
   - Project URL → `SUPABASE_URL`
   - anon public → `SUPABASE_KEY`
   - service_role secret → `SUPABASE_SERVICE_KEY`

**Example values:**
```
SUPABASE_URL=https://abcdef123456.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSJ9.Abc123...
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJvbGUiOiJzZXJ2aWNlX3JvbGUifQ.Xyz789...
```

### Step 2: Create .env Files (3 min)

**File 1:** `apps/web/.env.local`
```bash
# Copy from Step 1
NEXT_PUBLIC_SUPABASE_URL=https://abcdef123456.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGc...
```

**File 2:** `services/api/.env`
```bash
# Copy from Step 1
SUPABASE_URL=https://abcdef123456.supabase.co
SUPABASE_KEY=eyJhbGc...
SUPABASE_SERVICE_KEY=eyJhbGc...
```

### Step 3: Run Migration 010 (5 min)

1. Go to Supabase SQL Editor → **"New query"**
2. Open file: `services/api/supabase/migrations/010_eod_data_layer.sql`
3. Copy entire contents
4. Paste into SQL Editor
5. Click **"Run"** button
6. Wait for completion
7. Check output shows ✓ SETUP COMPLETE!

**Expected Output:**
```
table_name    column_count
eod_data           12
eod_fetch_log      11
eod_levels         15
symbols            13

symbol    name                  type      is_active
^DJI      Dow Jones            index     true
^GDAXI    DAX 40               index     true
^NDX      NASDAQ 100           index     true
EURUSD    EUR/USD              forex     true
GBPUSD    GBP/USD              forex     true
```

### Step 4: Run Migration 011 (3 min)

1. Click **"New query"** again
2. Open file: `services/api/supabase/migrations/011_ utility_functions_fix.sql`
3. Copy entire contents
4. Paste into SQL Editor
5. Click **"Run"** button
6. Check for verification messages

**Expected Output:**
```
NOTICE: Testing utility functions...
NOTICE: ✓ get_active_symbols() - Working
NOTICE: ✓ get_symbol_by_name() - Working
NOTICE: ✓ get_symbol_id() - Working
All utility functions created successfully!
```

### Step 5: Quick Verification (2 min)

Run these 3 test queries in SQL Editor:

**Test 1: Check Tables Exist**
```sql
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN ('symbols', 'eod_data', 'eod_levels', 'eod_fetch_log')
ORDER BY table_name;
```
Expected: 4 rows

**Test 2: Check Symbols**
```sql
SELECT symbol, name, type, is_active FROM symbols ORDER BY symbol;
```
Expected: 5 rows (^DJI, ^GDAXI, ^NDX, EURUSD, GBPUSD)

**Test 3: Test Function**
```sql
SELECT * FROM get_active_symbols();
```
Expected: 5 rows

---

## Summary: What Was Created

### Tables (4 total)

| Table | Purpose | Records |
|-------|---------|---------|
| **symbols** | Market reference | 5 |
| **eod_data** | OHLCV history | 0 (empty, will fill) |
| **eod_levels** | Derived metrics | 0 (empty, will fill) |
| **eod_fetch_log** | Audit log | 0 (empty, will fill) |

### Functions (7 total)

| Function | Purpose | Used By |
|----------|---------|---------|
| **get_latest_eod** | Current prices | Dashboard |
| **get_yesterday_levels** | Yesterday's support/resistance | MorningPlanner |
| **calculate_atr** | Volatility metrics | RiskManager |
| **get_active_symbols** | Symbols to fetch | Data Fetcher |
| **get_symbol_by_name** | Symbol details | Data Fetcher |
| **get_symbol_id** | Symbol UUID | Internal |
| **get_all_symbols** | Full catalog | Debugging |

### Default Symbols (5 total)

```
^GDAXI   DAX 40              (German Stock Index)
^NDX     NASDAQ 100          (US Tech Index)
^DJI     Dow Jones           (US Blue Chip Index)
EURUSD   EUR/USD             (Forex: Euro to Dollar)
GBPUSD   GBP/USD             (Forex: Pound to Dollar)
```

### Security

- ✓ RLS enabled on all tables
- ✓ All authenticated users can read data
- ✓ Only service_role can write data
- ✓ No user can tamper with trading data

---

## Troubleshooting

### "Syntax Error" in SQL
**Fix:** Make sure you copied the entire file, including all lines at the end

### "Table already exists"
**Fix:** This is OK, migrations are idempotent (safe to re-run)

### "Service key is blank"
**Fix:** You copied the anon key instead of service_role key. Get the correct one from Settings > API

### "Foreign key constraint failed"
**Fix:** Make sure migration 010 ran before 011

### "No output or errors" after Run
**Fix:** The query ran successfully but produced no output. This is normal for CREATE statements. Scroll down to see verification results.

---

## Files Used

| File | Location | Size | Type |
|------|----------|------|------|
| Migration 010 | `services/api/supabase/migrations/010_eod_data_layer.sql` | 15 KB | SQL |
| Migration 011 | `services/api/supabase/migrations/011_ utility_functions_fix.sql` | 5 KB | SQL |
| .env template | `apps/web/.env.example` | 1 KB | Config |

---

## What Happens Next?

After this setup:

### Next: Phase 1 Day 2-3
- Create Python data fetcher (`services/agents/src/eod_data_fetcher.py`)
- Implement Stooq API integration
- Fetch first data point
- Test full pipeline

### Then: Phase 2-3
- AI agents for pattern recognition
- Trading signal generation
- Risk management calculations
- Dashboard visualization

### Finally: Phase 4-5
- SaaS features (Stripe billing)
- Multi-user support
- Publishing & notifications

---

## Success Criteria

After completing all 5 steps, verify:

- [ ] Migration 010 completed without errors
- [ ] Migration 011 completed without errors
- [ ] All 4 tables exist
- [ ] 5 symbols are in database
- [ ] All 7 functions are callable
- [ ] RLS is enabled
- [ ] Test queries return expected results

---

## Questions?

For more details, see:
1. **PHASE_1_DAY_1_REPORT.md** - Complete documentation
2. **PHASE_1_DAY_1_TECHNICAL_ANALYSIS.md** - Deep dive analysis
3. **services/api/supabase/README.md** - Supabase setup guide
4. **QUICKSTART.md** - General project setup

---

**Time to Complete:** 10-15 minutes
**Difficulty:** Beginner (copy-paste SQL)
**Risk Level:** Very Low (Supabase can rollback)

**Status:** READY FOR EXECUTION ✓
