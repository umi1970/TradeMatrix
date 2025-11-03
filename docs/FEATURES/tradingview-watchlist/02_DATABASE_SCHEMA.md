# Database Schema: User Watchlist

**Last Updated:** 2025-11-03
**Migration:** 017 (✅ **ALREADY EXECUTED**)

---

## ⚠️ IMPORTANT: Migration Already Run!

**Migration 017 was executed in previous session.**

No need to run SQL again! Schema is already in production.

---

## 📊 Table: `user_watchlist`

### Purpose
Stores user-customized symbol selections for dashboard display (max 10 per user).

### Schema

```sql
CREATE TABLE IF NOT EXISTS public.user_watchlist (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  symbol_id UUID NOT NULL REFERENCES public.symbols(id) ON DELETE CASCADE,
  position INT NOT NULL CHECK (position >= 1 AND position <= 10),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),

  -- Constraints
  UNIQUE(user_id, symbol_id),    -- User can't add same symbol twice
  UNIQUE(user_id, position)      -- Each position used only once
);
```

### Columns

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | Unique watchlist entry ID |
| `user_id` | UUID | FK → auth.users, NOT NULL | Owner of watchlist |
| `symbol_id` | UUID | FK → symbols, NOT NULL | Symbol to watch |
| `position` | INT | CHECK (1-10), NOT NULL | Display order (1 = first) |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | When added |
| `updated_at` | TIMESTAMPTZ | DEFAULT NOW() | Last modified |

### Constraints

1. **UNIQUE(user_id, symbol_id)**
   - Prevents duplicate symbols in same user's watchlist
   - Error: `duplicate key value violates unique constraint "user_watchlist_user_id_symbol_id_key"`

2. **UNIQUE(user_id, position)**
   - Ensures each position (1-10) used only once
   - Error: `duplicate key value violates unique constraint "user_watchlist_user_id_position_key"`

3. **CHECK (position >= 1 AND position <= 10)**
   - Enforces 10-symbol limit
   - Error: `new row for relation "user_watchlist" violates check constraint "user_watchlist_position_check"`

---

## 🔐 Row Level Security (RLS)

### Policy: "Users manage own watchlist"

```sql
ALTER TABLE public.user_watchlist ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users manage own watchlist"
  ON public.user_watchlist FOR ALL
  USING (auth.uid() = user_id);
```

**Effect:**
- Users can SELECT/INSERT/UPDATE/DELETE only their own rows
- Other users' watchlists are invisible
- No service_role bypass needed for normal operations

**Testing:**
```sql
-- As User A (logged in via Supabase client)
SELECT * FROM user_watchlist;
-- Returns only User A's symbols

-- Try to insert for User B
INSERT INTO user_watchlist (user_id, symbol_id, position)
VALUES ('user-b-id', 'some-symbol', 1);
-- ERROR: new row violates row-level security policy
```

---

## 📇 Indexes

```sql
CREATE INDEX idx_user_watchlist_user
  ON public.user_watchlist(user_id);

CREATE INDEX idx_user_watchlist_position
  ON public.user_watchlist(user_id, position);
```

**Performance:**
- **idx_user_watchlist_user**: Fast user-specific queries (`WHERE user_id = ?`)
- **idx_user_watchlist_position**: Ordered retrieval (`ORDER BY position`)

---

## 🆕 Update: `symbols` Table

### New Column: `tv_symbol`

**Purpose:** Store TradingView-compatible symbol format

```sql
ALTER TABLE public.symbols
ADD COLUMN tv_symbol TEXT;

COMMENT ON COLUMN public.symbols.tv_symbol IS 'TradingView widget symbol format (e.g., "XETR:DAX", "FX:EURUSD")';
```

### Symbol Mapping

| symbol | name | tv_symbol | type |
|--------|------|-----------|------|
| `^GDAXI` | DAX Performance Index | `XETR:DAX` | index |
| `^NDX` | NASDAQ 100 Index | `NASDAQ:NDX` | index |
| `^DJI` | Dow Jones Industrial Average | `DJ:DJI` | index |
| `EURUSD` | EUR/USD | `FX:EURUSD` | forex |
| `EURGBP` | EUR/GBP | `FX:EURGBP` | forex |
| `GBPUSD` | GBP/USD | `FX:GBPUSD` | forex |

**Update existing symbols:**
```sql
UPDATE public.symbols SET tv_symbol = 'XETR:DAX' WHERE symbol = '^GDAXI';
UPDATE public.symbols SET tv_symbol = 'NASDAQ:NDX' WHERE symbol = '^NDX';
UPDATE public.symbols SET tv_symbol = 'DJ:DJI' WHERE symbol = '^DJI';
UPDATE public.symbols SET tv_symbol = 'FX:EURUSD' WHERE symbol = 'EURUSD';
UPDATE public.symbols SET tv_symbol = 'FX:EURGBP' WHERE symbol = 'EURGBP';
UPDATE public.symbols SET tv_symbol = 'FX:GBPUSD' WHERE symbol = 'GBPUSD';
```

---

## 🎯 Default Watchlist

### Function: `create_default_watchlist()`

**Purpose:** Initialize new users with 5 default symbols

