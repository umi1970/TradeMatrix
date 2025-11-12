-- =====================================================================
-- Migration: 031_add_setup_validity_and_analysis.sql
-- Description: Add validity period and outcome analysis for setups
-- Created: 2025-11-12
-- Feature: Trade Lifecycle Management
-- =====================================================================
--
-- Purpose:
--   Add missing columns for setup validity tracking and post-mortem analysis.
--   Extends 030_setup_monitoring.sql with additional lifecycle fields.
--
-- Related Documentation:
--   TOMORROW_TODO.md - Trade Monitoring & Validation
--
-- =====================================================================

BEGIN;

-- =====================================================================
-- 1. ADD VALIDITY AND LIFECYCLE COLUMNS
-- =====================================================================

-- Validity Period
ALTER TABLE setups ADD COLUMN IF NOT EXISTS valid_until TIMESTAMPTZ;

COMMENT ON COLUMN setups.valid_until IS 'Setup expires after this timestamp if entry not hit (calculated based on timeframe)';

-- Monitoring Lifecycle
ALTER TABLE setups ADD COLUMN IF NOT EXISTS monitoring_started_at TIMESTAMPTZ;

COMMENT ON COLUMN setups.monitoring_started_at IS 'Timestamp when trade monitoring started (after entry hit)';

-- Closed Timestamp
ALTER TABLE setups ADD COLUMN IF NOT EXISTS closed_at TIMESTAMPTZ;

COMMENT ON COLUMN setups.closed_at IS 'Timestamp when trade was closed (TP hit, SL hit, or expired)';

-- Post-Mortem Analysis
ALTER TABLE setups ADD COLUMN IF NOT EXISTS outcome_analysis TEXT;

COMMENT ON COLUMN setups.outcome_analysis IS 'AI-generated post-mortem analysis explaining why trade succeeded/failed';

-- =====================================================================
-- 2. CREATE HELPER FUNCTION TO CALCULATE valid_until
-- =====================================================================

CREATE OR REPLACE FUNCTION calculate_valid_until(
  p_created_at TIMESTAMPTZ,
  p_timeframe TEXT
)
RETURNS TIMESTAMPTZ AS $$
DECLARE
  validity_hours INTEGER;
BEGIN
  -- Calculate validity based on timeframe
  CASE p_timeframe
    WHEN '1m', '5m', '15m' THEN
      validity_hours := 6;  -- Intraday: 6 hours
    WHEN '1h', '4h' THEN
      validity_hours := 48;  -- Swing: 2 days
    WHEN '1d' THEN
      validity_hours := 120;  -- Midterm: 5 days
    ELSE
      validity_hours := 24;  -- Default: 1 day
  END CASE;

  RETURN p_created_at + (validity_hours || ' hours')::INTERVAL;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

COMMENT ON FUNCTION calculate_valid_until IS 'Calculate setup expiration time based on timeframe (1m/5m/15m: 6h, 1h/4h: 48h, 1d: 120h)';

-- =====================================================================
-- 3. UPDATE EXISTING SETUPS WITH valid_until
-- =====================================================================

-- Backfill valid_until for existing setups
UPDATE setups
SET valid_until = calculate_valid_until(created_at,
  COALESCE(
    (payload->>'timeframe')::TEXT,
    '1h'  -- Default to 1h if timeframe missing
  )
)
WHERE valid_until IS NULL
  AND status IN ('pending', 'entry_hit');

-- =====================================================================
-- 4. CREATE TRIGGER TO AUTO-SET valid_until ON INSERT
-- =====================================================================

CREATE OR REPLACE FUNCTION set_valid_until_on_insert()
RETURNS TRIGGER AS $$
BEGIN
  -- Only set if not already provided
  IF NEW.valid_until IS NULL THEN
    NEW.valid_until := calculate_valid_until(
      NEW.created_at,
      COALESCE(
        (NEW.payload->>'timeframe')::TEXT,
        '1h'
      )
    );
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_set_valid_until
  BEFORE INSERT ON setups
  FOR EACH ROW
  EXECUTE FUNCTION set_valid_until_on_insert();

COMMENT ON TRIGGER trigger_set_valid_until ON setups IS 'Auto-calculate valid_until based on timeframe when setup is created';

-- =====================================================================
-- 5. CREATE TRIGGER TO AUTO-SET closed_at
-- =====================================================================

CREATE OR REPLACE FUNCTION set_closed_at_on_outcome()
RETURNS TRIGGER AS $$
BEGIN
  -- Set closed_at when outcome is set
  IF NEW.outcome IS NOT NULL AND OLD.outcome IS NULL THEN
    NEW.closed_at := NOW();
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_set_closed_at
  BEFORE UPDATE ON setups
  FOR EACH ROW
  EXECUTE FUNCTION set_closed_at_on_outcome();

COMMENT ON TRIGGER trigger_set_closed_at ON setups IS 'Auto-set closed_at timestamp when outcome is determined';

