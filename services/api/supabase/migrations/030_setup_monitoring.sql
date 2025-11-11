-- =====================================================================
-- Migration: 030_setup_monitoring.sql
-- Description: Add Setup Monitoring fields for TradingView integration
-- Created: 2025-11-11
-- Feature: TradingView Setup Automation
-- =====================================================================
--
-- Purpose:
--   Enable real-time monitoring of trading setups created from TradingView alerts.
--   Track Entry/SL/TP hits and calculate outcomes (win/loss/invalidated/missed).
--
-- Related Documentation:
--   docs/FEATURES/tradingview-setup-automation/README.md
--
-- =====================================================================

BEGIN;

-- =====================================================================
-- 1. EXTEND SETUPS TABLE - MONITORING FIELDS
-- =====================================================================

-- Setup Lifecycle Tracking
ALTER TABLE setups ADD COLUMN IF NOT EXISTS entry_hit BOOLEAN DEFAULT false;
ALTER TABLE setups ADD COLUMN IF NOT EXISTS entry_hit_at TIMESTAMPTZ;
ALTER TABLE setups ADD COLUMN IF NOT EXISTS sl_hit_at TIMESTAMPTZ;
ALTER TABLE setups ADD COLUMN IF NOT EXISTS tp_hit_at TIMESTAMPTZ;

-- Outcome Tracking
ALTER TABLE setups ADD COLUMN IF NOT EXISTS outcome TEXT;
ALTER TABLE setups ADD CONSTRAINT setups_outcome_check
  CHECK (outcome IN ('win', 'loss', 'invalidated', 'missed'));

-- P&L Calculation
ALTER TABLE setups ADD COLUMN IF NOT EXISTS pnl_percent NUMERIC(6,2);

-- Price Monitoring
ALTER TABLE setups ADD COLUMN IF NOT EXISTS last_price NUMERIC;
ALTER TABLE setups ADD COLUMN IF NOT EXISTS last_checked_at TIMESTAMPTZ;

-- Pine Script Integration
ALTER TABLE setups ADD COLUMN IF NOT EXISTS pine_script TEXT;
ALTER TABLE setups ADD COLUMN IF NOT EXISTS pine_script_active BOOLEAN DEFAULT false;

-- =====================================================================
-- 2. EXTEND STATUS ENUM
-- =====================================================================

-- Drop existing constraint
ALTER TABLE setups DROP CONSTRAINT IF EXISTS setups_status_check;

-- Add new constraint with extended status values
ALTER TABLE setups ADD CONSTRAINT setups_status_check
  CHECK (status IN (
    'pending',      -- Setup created, waiting for entry
    'active',       -- Setup active (generic)
    'invalid',      -- Setup invalidated
    'filled',       -- Order filled (generic)
    'cancelled',    -- Setup cancelled by user
    'entry_hit',    -- Entry price hit, position open
    'sl_hit',       -- Stop loss hit, position closed
    'tp_hit',       -- Take profit hit, position closed
    'expired'       -- Setup expired (time-based)
  ));

-- =====================================================================
-- 3. CREATE INDEXES FOR PERFORMANCE
-- =====================================================================

-- Index for finding setups with Entry hit but not closed
CREATE INDEX IF NOT EXISTS idx_setups_entry_hit_pending
  ON setups(entry_hit, status)
  WHERE entry_hit = true AND status = 'entry_hit';

-- Index for finding completed setups (for analytics)
CREATE INDEX IF NOT EXISTS idx_setups_outcome
  ON setups(outcome)
  WHERE outcome IS NOT NULL;

-- Index for monitoring active setups
CREATE INDEX IF NOT EXISTS idx_setups_monitoring_active
  ON setups(pine_script_active, status)
  WHERE pine_script_active = true AND status IN ('pending', 'entry_hit');

-- Index for P&L queries
CREATE INDEX IF NOT EXISTS idx_setups_pnl
  ON setups(pnl_percent)
  WHERE pnl_percent IS NOT NULL;

-- =====================================================================
-- 4. ADD DOCUMENTATION COMMENTS
-- =====================================================================

COMMENT ON COLUMN setups.entry_hit IS 'TRUE if entry price was hit and position opened';
COMMENT ON COLUMN setups.entry_hit_at IS 'Timestamp when entry price was hit';
COMMENT ON COLUMN setups.sl_hit_at IS 'Timestamp when stop loss was hit';
COMMENT ON COLUMN setups.tp_hit_at IS 'Timestamp when take profit was hit';
COMMENT ON COLUMN setups.outcome IS 'Final outcome: win (TP hit after entry), loss (SL hit after entry), invalidated (SL hit before entry), missed (TP hit before entry)';
COMMENT ON COLUMN setups.pnl_percent IS 'Profit/Loss percentage (positive = profit, negative = loss)';
COMMENT ON COLUMN setups.last_price IS 'Last observed price for this setup (from monitoring webhook)';
COMMENT ON COLUMN setups.last_checked_at IS 'Timestamp of last price check';
COMMENT ON COLUMN setups.pine_script IS 'Generated Pine Script code for TradingView monitoring';
COMMENT ON COLUMN setups.pine_script_active IS 'TRUE if Pine Script is active and monitoring this setup';