```sql
CREATE OR REPLACE FUNCTION public.create_default_watchlist(p_user_id UUID)
RETURNS VOID AS $$
DECLARE
  v_symbols UUID[];
BEGIN
  -- Get top 5 most popular symbols
  SELECT ARRAY_AGG(id ORDER BY symbol)
  INTO v_symbols
  FROM public.symbols
  WHERE symbol IN ('^GDAXI', '^NDX', '^DJI', 'EURUSD', 'EURGBP')
  LIMIT 5;

  -- Insert default watchlist
  INSERT INTO public.user_watchlist (user_id, symbol_id, position)
  SELECT p_user_id, symbol_id, ROW_NUMBER() OVER ()
  FROM UNNEST(v_symbols) AS symbol_id
  ON CONFLICT (user_id, symbol_id) DO NOTHING;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION public.create_default_watchlist IS 'Initialize new user with 5 default symbols (DAX, NASDAQ, DOW, EURUSD, EURGBP)';
```

**Trigger:** Call on user signup

```sql
-- In Supabase Edge Function or Next.js Server Action
await supabase.rpc('create_default_watchlist', {
  p_user_id: userId
});
```

---

## 🔍 Common Queries

### 1. Get User's Watchlist (Ordered)

```sql
SELECT
  uw.id,
  uw.position,
  s.symbol,
  s.name,
  s.tv_symbol,
  s.type,
  uw.created_at
FROM user_watchlist uw
JOIN symbols s ON s.id = uw.symbol_id
WHERE uw.user_id = auth.uid()
ORDER BY uw.position ASC;
```

**TypeScript (Supabase):**
```typescript
const { data: watchlist } = await supabase
  .from('user_watchlist')
  .select('*, symbols(*)')
  .eq('user_id', session.user.id)
  .order('position', { ascending: true });
```

### 2. Add Symbol to Watchlist

```sql
INSERT INTO user_watchlist (user_id, symbol_id, position)
VALUES (auth.uid(), '...symbol-uuid...', 3)
ON CONFLICT (user_id, position) DO UPDATE
SET symbol_id = EXCLUDED.symbol_id,
    updated_at = NOW();
```

**TypeScript:**
```typescript
const { error } = await supabase
  .from('user_watchlist')
  .insert({
    user_id: session.user.id,
    symbol_id: symbolId,
    position: 3
  });
```

### 3. Remove Symbol

```sql
DELETE FROM user_watchlist
WHERE user_id = auth.uid()
  AND symbol_id = '...symbol-uuid...';
```

**TypeScript:**
```typescript
const { error } = await supabase
  .from('user_watchlist')
  .delete()
  .eq('user_id', session.user.id)
  .eq('symbol_id', symbolId);
```

### 4. Reorder Symbols (Swap Positions)

```sql
-- Swap position 3 and 5
UPDATE user_watchlist SET position = CASE
  WHEN position = 3 THEN 5
  WHEN position = 5 THEN 3
  ELSE position
END
WHERE user_id = auth.uid()
  AND position IN (3, 5);
```

### 5. Get All Unique Symbols (For Alerts)

```sql
SELECT DISTINCT s.*
FROM user_watchlist uw
JOIN symbols s ON s.id = uw.symbol_id
WHERE s.is_active = true;
```

**Python (Hetzner Backend):**
```python
result = supabase.table('user_watchlist')\
    .select('symbols(*)')\
    .execute()

unique_symbols = list(set([r['symbols']['symbol'] for r in result.data]))
```

---

## 📊 Storage Estimates

### Assumptions
- **Users:** 1,000
- **Symbols per user:** 10 (max)
- **Row size:** ~120 bytes (UUID + UUID + INT + timestamps)

### Calculation
```
1,000 users × 10 symbols × 120 bytes = 1.2 MB
```

**Supabase Free Tier:** 500 MB database → 1.2 MB is negligible ✅

---

## 🧪 Testing Queries

### Test Constraints

```sql
-- Test 1: Duplicate symbol (should fail)
INSERT INTO user_watchlist (user_id, symbol_id, position)
VALUES ('user-1', 'symbol-a', 1);

INSERT INTO user_watchlist (user_id, symbol_id, position)
VALUES ('user-1', 'symbol-a', 2);
-- ERROR: duplicate key value violates unique constraint

-- Test 2: Invalid position (should fail)
INSERT INTO user_watchlist (user_id, symbol_id, position)
VALUES ('user-1', 'symbol-b', 11);
-- ERROR: new row violates check constraint

-- Test 3: Position conflict (should fail)
INSERT INTO user_watchlist (user_id, symbol_id, position)
VALUES ('user-1', 'symbol-b', 1);

INSERT INTO user_watchlist (user_id, symbol_id, position)
VALUES ('user-1', 'symbol-c', 1);
-- ERROR: duplicate key value violates unique constraint
```

### Test RLS

```sql
-- As User A
SET SESSION "request.jwt.claim.sub" = 'user-a-uuid';

SELECT * FROM user_watchlist;
-- Returns only User A's rows

-- Try to see User B's watchlist
SELECT * FROM user_watchlist WHERE user_id = 'user-b-uuid';
-- Returns 0 rows (RLS blocks)
```

---

## 🚀 Deployment Checklist

- [x] Migration 017 executed in Supabase SQL Editor
- [x] RLS policies enabled
- [x] Indexes created
- [ ] `symbols.tv_symbol` column added (migration 018)
- [ ] Existing symbols updated with tv_symbol values
- [ ] Default watchlist function deployed
- [ ] Frontend updated to call create_default_watchlist on signup

---

**Next:** [03_FRONTEND_IMPLEMENTATION.md](./03_FRONTEND_IMPLEMENTATION.md)
