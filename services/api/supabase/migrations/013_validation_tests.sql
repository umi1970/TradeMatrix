-- =====================================================================
-- Validation Tests for Migration 013: chart-img.com Integration
-- =====================================================================
-- Run these queries AFTER applying migration 013 to verify success
-- Execute in Supabase SQL Editor or via psql
-- =====================================================================

-- =====================================================================
-- TEST 1: Verify new columns exist and are configured
-- =====================================================================
-- Expected: 5+ rows (DAX, NASDAQ, DOW, EUR/USD, EUR/GBP or GBP/USD)
-- All should have chart_enabled = true and valid chart_img_symbol

SELECT
  symbol,
  name,
  type,
  chart_img_symbol,
  chart_enabled,
  chart_config->'default_timeframe' as default_timeframe,
  chart_config->'indicators' as indicators
FROM public.symbols
WHERE chart_enabled = true
ORDER BY type, symbol;

-- Expected Result:
-- ┌─────────┬──────────────────────┬───────┬──────────────────┬───────────────┬──────────────────┐
-- │ symbol  │ name                 │ type  │ chart_img_symbol │ chart_enabled │ default_tf       │
-- ├─────────┼──────────────────────┼───────┼──────────────────┼───────────────┼──────────────────┤
-- │ EURUSD  │ EUR/USD              │ forex │ OANDA:EURUSD     │ true          │ "4h"             │
-- │ EURGBP  │ EUR/GBP              │ forex │ OANDA:EURGBP     │ true          │ "4h"             │
-- │ ^GDAXI  │ DAX 40               │ index │ XETR:DAX         │ true          │ "4h"             │
-- │ ^NDX    │ NASDAQ 100           │ index │ NASDAQ:NDX       │ true          │ "4h"             │
-- │ ^DJI    │ Dow Jones Industrial │ index │ DJCFD:DJI        │ true          │ "4h"             │
-- └─────────┴──────────────────────┴───────┴──────────────────┴───────────────┴──────────────────┘


-- =====================================================================
-- TEST 2: Verify chart_snapshots table structure
-- =====================================================================
-- Expected: Table exists with correct columns and constraints

SELECT
  column_name,
  data_type,
  is_nullable,
  column_default
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'chart_snapshots'
ORDER BY ordinal_position;

-- Expected Result: 9 columns (id, symbol_id, timeframe, chart_url, trigger_type, generated_by, generated_at, expires_at, metadata, created_at)


-- =====================================================================
-- TEST 3: Verify RLS policies are active
-- =====================================================================
-- Expected: 4 policies (view, create, delete own, service role manage)

SELECT
  schemaname,
  tablename,
  policyname,
  permissive,
  roles,
  cmd,
  qual
FROM pg_policies
WHERE tablename = 'chart_snapshots'
ORDER BY policyname;

-- Expected Result: 4 policies
-- 1. "Anyone can view chart_snapshots" (SELECT)
-- 2. "Authenticated users can create chart_snapshots" (INSERT)
-- 3. "Users can delete own chart_snapshots" (DELETE)
-- 4. "Service role can manage all chart_snapshots" (ALL)


-- =====================================================================
-- TEST 4: Verify indexes are created
-- =====================================================================
-- Expected: 6 indexes (PK + 5 performance indexes)

SELECT
  schemaname,
  tablename,
  indexname,
  indexdef
FROM pg_indexes
WHERE tablename IN ('chart_snapshots', 'symbols')
  AND (indexname LIKE '%chart%' OR indexname LIKE 'chart_snapshots%')
ORDER BY tablename, indexname;

-- Expected Indexes:
-- - chart_snapshots_pkey (PRIMARY KEY)
-- - idx_chart_snapshots_symbol_id
-- - idx_chart_snapshots_generated_at
-- - idx_chart_snapshots_timeframe
-- - idx_chart_snapshots_trigger_type
-- - idx_chart_snapshots_symbol_timeframe
-- - idx_symbols_chart_enabled


-- =====================================================================
-- TEST 5: Insert test chart snapshot
-- =====================================================================
-- Note: Run this as an authenticated user (not service role)
-- This tests INSERT RLS policy

INSERT INTO public.chart_snapshots (
  symbol_id,
  timeframe,
  chart_url,
  trigger_type,
  generated_by,
  expires_at,
  metadata
) VALUES (
  (SELECT id FROM public.symbols WHERE symbol = '^GDAXI' LIMIT 1),
  '4h',
  'https://chart-img.com/test/dax-4h-20251102-120000.png',
  'manual',
  auth.uid(),  -- Current authenticated user
  NOW() + INTERVAL '60 days',
  '{"test": true, "description": "Migration validation test"}'::jsonb
)
RETURNING id, symbol_id, timeframe, chart_url, trigger_type, generated_at;

-- Expected: 1 row inserted successfully with auto-generated ID


-- =====================================================================
-- TEST 6: Query test snapshot (verify SELECT works)
-- =====================================================================
-- This tests SELECT RLS policy (anyone can view)

