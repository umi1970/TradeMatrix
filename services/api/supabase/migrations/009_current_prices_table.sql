-- ================================================
-- Migration 009: Current Prices Table
-- ================================================
-- Purpose: Add table for real-time current market prices
-- Created: 2025-10-29
-- Author: TradeMatrix.ai Development Team
-- ================================================

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ================================================
-- TABLE: current_prices
-- ================================================
-- Stores latest/current prices for quick access (snapshot table)
-- Updated every minute by Celery worker
CREATE TABLE IF NOT EXISTS current_prices (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  symbol_id UUID NOT NULL REFERENCES market_symbols(id) ON DELETE CASCADE,

  -- Current price data
  price NUMERIC NOT NULL,
  open NUMERIC,
  high NUMERIC,
  low NUMERIC,
  previous_close NUMERIC,

  -- Change metrics
  change NUMERIC,
  change_percent NUMERIC,

  -- Volume
  volume BIGINT DEFAULT 0,

  -- Metadata
  exchange TEXT,
  currency TEXT DEFAULT 'USD',
  is_market_open BOOLEAN DEFAULT false,

  -- Timestamps
  price_timestamp TIMESTAMPTZ,
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  created_at TIMESTAMPTZ DEFAULT NOW(),

  -- Ensure only one current price per symbol
  UNIQUE(symbol_id),

  -- Validation
  CHECK (price > 0)
);

-- Indexes for fast queries
CREATE INDEX idx_current_prices_symbol_id ON current_prices(symbol_id);
CREATE INDEX idx_current_prices_updated_at ON current_prices(updated_at DESC);
CREATE INDEX idx_current_prices_market_open ON current_prices(is_market_open) WHERE is_market_open = true;

-- ================================================
-- TRIGGER: Auto-update timestamps
-- ================================================

DROP TRIGGER IF EXISTS update_current_prices_updated_at ON current_prices;
CREATE TRIGGER update_current_prices_updated_at
  BEFORE UPDATE ON current_prices
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- ================================================
-- VIEW: current_prices_with_symbols
-- ================================================
-- Convenient view that joins current_prices with symbol names
CREATE OR REPLACE VIEW current_prices_with_symbols AS
SELECT
  cp.id,
  cp.symbol_id,
  ms.symbol,
  ms.alias as symbol_name,
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
JOIN market_symbols ms ON cp.symbol_id = ms.id
WHERE ms.active = true;

-- ================================================
-- COMMENTS
-- ================================================

COMMENT ON TABLE current_prices IS 'Current/latest market prices (snapshot table, updated every minute)';
COMMENT ON COLUMN current_prices.price IS 'Current market price';
COMMENT ON COLUMN current_prices.change IS 'Absolute price change from previous close';
COMMENT ON COLUMN current_prices.change_percent IS 'Percentage price change from previous close';
COMMENT ON COLUMN current_prices.is_market_open IS 'Is the market currently open for trading?';
COMMENT ON COLUMN current_prices.price_timestamp IS 'Timestamp when price was fetched from exchange';

-- ================================================
-- END OF MIGRATION 009
-- ================================================
