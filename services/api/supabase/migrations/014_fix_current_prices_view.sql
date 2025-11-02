-- ================================================
-- Migration 014: Fix current_prices_with_symbols View
-- ================================================
-- Purpose: Update view to use 'symbols' table instead of 'market_symbols'
-- Created: 2025-11-02
-- Author: TradeMatrix.ai Development Team
-- ================================================

-- Drop the old view
DROP VIEW IF EXISTS current_prices_with_symbols;

-- Recreate view using the 'symbols' table
CREATE OR REPLACE VIEW current_prices_with_symbols AS
SELECT
  cp.id,
  cp.symbol_id,
  s.symbol,
  s.name as symbol_name,
  cp.price,
  cp.open,
  cp.high,
  cp.low,
  cp.previous_close,
  cp.change,
  cp.change_percent,
  cp.volume,
  cp.exchange,
  cp.currency,
  cp.is_market_open,
  cp.price_timestamp,
  cp.updated_at
FROM current_prices cp
JOIN symbols s ON cp.symbol_id = s.id
WHERE s.is_active = true;

COMMENT ON VIEW current_prices_with_symbols IS 'Current prices joined with symbol information (using symbols table)';

-- ================================================
-- END OF MIGRATION 014
-- ================================================