SELECT
  cs.id,
  s.symbol,
  s.name,
  s.chart_img_symbol,
  cs.timeframe,
  cs.chart_url,
  cs.trigger_type,
  cs.generated_at,
  cs.expires_at,
  cs.metadata
FROM public.chart_snapshots cs
JOIN public.symbols s ON cs.symbol_id = s.id
ORDER BY cs.generated_at DESC
LIMIT 5;

-- Expected: At least 1 row (the test snapshot from Test 5)


-- =====================================================================
-- TEST 7: Test utility function - get_latest_chart_snapshot
-- =====================================================================
-- Expected: Returns the most recent snapshot for DAX 4h

SELECT * FROM get_latest_chart_snapshot(
  (SELECT id FROM public.symbols WHERE symbol = '^GDAXI' LIMIT 1),
  '4h'
);

-- Expected: 1 row with the test snapshot


-- =====================================================================
-- TEST 8: Test utility function - cleanup_expired_chart_snapshots
-- =====================================================================
-- Expected: Returns 0 (no expired snapshots yet, since we set 60 days expiry)

SELECT cleanup_expired_chart_snapshots() as deleted_count;

-- Expected Result: deleted_count = 0


-- =====================================================================
-- TEST 9: Test DELETE RLS policy (users can delete own snapshots)
-- =====================================================================
-- Note: Run as the same authenticated user who created the test snapshot

DELETE FROM public.chart_snapshots
WHERE metadata->>'test' = 'true'
  AND generated_by = auth.uid()
RETURNING id, symbol_id, timeframe, trigger_type;

-- Expected: 1 row deleted successfully


-- =====================================================================
-- TEST 10: Verify chart_config JSONB structure
-- =====================================================================
-- Expected: All enabled symbols have valid JSON config

SELECT
  symbol,
  chart_config ? 'timeframes' as has_timeframes,
  chart_config ? 'indicators' as has_indicators,
  chart_config ? 'default_timeframe' as has_default_tf,
  jsonb_array_length(chart_config->'timeframes') as tf_count,
  jsonb_array_length(chart_config->'indicators') as indicator_count
FROM public.symbols
WHERE chart_enabled = true;

-- Expected: All rows should have has_* = true, tf_count >= 3, indicator_count >= 3


-- =====================================================================
-- TEST 11: Test multi-timeframe snapshots
-- =====================================================================
-- Create snapshots for different timeframes to test query performance

DO $$
DECLARE
  dax_id UUID;
  tf TEXT;
BEGIN
  -- Get DAX symbol ID
  SELECT id INTO dax_id FROM public.symbols WHERE symbol = '^GDAXI' LIMIT 1;

  -- Insert snapshots for 1h, 4h, 1d
  FOREACH tf IN ARRAY ARRAY['1h', '4h', '1d']
  LOOP
    INSERT INTO public.chart_snapshots (
      symbol_id,
      timeframe,
      chart_url,
      trigger_type,
      generated_by,
      expires_at,
      metadata
    ) VALUES (
      dax_id,
      tf,
      format('https://chart-img.com/test/dax-%s-%s.png', tf, to_char(NOW(), 'YYYYMMDDHH24MISS')),
      'manual',
      auth.uid(),
      NOW() + INTERVAL '60 days',
      jsonb_build_object('test', true, 'timeframe', tf, 'created_for', 'validation')
    );
  END LOOP;
END $$;

-- Expected: 3 rows inserted


-- =====================================================================
-- TEST 12: Query snapshots by timeframe (test index performance)
-- =====================================================================
-- Expected: Fast query using idx_chart_snapshots_symbol_timeframe index

EXPLAIN ANALYZE
SELECT
  cs.id,
  s.symbol,
  cs.timeframe,
  cs.chart_url,
  cs.generated_at
FROM public.chart_snapshots cs
JOIN public.symbols s ON cs.symbol_id = s.id
WHERE cs.symbol_id = (SELECT id FROM public.symbols WHERE symbol = '^GDAXI' LIMIT 1)
  AND cs.timeframe = '4h'
ORDER BY cs.generated_at DESC
LIMIT 1;

-- Expected: Query plan should show Index Scan using idx_chart_snapshots_symbol_timeframe


-- =====================================================================
-- TEST 13: Cleanup all test data
-- =====================================================================
-- Remove all test snapshots created during validation

DELETE FROM public.chart_snapshots
WHERE metadata->>'test' = 'true'
  OR metadata->>'created_for' = 'validation';

-- Expected: 4 rows deleted (1 from Test 5 + 3 from Test 11)


-- =====================================================================
-- VALIDATION SUMMARY
-- =====================================================================
-- If all tests pass:
-- ✅ Migration 013 successfully applied
-- ✅ chart_img_symbol, chart_enabled, chart_config columns exist
-- ✅ 5 symbols configured with TradingView mappings
-- ✅ chart_snapshots table created with correct structure
-- ✅ All RLS policies working correctly
-- ✅ Performance indexes active
-- ✅ Utility functions operational
--
-- Next steps:
-- 1. Implement chart-img.com API integration in FastAPI
-- 2. Create React components for chart display
-- 3. Add chart snapshot management UI
-- 4. Implement automatic chart generation on alerts
-- =====================================================================
