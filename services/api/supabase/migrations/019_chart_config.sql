-- =============================================
-- Migration 019: Add chart_config to market_symbols
-- Created: 2025-11-05
-- Description: Extends market_symbols with JSONB chart configuration for chart-img.com API
-- =============================================

BEGIN;

-- Add chart_config column
ALTER TABLE market_symbols
ADD COLUMN IF NOT EXISTS chart_config JSONB DEFAULT '{}'::JSONB;

-- Add comment
COMMENT ON COLUMN market_symbols.chart_config
IS 'User-defined chart configuration for chart-img.com API (indicators, timeframes, theme, etc.)';

-- Create GIN index for JSONB queries
CREATE INDEX IF NOT EXISTS idx_market_symbols_chart_config
ON market_symbols USING GIN (chart_config);

-- Set default chart_config for existing symbols
-- Uses TVC: prefix for real-time data (TVC:DAX, TVC:DJI, etc.)
UPDATE market_symbols
SET chart_config = jsonb_build_object(
    'tv_symbol', CASE symbol
        WHEN 'DAX' THEN 'TVC:DAX'
        WHEN 'NDX' THEN 'NASDAQ:NDX'
        WHEN 'DJI' THEN 'TVC:DJI'
        WHEN 'EUR/USD' THEN 'FX:EURUSD'
        WHEN 'XAG/USD' THEN 'FX:XAGUSD'
        ELSE symbol
    END,
    'timeframes', ARRAY['15', '60', 'D']::TEXT[],
    'indicators', ARRAY['Relative Strength Index']::TEXT[],
    'chart_type', 'candles',
    'theme', 'dark',
    'width', 1200,
    'height', 800,
    'show_volume', true,
    'show_legend', true,
    'timezone', 'Europe/Berlin'
)
WHERE chart_config = '{}'::JSONB OR chart_config IS NULL;

-- Verify migration
DO $$
DECLARE
    v_count INT;
BEGIN
    SELECT COUNT(*) INTO v_count
    FROM market_symbols
    WHERE chart_config IS NOT NULL AND chart_config != '{}'::JSONB;

    IF v_count > 0 THEN
        RAISE NOTICE '✅ Chart config added to % symbols', v_count;
    ELSE
        RAISE WARNING '⚠️ No symbols updated with chart_config';
    END IF;
END $$;

COMMIT;

-- =============================================
-- USAGE EXAMPLES
-- =============================================

-- Query symbols with specific indicator
-- SELECT symbol, alias, chart_config
-- FROM market_symbols
-- WHERE chart_config @> '{"indicators": ["Relative Strength Index"]}';

-- Query symbols with D1 timeframe
-- SELECT symbol, alias, chart_config
-- FROM market_symbols
-- WHERE chart_config->'timeframes' ? 'D';

-- Update chart config for specific symbol
-- UPDATE market_symbols
-- SET chart_config = chart_config || '{"indicators": ["RSI", "MACD"]}'::JSONB
-- WHERE symbol = 'DAX';
