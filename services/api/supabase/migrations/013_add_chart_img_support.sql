-- =====================================================================
-- Migration: 013_add_chart_img_support.sql
-- Description: Add chart-img.com integration for dynamic chart generation
-- Created: 2025-11-02
--
-- Purpose:
--   - Enable dynamic chart generation via chart-img.com API
--   - Store TradingView symbol mappings for 5 main symbols
--   - Track chart snapshot history with metadata
--   - Support multiple timeframes (1h, 4h, 1d)
--   - Configure indicators per symbol (EMAs, RSI, Volume)
--
-- Tables Modified:
--   1. market_symbols - Add chart configuration fields
--
-- Tables Created:
--   1. chart_snapshots - Store generated chart URLs and metadata
--
-- Rollback Instructions:
--   DROP TABLE IF EXISTS public.chart_snapshots CASCADE;
--   ALTER TABLE public.symbols
--     DROP COLUMN IF EXISTS chart_img_symbol,
--     DROP COLUMN IF EXISTS chart_enabled,
--     DROP COLUMN IF EXISTS chart_config;
-- =====================================================================

BEGIN;

-- =====================================================================
-- 1. EXTEND SYMBOLS TABLE
-- Add chart-img.com configuration fields
-- =====================================================================

-- Add new columns for chart configuration
DO $$
BEGIN
    -- Check if chart_img_symbol column exists, if not add it
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name = 'symbols'
        AND column_name = 'chart_img_symbol'
    ) THEN
        ALTER TABLE public.symbols
        ADD COLUMN chart_img_symbol TEXT;
    END IF;

    -- Check if chart_enabled column exists, if not add it
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name = 'symbols'
        AND column_name = 'chart_enabled'
    ) THEN
        ALTER TABLE public.symbols
        ADD COLUMN chart_enabled BOOLEAN DEFAULT false;
    END IF;

    -- Check if chart_config column exists, if not add it
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name = 'symbols'
        AND column_name = 'chart_config'
    ) THEN
        ALTER TABLE public.symbols
        ADD COLUMN chart_config JSONB DEFAULT '{
          "timeframes": ["1h", "4h", "1d"],
          "indicators": ["EMA_20", "EMA_50", "EMA_200", "RSI", "Volume"],
          "default_timeframe": "4h"
        }'::jsonb;
    END IF;
END $$;

-- Create index for faster queries on chart-enabled symbols
CREATE INDEX IF NOT EXISTS idx_symbols_chart_enabled
  ON public.symbols(chart_enabled)
  WHERE chart_enabled = true;

-- =====================================================================
-- 2. CREATE CHART_SNAPSHOTS TABLE
-- Stores generated chart snapshots from chart-img.com
-- =====================================================================

-- Drop table if exists (for clean migration)
DROP TABLE IF EXISTS public.chart_snapshots CASCADE;