-- =====================================================================
-- 5. CREATE HELPER VIEWS
-- =====================================================================

-- View: Active Setups (monitoring in progress)
CREATE OR REPLACE VIEW active_setups AS
SELECT
  s.id,
  s.user_id,
  ms.symbol,
  ms.alias AS symbol_name,
  s.side,
  s.entry_price,
  s.stop_loss,
  s.take_profit,
  s.confidence,
  s.status,
  s.entry_hit,
  s.pine_script_active,
  s.last_price,
  s.last_checked_at,
  s.created_at
FROM setups s
JOIN market_symbols ms ON s.symbol_id = ms.id
WHERE s.status IN ('pending', 'entry_hit')
  AND s.pine_script_active = true
ORDER BY s.created_at DESC;

COMMENT ON VIEW active_setups IS 'Setups currently being monitored (pending or entry hit)';

-- View: Completed Setups (with outcomes)
CREATE OR REPLACE VIEW completed_setups AS
SELECT
  s.id,
  s.user_id,
  ms.symbol,
  ms.alias AS symbol_name,
  s.side,
  s.entry_price,
  s.stop_loss,
  s.take_profit,
  s.confidence,
  s.status,
  s.outcome,
  s.pnl_percent,
  s.entry_hit_at,
  s.sl_hit_at,
  s.tp_hit_at,
  s.created_at,
  -- Calculate duration (entry to close)
  CASE
    WHEN s.tp_hit_at IS NOT NULL AND s.entry_hit_at IS NOT NULL
      THEN EXTRACT(EPOCH FROM (s.tp_hit_at - s.entry_hit_at)) / 3600.0
    WHEN s.sl_hit_at IS NOT NULL AND s.entry_hit_at IS NOT NULL
      THEN EXTRACT(EPOCH FROM (s.sl_hit_at - s.entry_hit_at)) / 3600.0
    ELSE NULL
  END AS duration_hours
FROM setups s
JOIN market_symbols ms ON s.symbol_id = ms.id
WHERE s.outcome IS NOT NULL
ORDER BY s.created_at DESC;

COMMENT ON VIEW completed_setups IS 'Setups with final outcomes (win/loss/invalidated/missed) and P&L';

-- =====================================================================
-- 6. CREATE HELPER FUNCTIONS
-- =====================================================================

-- Function: Calculate P&L percentage
CREATE OR REPLACE FUNCTION calculate_pnl_percent(
  p_entry_price NUMERIC,
  p_exit_price NUMERIC,
  p_side TEXT
)
RETURNS NUMERIC AS $$
DECLARE
  pnl NUMERIC;
BEGIN
  IF p_side = 'long' THEN
    pnl := ((p_exit_price - p_entry_price) / p_entry_price) * 100;
  ELSIF p_side = 'short' THEN
    pnl := ((p_entry_price - p_exit_price) / p_entry_price) * 100;
  ELSE
    RETURN NULL;
  END IF;

  RETURN ROUND(pnl, 2);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

COMMENT ON FUNCTION calculate_pnl_percent IS 'Calculate P&L percentage for a trade (positive = profit, negative = loss)';