-- =====================================================================
-- 6. UPDATE EXPIRED SETUPS FUNCTION
-- =====================================================================

-- Replace the expire_old_setups function with validity-aware version
CREATE OR REPLACE FUNCTION expire_old_setups()
RETURNS INTEGER AS $$
DECLARE
  expired_count INTEGER;
BEGIN
  -- Mark setups as expired if:
  -- 1. Status is 'pending' (entry not hit yet)
  -- 2. valid_until has passed
  UPDATE setups
  SET
    status = 'expired',
    outcome = 'missed',  -- Entry never hit
    pine_script_active = false,
    closed_at = NOW(),
    updated_at = NOW()
  WHERE status = 'pending'
    AND valid_until < NOW();

  GET DIAGNOSTICS expired_count = ROW_COUNT;
  RETURN expired_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION expire_old_setups IS 'Auto-expire pending setups past their valid_until timestamp';

-- =====================================================================
-- 7. CREATE INDEXES FOR PERFORMANCE
-- =====================================================================

-- Index for expiration checks
CREATE INDEX IF NOT EXISTS idx_setups_valid_until
  ON setups(valid_until)
  WHERE status = 'pending' AND valid_until IS NOT NULL;

-- Index for closed trades
CREATE INDEX IF NOT EXISTS idx_setups_closed_at
  ON setups(closed_at)
  WHERE closed_at IS NOT NULL;

-- =====================================================================
-- 8. UPDATE VIEWS
-- =====================================================================

-- Drop existing views before recreating (to avoid column conflicts)
DROP VIEW IF EXISTS active_setups;
DROP VIEW IF EXISTS completed_setups;

-- Recreate active_setups view with validity info
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
  s.valid_until,
  s.created_at,
  -- Calculate time remaining
  CASE
    WHEN s.valid_until IS NOT NULL AND s.status = 'pending'
      THEN EXTRACT(EPOCH FROM (s.valid_until - NOW())) / 3600.0
    ELSE NULL
  END AS hours_remaining
FROM setups s
JOIN market_symbols ms ON s.symbol_id = ms.id
WHERE s.status IN ('pending', 'entry_hit')
  AND (s.valid_until IS NULL OR s.valid_until > NOW())
ORDER BY s.created_at DESC;

COMMENT ON VIEW active_setups IS 'Active setups (pending or entry hit) with validity and time remaining';

-- Update completed_setups view to include analysis
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
  s.closed_at,
  s.outcome_analysis,
  s.created_at,
  -- Calculate duration (entry to close)
  CASE
    WHEN s.closed_at IS NOT NULL AND s.entry_hit_at IS NOT NULL
      THEN EXTRACT(EPOCH FROM (s.closed_at - s.entry_hit_at)) / 3600.0
    ELSE NULL
  END AS duration_hours,
  -- Calculate total time (created to close)
  CASE
    WHEN s.closed_at IS NOT NULL
      THEN EXTRACT(EPOCH FROM (s.closed_at - s.created_at)) / 3600.0
    ELSE NULL
  END AS total_hours
FROM setups s
JOIN market_symbols ms ON s.symbol_id = ms.id
WHERE s.outcome IS NOT NULL OR s.closed_at IS NOT NULL
ORDER BY s.created_at DESC;

COMMENT ON VIEW completed_setups IS 'Completed setups with outcomes, P&L, and post-mortem analysis';

-- =====================================================================
-- 9. VERIFICATION
-- =====================================================================

DO $$
DECLARE
  missing_columns TEXT[];
BEGIN
  SELECT ARRAY_AGG(column_name)
  INTO missing_columns
  FROM (
    VALUES
      ('valid_until'),
      ('monitoring_started_at'),
      ('closed_at'),
      ('outcome_analysis')
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
    RAISE NOTICE '✅ All validity and analysis columns added successfully';
  END IF;
END $$;

-- Verify triggers
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trigger_set_valid_until') AND
     EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trigger_set_closed_at') THEN
    RAISE NOTICE '✅ Auto-set triggers created successfully';
  ELSE
    RAISE WARNING '⚠️ Some triggers missing';
  END IF;
END $$;

COMMIT;

-- =====================================================================
-- MIGRATION COMPLETE!
-- =====================================================================
--
-- Summary:
-- ✅ Added 4 new columns: valid_until, monitoring_started_at, closed_at, outcome_analysis
-- ✅ Created calculate_valid_until() function (timeframe-based expiration)
-- ✅ Created auto-set triggers for valid_until and closed_at
-- ✅ Updated expire_old_setups() to use valid_until
-- ✅ Updated active_setups and completed_setups views
-- ✅ Created performance indexes
--
-- Next Steps:
-- 1. Run this migration in Supabase SQL Editor
-- 2. Test with sample data
-- 3. Implement POST /api/setups/{id}/monitor endpoint
-- 4. Add CSV upload UI in Setup Card
-- 5. Implement post-mortem analysis (OpenAI)
--
-- =====================================================================
