# Migration 018 Execution Instructions

**Created:** 2025-11-03
**Status:** ⏸️ READY TO EXECUTE
**Priority:** 🔥 BLOCKER - Frontend needs this to work!

---

## ⚠️ IMPORTANT: Execute This Before Testing!

The TradingView Watchlist feature is **fully implemented** but won't work until this migration is executed.

**Why?** The frontend needs the `tv_symbol` column to render TradingView widgets.

---

## 📋 Quick Instructions

### Step 1: Open Supabase SQL Editor

1. Go to https://supabase.com/dashboard
2. Select your TradeMatrix project
3. Click **SQL Editor** in left sidebar
4. Click **New Query**

### Step 2: Execute Migration 018

**File:** `/services/api/supabase/migrations/018_add_tv_symbol_and_default_watchlist.sql`

**Option A - Copy/Paste:**
```bash
# In your terminal:
cat services/api/supabase/migrations/018_add_tv_symbol_and_default_watchlist.sql
```
Then paste the entire content into Supabase SQL Editor and click **Run**.

**Option B - Manual:**
Copy the content from the file manually and paste into SQL Editor.

### Step 3: Verify Success

You should see these success messages:
```
✅ Column tv_symbol added successfully
✅ 6 symbols updated with tv_symbol values
✅ Function create_default_watchlist created successfully
🚀 Migration 018 completed successfully!
```

If you see any errors, check:
- Migration 017 was executed (user_watchlist table exists)
- Symbols table exists and has at least 6 rows

---

## 🔍 What This Migration Does

### 1. Adds `tv_symbol` Column
Adds a new column to the `symbols` table to store TradingView-compatible symbol format.

**Before:**
```
symbols table:
- id, symbol, name, type, is_active
```

**After:**
```
symbols table:
- id, symbol, name, type, is_active, tv_symbol
```

### 2. Updates Existing Symbols

Maps internal symbols to TradingView format:

| Internal Symbol | TradingView Format | Type |
|----------------|-------------------|------|
| `^GDAXI` | `XETR:DAX` | index |
| `^NDX` | `NASDAQ:NDX` | index |
| `^DJI` | `DJ:DJI` | index |
| `EURUSD` | `FX:EURUSD` | forex |
| `EURGBP` | `FX:EURGBP` | forex |
| `GBPUSD` | `FX:GBPUSD` | forex |

### 3. Creates Default Watchlist Function

Creates a PostgreSQL function `create_default_watchlist(p_user_id)` that:
- Initializes new users with 5 default symbols (DAX, NASDAQ, DOW, EURUSD, EURGBP)
- Can be called manually or via trigger

**Usage:**
```sql
SELECT create_default_watchlist('user-uuid-here');
```

---

## 🧪 Testing After Migration

### 1. Verify tv_symbol Column Exists

```sql
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'symbols'
  AND column_name = 'tv_symbol';
```

**Expected:** 1 row returned (`tv_symbol | text`)

### 2. Check Symbol Updates

```sql
SELECT symbol, name, tv_symbol
FROM public.symbols
WHERE tv_symbol IS NOT NULL
ORDER BY symbol;
```

**Expected:** At least 6 rows with tv_symbol values

### 3. Test Default Watchlist Function

```sql
-- Create test user watchlist
SELECT create_default_watchlist(auth.uid());

-- Verify watchlist created
SELECT uw.position, s.symbol, s.tv_symbol
FROM user_watchlist uw
JOIN symbols s ON s.id = uw.symbol_id
WHERE uw.user_id = auth.uid()
ORDER BY uw.position;
```

**Expected:** 5 rows (positions 1-5 with symbols)

---

## 🚀 After Migration: Next Steps

1. ✅ Migration executed successfully
2. ✅ Frontend components already implemented
3. ✅ Backend updates already implemented
4. ⏭️ **Run local tests** (`npm run dev`)
5. ⏭️ **Deploy to Netlify** (automatic on git push)
6. ⏭️ **Deploy to Hetzner** (restart Celery worker)

---

## 🐛 Troubleshooting

### Error: "relation 'user_watchlist' does not exist"
**Solution:** Execute Migration 017 first (creates user_watchlist table)

### Error: "column 'tv_symbol' already exists"
**Solution:** Migration already ran, skip to testing

### Error: "function 'create_default_watchlist' already exists"
**Solution:** Drop function first:
```sql
DROP FUNCTION IF EXISTS public.create_default_watchlist(UUID);
```
Then re-run migration.

### Error: "no rows returned" when updating symbols
**Solution:** Check if symbols exist:
```sql
SELECT * FROM public.symbols WHERE symbol IN ('^GDAXI', '^NDX', '^DJI', 'EURUSD', 'EURGBP', 'GBPUSD');
```

If no rows, you need to populate symbols table first.

---

## 📝 Rollback Instructions (If Needed)

**⚠️ Use only if migration causes issues!**

```sql
-- 1. Drop function
DROP FUNCTION IF EXISTS public.create_default_watchlist(UUID);

-- 2. Remove tv_symbol column
ALTER TABLE public.symbols DROP COLUMN IF EXISTS tv_symbol;

-- Verify rollback
SELECT column_name FROM information_schema.columns
WHERE table_schema = 'public' AND table_name = 'symbols';
-- tv_symbol should NOT be in list
```

---

## ✅ Checklist

After executing this migration, mark these as done:

- [ ] Opened Supabase SQL Editor
- [ ] Executed migration 018
- [ ] Verified success messages (✅ symbols updated, ✅ function created)
- [ ] Tested: tv_symbol column exists
- [ ] Tested: Symbols have tv_symbol values
- [ ] Tested: create_default_watchlist() works
- [ ] Ready to test frontend (npm run dev)

---

**Status:** 🟡 Waiting for user to execute in Supabase SQL Editor

Once executed, the entire TradingView Watchlist feature will be ready to test!