CREATE TABLE public.chart_snapshots (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  symbol_id UUID NOT NULL REFERENCES public.symbols(id) ON DELETE CASCADE,
  timeframe TEXT NOT NULL CHECK (timeframe IN ('1m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '12h', '1d', '3d', '1w', '1M')),
  chart_url TEXT NOT NULL,
  trigger_type TEXT NOT NULL CHECK (trigger_type IN ('manual', 'report', 'setup', 'analysis', 'monitoring', 'alert')),
  generated_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
  generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  expires_at TIMESTAMPTZ,  -- 60 days retention by chart-img.com
  metadata JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =====================================================================
-- 3. CREATE INDEXES FOR PERFORMANCE
-- Optimize common query patterns
-- =====================================================================

CREATE INDEX IF NOT EXISTS idx_chart_snapshots_symbol_id
  ON public.chart_snapshots(symbol_id);

CREATE INDEX IF NOT EXISTS idx_chart_snapshots_generated_at
  ON public.chart_snapshots(generated_at DESC);

CREATE INDEX IF NOT EXISTS idx_chart_snapshots_timeframe
  ON public.chart_snapshots(timeframe);

CREATE INDEX IF NOT EXISTS idx_chart_snapshots_trigger_type
  ON public.chart_snapshots(trigger_type);

CREATE INDEX IF NOT EXISTS idx_chart_snapshots_symbol_timeframe
  ON public.chart_snapshots(symbol_id, timeframe);

-- =====================================================================
-- 4. SETUP ROW LEVEL SECURITY (RLS)
-- Define access policies for chart_snapshots
-- =====================================================================

-- Enable RLS
ALTER TABLE public.chart_snapshots ENABLE ROW LEVEL SECURITY;

-- Policy: Anyone can view chart snapshots
DROP POLICY IF EXISTS "Anyone can view chart_snapshots" ON public.chart_snapshots;
CREATE POLICY "Anyone can view chart_snapshots"
  ON public.chart_snapshots FOR SELECT
  USING (true);

-- Policy: Authenticated users can create chart snapshots
DROP POLICY IF EXISTS "Authenticated users can create chart_snapshots" ON public.chart_snapshots;
CREATE POLICY "Authenticated users can create chart_snapshots"
  ON public.chart_snapshots FOR INSERT
  WITH CHECK (auth.role() = 'authenticated');

-- Policy: Users can delete their own chart snapshots
DROP POLICY IF EXISTS "Users can delete own chart_snapshots" ON public.chart_snapshots;
CREATE POLICY "Users can delete own chart_snapshots"
  ON public.chart_snapshots FOR DELETE
  USING (generated_by = auth.uid());

-- Policy: Service role can manage all snapshots (backend cleanup)
DROP POLICY IF EXISTS "Service role can manage all chart_snapshots" ON public.chart_snapshots;
CREATE POLICY "Service role can manage all chart_snapshots"
  ON public.chart_snapshots FOR ALL
  USING (auth.role() = 'service_role');

-- =====================================================================
-- 5. INSERT INITIAL DATA FOR 5 MAIN SYMBOLS
-- Configure TradingView symbols and chart settings
-- =====================================================================

-- DAX (Germany 40 Index)
UPDATE public.symbols SET
  chart_img_symbol = 'XETR:DAX',
  chart_enabled = true,
  chart_config = '{
    "timeframes": ["1h", "4h", "1d"],
    "indicators": ["EMA_20", "EMA_50", "EMA_200", "RSI", "Volume"],
    "default_timeframe": "4h",
    "theme": "dark"
  }'::jsonb
WHERE symbol = '^GDAXI' AND chart_img_symbol IS NULL;

-- NASDAQ 100 (US Tech Index)
UPDATE public.symbols SET
  chart_img_symbol = 'NASDAQ:NDX',
  chart_enabled = true,
  chart_config = '{
    "timeframes": ["1h", "4h", "1d"],
    "indicators": ["EMA_20", "EMA_50", "EMA_200", "RSI", "Volume"],
    "default_timeframe": "4h",
    "theme": "dark"
  }'::jsonb
WHERE symbol = '^NDX' AND chart_img_symbol IS NULL;

-- DOW JONES (US 30 Index)
UPDATE public.symbols SET
  chart_img_symbol = 'DJCFD:DJI',
  chart_enabled = true,
  chart_config = '{
    "timeframes": ["1h", "4h", "1d"],
    "indicators": ["EMA_20", "EMA_50", "EMA_200", "RSI", "Volume"],
    "default_timeframe": "4h",
    "theme": "dark"
  }'::jsonb
WHERE symbol = '^DJI' AND chart_img_symbol IS NULL;

-- EUR/USD (Forex Major Pair)
UPDATE public.symbols SET
  chart_img_symbol = 'OANDA:EURUSD',
  chart_enabled = true,
  chart_config = '{
    "timeframes": ["1h", "4h", "1d"],
    "indicators": ["EMA_20", "EMA_50", "RSI", "Volume"],
    "default_timeframe": "4h",
    "theme": "dark"
  }'::jsonb
WHERE symbol = 'EURUSD' AND chart_img_symbol IS NULL;

-- EUR/GBP (Forex Major Pair)
-- Note: EURGBP might not exist yet, check if GBPUSD was inserted instead
UPDATE public.symbols SET
  chart_img_symbol = 'OANDA:EURGBP',
  chart_enabled = true,
  chart_config = '{
    "timeframes": ["1h", "4h", "1d"],
    "indicators": ["EMA_20", "EMA_50", "RSI", "Volume"],
    "default_timeframe": "4h",
    "theme": "dark"
  }'::jsonb
WHERE symbol = 'EURGBP' AND chart_img_symbol IS NULL;

-- Also configure GBPUSD if it exists (from migration 010)
UPDATE public.symbols SET
  chart_img_symbol = 'OANDA:GBPUSD',
  chart_enabled = true,
  chart_config = '{
    "timeframes": ["1h", "4h", "1d"],
    "indicators": ["EMA_20", "EMA_50", "RSI", "Volume"],
    "default_timeframe": "4h",
    "theme": "dark"
  }'::jsonb
WHERE symbol = 'GBPUSD' AND chart_img_symbol IS NULL;

-- =====================================================================
-- 6. ADD DOCUMENTATION COMMENTS
-- Provide context for future developers
-- =====================================================================

COMMENT ON COLUMN public.symbols.chart_img_symbol IS 'TradingView symbol for chart-img.com API (e.g. XETR:DAX, NASDAQ:NDX, OANDA:EURUSD)';
COMMENT ON COLUMN public.symbols.chart_enabled IS 'Whether chart generation is enabled for this symbol';
COMMENT ON COLUMN public.symbols.chart_config IS 'JSON configuration for chart generation: timeframes, indicators, theme, default_timeframe';

