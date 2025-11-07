-- =====================================================================
-- Migration: 024_normalize_price_data.sql
-- Description: Normalize price data - merge price_cache into current_prices, drop symbols table
-- Created: 2025-11-07
-- Reason: Eliminate redundancy - only ONE price table needed (current_prices)
--         Migration 023 was incorrect - current_prices should reference market_symbols (original design)
--         symbols table was created for EOD data layer but is not needed for day trading
--         price_cache duplicates current_prices - remove it
-- =====================================================================

BEGIN;

-- =====================================================================
-- STEP 1: Drop price_cache table (redundant - created by Migration 012)
-- =====================================================================
-- Note: liquidity_alert_engine.py will be refactored to use current_prices instead
DROP TABLE IF EXISTS public.price_cache CASCADE;

-- =====================================================================
-- STEP 2: Drop existing FK constraint to symbols (from Migration 023)
-- =====================================================================
ALTER TABLE public.current_prices
    DROP CONSTRAINT IF EXISTS current_prices_symbol_id_fkey;

-- =====================================================================
-- STEP 3: Add FK constraint back to market_symbols (original design)
-- =====================================================================
ALTER TABLE public.current_prices
    ADD CONSTRAINT current_prices_symbol_id_fkey
    FOREIGN KEY (symbol_id)
    REFERENCES public.market_symbols(id)
    ON DELETE CASCADE;

-- =====================================================================
-- STEP 4: Add api_symbol column to market_symbols (for PriceFetcher)
-- =====================================================================
-- PriceFetcher needs to know API-specific symbol format (e.g., ^GDAXI for yfinance)
-- This avoids hardcoded mapping in code
ALTER TABLE public.market_symbols
    ADD COLUMN IF NOT EXISTS api_symbol TEXT;

COMMENT ON COLUMN public.market_symbols.api_symbol IS
    'API-specific symbol format (e.g., ^GDAXI for yfinance, EUR/USD for twelvedata)';

-- Populate api_symbol for existing symbols
UPDATE public.market_symbols SET api_symbol = '^GDAXI' WHERE symbol = 'DAX';
UPDATE public.market_symbols SET api_symbol = '^NDX' WHERE symbol = 'NDX';
UPDATE public.market_symbols SET api_symbol = '^DJI' WHERE symbol = 'DJI';
UPDATE public.market_symbols SET api_symbol = 'EUR/USD' WHERE symbol = 'EUR/USD';
UPDATE public.market_symbols SET api_symbol = 'EUR/GBP' WHERE symbol = 'EUR/GBP';
UPDATE public.market_symbols SET api_symbol = 'GBP/USD' WHERE symbol = 'GBP/USD';

-- =====================================================================
-- STEP 5: Migrate chart-img.com columns from symbols to market_symbols
-- =====================================================================
-- Migration 013 added these columns to symbols table
-- We need to preserve chart configuration when dropping symbols table

-- Add chart columns to market_symbols
ALTER TABLE public.market_symbols
    ADD COLUMN IF NOT EXISTS chart_img_symbol TEXT,
    ADD COLUMN IF NOT EXISTS chart_enabled BOOLEAN DEFAULT false,
    ADD COLUMN IF NOT EXISTS chart_config JSONB DEFAULT '{
      "timeframes": ["1h", "4h", "1d"],
      "indicators": ["EMA_20", "EMA_50", "EMA_200", "RSI", "Volume"],
      "default_timeframe": "4h"
    }'::jsonb;

-- Create index for faster queries on chart-enabled symbols
CREATE INDEX IF NOT EXISTS idx_market_symbols_chart_enabled
  ON public.market_symbols(chart_enabled)
  WHERE chart_enabled = true;

-- Migrate chart configuration from symbols to market_symbols
-- Mapping: symbols.symbol (^GDAXI, ^NDX, ^DJI, EURUSD) → market_symbols.symbol (DAX, NDX, DJI, EUR/USD)
UPDATE public.market_symbols ms
SET
    chart_img_symbol = s.chart_img_symbol,
    chart_enabled = s.chart_enabled,
    chart_config = s.chart_config
