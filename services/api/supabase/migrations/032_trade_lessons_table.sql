-- =====================================================================
-- Migration: 032_trade_lessons_table.sql
-- Description: Create trade_lessons table for post-mortem analysis
-- Created: 2025-11-12
-- Feature: Trade Outcome Analysis (AI-Powered Post-Mortem)
-- =====================================================================
--
-- Purpose:
--   Store AI-generated analysis of why trades succeeded or failed.
--   Enable continuous learning from trading outcomes.
--
-- Related Documentation:
--   TOMORROW_TODO.md - Trade Outcome Analysis
--
-- =====================================================================

BEGIN;

-- =====================================================================
-- 1. CREATE TRADE_LESSONS TABLE
-- =====================================================================

CREATE TABLE IF NOT EXISTS trade_lessons (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Reference to setup
  setup_id UUID NOT NULL REFERENCES setups(id) ON DELETE CASCADE,

  -- Outcome context
  outcome TEXT NOT NULL,
  CONSTRAINT trade_lessons_outcome_check CHECK (outcome IN ('win', 'loss', 'invalidated', 'missed')),

  -- AI Analysis Results
  root_cause TEXT,
  failed_indicators TEXT[],
  lesson_learned TEXT NOT NULL,
  improved_strategy TEXT,

  -- Additional context
  analysis_payload JSONB,

  -- Timestamps
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- =====================================================================
-- 2. CREATE INDEXES
-- =====================================================================

-- Index for finding lessons by setup
CREATE INDEX IF NOT EXISTS idx_trade_lessons_setup_id
  ON trade_lessons(setup_id);

-- Index for finding lessons by outcome type
CREATE INDEX IF NOT EXISTS idx_trade_lessons_outcome
  ON trade_lessons(outcome);

-- Index for recent lessons
CREATE INDEX IF NOT EXISTS idx_trade_lessons_created_at
  ON trade_lessons(created_at DESC);

-- Unique constraint: One lesson per setup
CREATE UNIQUE INDEX IF NOT EXISTS idx_trade_lessons_setup_unique
  ON trade_lessons(setup_id);

-- =====================================================================
-- 3. ADD COMMENTS
-- =====================================================================

COMMENT ON TABLE trade_lessons IS 'AI-generated post-mortem analysis of completed trades';
COMMENT ON COLUMN trade_lessons.setup_id IS 'Reference to the setup that was analyzed';
COMMENT ON COLUMN trade_lessons.outcome IS 'Trade outcome: win (TP hit), loss (SL hit), invalidated (SL before entry), missed (TP before entry)';
COMMENT ON COLUMN trade_lessons.root_cause IS 'AI analysis: What went wrong or right?';
COMMENT ON COLUMN trade_lessons.failed_indicators IS 'List of indicators that failed to predict correctly';
COMMENT ON COLUMN trade_lessons.lesson_learned IS 'Key takeaway from this trade';
COMMENT ON COLUMN trade_lessons.improved_strategy IS 'How to improve the strategy based on this outcome';
COMMENT ON COLUMN trade_lessons.analysis_payload IS 'Full AI analysis response (JSON)';

-- =====================================================================
-- 4. CREATE HELPER VIEW: LESSONS WITH SETUP CONTEXT
-- =====================================================================

CREATE OR REPLACE VIEW trade_lessons_detailed AS
SELECT
  tl.id AS lesson_id,
  tl.setup_id,
  tl.outcome,
  tl.root_cause,
  tl.failed_indicators,
  tl.lesson_learned,
  tl.improved_strategy,
  tl.created_at AS lesson_created_at,
  -- Setup context
  s.user_id,
  ms.symbol,
  ms.alias AS symbol_name,
  s.side,
  s.entry_price,
  s.stop_loss,
  s.take_profit,
  s.confidence,
  s.status,
  s.pnl_percent,
  s.entry_hit_at,
  s.sl_hit_at,
  s.tp_hit_at,
  s.closed_at,
  s.created_at AS setup_created_at,
  -- Duration
  CASE
    WHEN s.closed_at IS NOT NULL AND s.entry_hit_at IS NOT NULL
      THEN EXTRACT(EPOCH FROM (s.closed_at - s.entry_hit_at)) / 3600.0
    ELSE NULL
  END AS trade_duration_hours
FROM trade_lessons tl
JOIN setups s ON tl.setup_id = s.id
JOIN market_symbols ms ON s.symbol_id = ms.id
ORDER BY tl.created_at DESC;

COMMENT ON VIEW trade_lessons_detailed IS 'Trade lessons with full setup context for analysis';

-- =====================================================================
-- 5. CREATE HELPER FUNCTIONS
-- =====================================================================

-- Function: Get lessons summary for a user
CREATE OR REPLACE FUNCTION get_lessons_summary(p_user_id UUID, p_days INTEGER DEFAULT 30)
RETURNS TABLE (
  total_lessons BIGINT,
  lessons_from_wins BIGINT,
  lessons_from_losses BIGINT,
  most_common_failure TEXT,
  top_improved_strategy TEXT
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    COUNT(*)::BIGINT AS total_lessons,
    COUNT(*) FILTER (WHERE outcome = 'win')::BIGINT AS lessons_from_wins,
    COUNT(*) FILTER (WHERE outcome = 'loss')::BIGINT AS lessons_from_losses,
    -- Most common root cause for losses
    (
      SELECT root_cause
      FROM trade_lessons tl
      JOIN setups s ON tl.setup_id = s.id
      WHERE s.user_id = p_user_id
        AND tl.outcome = 'loss'
        AND tl.root_cause IS NOT NULL
        AND tl.created_at >= NOW() - (p_days || ' days')::INTERVAL
      GROUP BY root_cause
      ORDER BY COUNT(*) DESC
      LIMIT 1
    ) AS most_common_failure,
    -- Most recent improved strategy
    (
      SELECT improved_strategy
      FROM trade_lessons tl
      JOIN setups s ON tl.setup_id = s.id
      WHERE s.user_id = p_user_id
        AND tl.improved_strategy IS NOT NULL
        AND tl.created_at >= NOW() - (p_days || ' days')::INTERVAL
      ORDER BY tl.created_at DESC
      LIMIT 1
    ) AS top_improved_strategy
  FROM trade_lessons tl
  JOIN setups s ON tl.setup_id = s.id
  WHERE s.user_id = p_user_id
    AND tl.created_at >= NOW() - (p_days || ' days')::INTERVAL;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_lessons_summary IS 'Get summary of trade lessons for a user (common failures, improvements)';

-- Function: Get most valuable lessons (sorted by impact)
CREATE OR REPLACE FUNCTION get_top_lessons(p_user_id UUID, p_limit INTEGER DEFAULT 5)
RETURNS TABLE (
  lesson_id UUID,
  outcome TEXT,
  lesson_learned TEXT,
  improved_strategy TEXT,
  pnl_percent NUMERIC,
  created_at TIMESTAMPTZ
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    tl.id AS lesson_id,
    tl.outcome,
    tl.lesson_learned,
    tl.improved_strategy,
    s.pnl_percent,
    tl.created_at
  FROM trade_lessons tl
  JOIN setups s ON tl.setup_id = s.id
  WHERE s.user_id = p_user_id
  ORDER BY
    -- Prioritize lessons from big losses (to avoid repeating mistakes)
    CASE WHEN tl.outcome = 'loss' THEN ABS(s.pnl_percent) ELSE 0 END DESC,
    tl.created_at DESC
  LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_top_lessons IS 'Get most valuable trade lessons (prioritizes big losses to avoid repeating)';

-- =====================================================================
-- 6. CREATE TRIGGER FOR UPDATED_AT
-- =====================================================================

CREATE OR REPLACE FUNCTION update_trade_lessons_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_trade_lessons_updated_at
  BEFORE UPDATE ON trade_lessons
  FOR EACH ROW
  EXECUTE FUNCTION update_trade_lessons_updated_at();

-- =====================================================================
-- 7. VERIFICATION
-- =====================================================================

DO $$
BEGIN
  -- Verify table exists
  IF EXISTS (SELECT 1 FROM pg_tables WHERE tablename = 'trade_lessons') THEN
    RAISE NOTICE '✅ trade_lessons table created successfully';
  ELSE
    RAISE EXCEPTION '❌ trade_lessons table not created';
  END IF;

  -- Verify indexes
  IF EXISTS (SELECT 1 FROM pg_indexes WHERE tablename = 'trade_lessons' AND indexname LIKE 'idx_trade_lessons_%') THEN
    RAISE NOTICE '✅ Indexes created successfully';
  ELSE
    RAISE WARNING '⚠️ Some indexes may be missing';
  END IF;

  -- Verify view
  IF EXISTS (SELECT 1 FROM pg_views WHERE viewname = 'trade_lessons_detailed') THEN
    RAISE NOTICE '✅ trade_lessons_detailed view created successfully';
  ELSE
    RAISE WARNING '⚠️ View missing';
  END IF;

  -- Verify functions
  IF EXISTS (SELECT 1 FROM pg_proc WHERE proname = 'get_lessons_summary') AND
     EXISTS (SELECT 1 FROM pg_proc WHERE proname = 'get_top_lessons') THEN
    RAISE NOTICE '✅ Helper functions created successfully';
  ELSE
    RAISE WARNING '⚠️ Some functions missing';
  END IF;
END $$;

COMMIT;

-- =====================================================================
-- MIGRATION COMPLETE!
-- =====================================================================
--
-- Summary:
-- ✅ Created trade_lessons table with AI analysis fields
-- ✅ Created indexes (setup_id, outcome, created_at, unique constraint)
-- ✅ Created trade_lessons_detailed view (with setup context)
-- ✅ Created get_lessons_summary() function (common failures, improvements)
-- ✅ Created get_top_lessons() function (most valuable lessons)
-- ✅ Created updated_at trigger
--
-- Next Steps:
-- 1. Run this migration in Supabase SQL Editor
-- 2. Implement POST /api/setups/{id}/analyze-outcome endpoint
-- 3. Auto-trigger analysis when SL/TP hit (in monitor endpoint)
-- 4. Display lessons in Setup Card UI
-- 5. Create lessons dashboard page
--
-- Example Usage:
--
-- -- Get lessons summary for user
-- SELECT * FROM get_lessons_summary('user-uuid-here', 30);
--
-- -- Get top 5 most valuable lessons
-- SELECT * FROM get_top_lessons('user-uuid-here', 5);
--
-- -- Get all lessons with context
-- SELECT * FROM trade_lessons_detailed WHERE user_id = 'user-uuid-here';
--
-- =====================================================================