COMMENT ON TABLE public.chart_snapshots IS 'Stores generated chart snapshots from chart-img.com API with 60-day retention';
COMMENT ON COLUMN public.chart_snapshots.symbol_id IS 'Reference to symbols table';
COMMENT ON COLUMN public.chart_snapshots.timeframe IS 'Chart timeframe (1m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 12h, 1d, 3d, 1w, 1M)';
COMMENT ON COLUMN public.chart_snapshots.chart_url IS 'Full URL to the generated chart image on chart-img.com CDN';
COMMENT ON COLUMN public.chart_snapshots.trigger_type IS 'What triggered this chart generation: manual, report, setup, analysis, monitoring, alert';
COMMENT ON COLUMN public.chart_snapshots.generated_by IS 'User who triggered chart generation (NULL for automated)';
COMMENT ON COLUMN public.chart_snapshots.expires_at IS 'When chart-img.com will delete the chart (typically 60 days from generated_at)';
COMMENT ON COLUMN public.chart_snapshots.metadata IS 'Additional metadata: indicator_values, annotations, notes, etc.';

-- =====================================================================
-- 7. CREATE UTILITY FUNCTIONS
-- Helper functions for chart snapshot management
-- =====================================================================

-- Function to get latest chart snapshot for a symbol and timeframe
CREATE OR REPLACE FUNCTION get_latest_chart_snapshot(p_symbol_id UUID, p_timeframe TEXT)
RETURNS TABLE (
  id UUID,
  chart_url TEXT,
  generated_at TIMESTAMPTZ,
  expires_at TIMESTAMPTZ,
  metadata JSONB
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    cs.id,
    cs.chart_url,
    cs.generated_at,
    cs.expires_at,
    cs.metadata
  FROM public.chart_snapshots cs
  WHERE cs.symbol_id = p_symbol_id
    AND cs.timeframe = p_timeframe
  ORDER BY cs.generated_at DESC
  LIMIT 1;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_latest_chart_snapshot(UUID, TEXT) IS 'Returns the most recent chart snapshot for a given symbol and timeframe';

-- Function to cleanup expired chart snapshots
CREATE OR REPLACE FUNCTION cleanup_expired_chart_snapshots()
RETURNS INTEGER AS $$
DECLARE
  deleted_count INTEGER;
BEGIN
  DELETE FROM public.chart_snapshots
  WHERE expires_at IS NOT NULL
    AND expires_at < NOW();

  GET DIAGNOSTICS deleted_count = ROW_COUNT;
  RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION cleanup_expired_chart_snapshots() IS 'Deletes chart snapshots past their expiration date, returns count of deleted rows';

-- =====================================================================
-- MIGRATION COMPLETE
-- =====================================================================

COMMIT;

-- Summary:
-- ✅ Extended symbols table with chart configuration fields
-- ✅ Created chart_snapshots table with RLS policies
-- ✅ Added performance indexes for common query patterns
-- ✅ Configured 5 main symbols with TradingView mappings:
--    - DAX (XETR:DAX)
--    - NASDAQ (NASDAQ:NDX)
--    - DOW JONES (DJCFD:DJI)
--    - EUR/USD (OANDA:EURUSD)
--    - EUR/GBP (OANDA:EURGBP)
-- ✅ Created utility functions for snapshot management
-- ✅ Added comprehensive documentation comments
--
-- Next Steps:
-- 1. Run validation queries (see below)
-- 2. Implement chart-img.com API integration in FastAPI
-- 3. Create frontend UI for chart display
--
-- Validation Queries:
--
-- -- Test 1: Check new columns and configured symbols
-- SELECT symbol, chart_img_symbol, chart_enabled, chart_config
-- FROM public.symbols
-- WHERE chart_enabled = true;
--
-- -- Test 2: Insert test snapshot (as authenticated user)
-- INSERT INTO public.chart_snapshots (symbol_id, timeframe, chart_url, trigger_type, generated_by)
-- VALUES (
--   (SELECT id FROM public.symbols WHERE symbol = '^GDAXI' LIMIT 1),
--   '4h',
--   'https://chart-img.com/test/dax-4h-20251102.png',
--   'manual',
--   auth.uid()
-- );
--
-- -- Test 3: Query snapshots
-- SELECT
--   cs.id,
--   s.symbol,
--   s.chart_img_symbol,
--   cs.timeframe,
--   cs.chart_url,
--   cs.trigger_type,
--   cs.generated_at
-- FROM public.chart_snapshots cs
-- JOIN public.symbols s ON cs.symbol_id = s.id
-- ORDER BY cs.generated_at DESC
-- LIMIT 10;
--
-- -- Test 4: Test utility function
-- SELECT * FROM get_latest_chart_snapshot(
--   (SELECT id FROM public.symbols WHERE symbol = '^GDAXI' LIMIT 1),
--   '4h'
-- );
--
-- -- Test 5: Test cleanup function (dry run)
-- SELECT cleanup_expired_chart_snapshots();