FROM public.symbols s
WHERE (
    -- Map index symbols (^GDAXI → DAX)
    (s.symbol = '^GDAXI' AND ms.symbol = 'DAX') OR
    (s.symbol = '^NDX' AND ms.symbol = 'NDX') OR
    (s.symbol = '^DJI' AND ms.symbol = 'DJI') OR
    -- Map forex symbols (EURUSD → EUR/USD)
    (s.symbol = 'EURUSD' AND ms.symbol = 'EUR/USD') OR
    (s.symbol = 'EURGBP' AND ms.symbol = 'EUR/GBP') OR
    (s.symbol = 'GBPUSD' AND ms.symbol = 'GBP/USD')
);

COMMENT ON COLUMN public.market_symbols.chart_img_symbol IS 'TradingView symbol for chart-img.com API (e.g. XETR:DAX, NASDAQ:NDX, OANDA:EURUSD)';
COMMENT ON COLUMN public.market_symbols.chart_enabled IS 'Whether chart generation is enabled for this symbol';
COMMENT ON COLUMN public.market_symbols.chart_config IS 'JSON configuration for chart generation: timeframes, indicators, theme, default_timeframe';

-- =====================================================================
-- STEP 6: Update chart_snapshots FK to reference market_symbols
-- =====================================================================
-- chart_snapshots currently references symbols.id
-- Need to update FK to reference market_symbols.id

-- First, update existing snapshot records to point to market_symbols
UPDATE public.chart_snapshots cs
SET symbol_id = ms.id
FROM public.symbols s
JOIN public.market_symbols ms ON (
    (s.symbol = '^GDAXI' AND ms.symbol = 'DAX') OR
    (s.symbol = '^NDX' AND ms.symbol = 'NDX') OR
    (s.symbol = '^DJI' AND ms.symbol = 'DJI') OR
    (s.symbol = 'EURUSD' AND ms.symbol = 'EUR/USD') OR
    (s.symbol = 'EURGBP' AND ms.symbol = 'EUR/GBP') OR
    (s.symbol = 'GBPUSD' AND ms.symbol = 'GBP/USD')
)
WHERE cs.symbol_id = s.id;

-- Drop existing FK constraint to symbols
ALTER TABLE public.chart_snapshots
    DROP CONSTRAINT IF EXISTS chart_snapshots_symbol_id_fkey;

-- Add new FK constraint to market_symbols
ALTER TABLE public.chart_snapshots
    ADD CONSTRAINT chart_snapshots_symbol_id_fkey
    FOREIGN KEY (symbol_id)
    REFERENCES public.market_symbols(id)
    ON DELETE CASCADE;

-- =====================================================================
-- STEP 7: Drop symbols table (EOD data layer - not needed)
-- =====================================================================
-- Now safe to drop - all chart data migrated to market_symbols
DROP TABLE IF EXISTS public.symbols CASCADE;

-- =====================================================================
-- STEP 5: Update table comment to reflect correct architecture
-- =====================================================================
COMMENT ON TABLE public.current_prices IS
    'Current market prices (snapshot table, updated every 60s by PriceFetcher). '
    'References market_symbols table (DJI, DAX, NDX, EUR/USD, EUR/GBP, GBP/USD). '
    'PriceFetcher normalizes API symbols (^DJI → DJI) before lookup.';

COMMENT ON COLUMN public.current_prices.symbol_id IS
    'Reference to market_symbols.id (Active Trading Assets: DJI, DAX, NDX, EUR/USD, etc.)';

COMMIT;

-- =====================================================================
-- VERIFICATION
-- =====================================================================
-- Run this after migration:
-- SELECT constraint_name, table_name
-- FROM information_schema.table_constraints
-- WHERE constraint_name = 'current_prices_symbol_id_fkey';
--
-- Should show: current_prices → market_symbols (not symbols)
--
-- Verify price_cache deleted:
-- SELECT table_name FROM information_schema.tables WHERE table_name = 'price_cache';
-- Should return 0 rows
-- =====================================================================