-- Function: Get setup statistics for a user
CREATE OR REPLACE FUNCTION get_setup_stats(p_user_id UUID, p_days INTEGER DEFAULT 30)
RETURNS TABLE (
  total_setups BIGINT,
  completed_setups BIGINT,
  wins BIGINT,
  losses BIGINT,
  invalidated BIGINT,
  missed BIGINT,
  win_rate NUMERIC,
  avg_pnl NUMERIC,
  total_pnl NUMERIC
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    COUNT(*)::BIGINT AS total_setups,
    COUNT(*) FILTER (WHERE outcome IS NOT NULL)::BIGINT AS completed_setups,
    COUNT(*) FILTER (WHERE outcome = 'win')::BIGINT AS wins,
    COUNT(*) FILTER (WHERE outcome = 'loss')::BIGINT AS losses,
    COUNT(*) FILTER (WHERE outcome = 'invalidated')::BIGINT AS invalidated,
    COUNT(*) FILTER (WHERE outcome = 'missed')::BIGINT AS missed,
    ROUND(
      (COUNT(*) FILTER (WHERE outcome = 'win')::NUMERIC /
       NULLIF(COUNT(*) FILTER (WHERE outcome IN ('win', 'loss'))::NUMERIC, 0) * 100),
      2
    ) AS win_rate,
    ROUND(AVG(pnl_percent) FILTER (WHERE outcome IN ('win', 'loss')), 2) AS avg_pnl,
    ROUND(SUM(pnl_percent) FILTER (WHERE outcome IN ('win', 'loss')), 2) AS total_pnl
  FROM setups
  WHERE user_id = p_user_id
    AND created_at >= NOW() - (p_days || ' days')::INTERVAL;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_setup_stats IS 'Get setup statistics for a user (win rate, avg P&L, etc.) for last N days';

-- Function: Auto-expire old pending setups
CREATE OR REPLACE FUNCTION expire_old_setups()
RETURNS INTEGER AS $$
DECLARE
  expired_count INTEGER;
BEGIN
  -- Mark setups as expired if:
  -- 1. Status is 'pending' or 'entry_hit'
  -- 2. Created more than 7 days ago
  -- 3. No recent price check (last_checked_at > 24h ago OR NULL)
  UPDATE setups
  SET
    status = 'expired',
    pine_script_active = false,
    updated_at = NOW()
  WHERE status IN ('pending', 'entry_hit')
    AND created_at < NOW() - INTERVAL '7 days'
    AND (
      last_checked_at IS NULL OR
      last_checked_at < NOW() - INTERVAL '24 hours'
    );

  GET DIAGNOSTICS expired_count = ROW_COUNT;
  RETURN expired_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION expire_old_setups IS 'Auto-expire old pending setups (>7 days old, no recent monitoring)';

-- =====================================================================
-- 7. VERIFICATION
-- =====================================================================

-- Verify new columns exist
DO $$
DECLARE
  missing_columns TEXT[];
BEGIN
  SELECT ARRAY_AGG(column_name)
  INTO missing_columns
  FROM (
    VALUES
      ('entry_hit'),
      ('entry_hit_at'),
      ('sl_hit_at'),
      ('tp_hit_at'),
      ('outcome'),
      ('pnl_percent'),
      ('last_price'),
      ('last_checked_at'),
      ('pine_script'),
      ('pine_script_active')
  ) AS expected(column_name)
  WHERE NOT EXISTS (
    SELECT 1
    FROM information_schema.columns
    WHERE table_schema = 'public'
      AND table_name = 'setups'
      AND columns.column_name = expected.column_name
  );

  IF missing_columns IS NOT NULL THEN
    RAISE EXCEPTION '❌ Missing columns: %', array_to_string(missing_columns, ', ');
  ELSE
    RAISE NOTICE '✅ All monitoring columns added successfully';
  END IF;
END $$;

-- Verify indexes created
DO $$
DECLARE
  index_count INTEGER;
BEGIN
  SELECT COUNT(*)
  INTO index_count
  FROM pg_indexes
  WHERE schemaname = 'public'
    AND tablename = 'setups'
    AND indexname LIKE 'idx_setups_%';

  IF index_count >= 4 THEN
    RAISE NOTICE '✅ % indexes created successfully', index_count;
  ELSE
    RAISE WARNING '⚠️ Only % indexes found (expected 4+)', index_count;
  END IF;
END $$;

-- Verify views created
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_views WHERE viewname = 'active_setups') AND
     EXISTS (SELECT 1 FROM pg_views WHERE viewname = 'completed_setups') THEN
    RAISE NOTICE '✅ Helper views created successfully';
  ELSE
    RAISE WARNING '⚠️ Some helper views missing';
  END IF;
END $$;

-- Verify functions created
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_proc WHERE proname = 'calculate_pnl_percent') AND
     EXISTS (SELECT 1 FROM pg_proc WHERE proname = 'get_setup_stats') AND
     EXISTS (SELECT 1 FROM pg_proc WHERE proname = 'expire_old_setups') THEN
    RAISE NOTICE '✅ Helper functions created successfully';
  ELSE
    RAISE WARNING '⚠️ Some helper functions missing';
  END IF;
END $$;

COMMIT;

-- =====================================================================
-- MIGRATION COMPLETE!
-- =====================================================================
--
-- Summary:
-- ✅ Extended setups table with 10 monitoring columns
-- ✅ Updated status enum with new values (entry_hit, sl_hit, tp_hit, expired)
-- ✅ Created 4 performance indexes
-- ✅ Created 2 helper views (active_setups, completed_setups)
-- ✅ Created 3 helper functions (calculate_pnl_percent, get_setup_stats, expire_old_setups)
-- ✅ Added comprehensive documentation comments
--
-- Next Steps:
-- 1. Test migration on dev environment
-- 2. Run verification queries (see below)
-- 3. Deploy to production
-- 4. Implement webhook endpoints
-- 5. Implement Pine Script generator
--
-- Verification Queries:
--
-- -- Test 1: Check new columns
-- SELECT column_name, data_type, is_nullable
-- FROM information_schema.columns
-- WHERE table_name = 'setups' AND column_name LIKE '%hit%';
--
-- -- Test 2: Check status constraint
-- INSERT INTO setups (user_id, symbol_id, module, status)
-- VALUES ('...', '...', 'tradingview', 'entry_hit');  -- Should work
--
-- -- Test 3: Test P&L calculation
-- SELECT calculate_pnl_percent(19500, 19600, 'long');  -- Should return 0.51
--
-- -- Test 4: Test views
-- SELECT * FROM active_setups LIMIT 5;
-- SELECT * FROM completed_setups LIMIT 5;
--
-- -- Test 5: Test statistics function
-- SELECT * FROM get_setup_stats('user-uuid-here', 30);
--
-- =====================================================================
