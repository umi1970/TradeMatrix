-- Migration 028: Add api_symbol to market_symbols
-- Created: 2025-11-12
-- Problem: OHLC Fetcher has hardcoded symbol mappings (DAX→^GDAXI, EUR/USD→EUR/USD)
--          This is inflexible and violates schema-first architecture
-- Solution: Add api_symbol column to store provider-specific symbol format
-- =====================================================================

-- Add api_symbol column to market_symbols
ALTER TABLE public.market_symbols
    ADD COLUMN IF NOT EXISTS api_symbol TEXT;

COMMENT ON COLUMN public.market_symbols.api_symbol IS
    'API-specific symbol format for data fetching (e.g., "^GDAXI" for yfinance, "EUR/USD" for twelvedata)';

-- Populate api_symbol for existing symbols
-- yfinance symbols (indices)
UPDATE public.market_symbols SET api_symbol = '^GDAXI' WHERE symbol = 'DAX';
UPDATE public.market_symbols SET api_symbol = '^NDX' WHERE symbol = 'NDX';
UPDATE public.market_symbols SET api_symbol = '^DJI' WHERE symbol = 'DJI';

-- Twelvedata symbols (forex - keep slash format)
UPDATE public.market_symbols SET api_symbol = 'EUR/USD' WHERE symbol = 'EUR/USD';
UPDATE public.market_symbols SET api_symbol = 'EUR/GBP' WHERE symbol = 'EUR/GBP';
UPDATE public.market_symbols SET api_symbol = 'GBP/USD' WHERE symbol = 'GBP/USD';
UPDATE public.market_symbols SET api_symbol = 'XAG/USD' WHERE symbol = 'XAG/USD';

-- Deactivate invalid/duplicate symbols
UPDATE public.market_symbols
SET active = false
WHERE symbol IN (
    'UNKNOWN',                      -- Placeholder
    'DJIUSD',                       -- Duplicate of DJI
    'EURUSD',                       -- Duplicate of EUR/USD (wrong format)
    '1762880625185_IG_NASDAQ',      -- IG Broker ID (not a symbol)
    'US Tech 100 Cash (S100)',      -- Broker display name
    'NASDAQ'                        -- Ambiguous (IXIC vs NDX)
);

-- =====================================================================
-- Verification
-- =====================================================================

DO $$
DECLARE
  v_count INTEGER;
  v_inactive INTEGER;
BEGIN
  -- Check column exists
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public'
      AND table_name = 'market_symbols'
      AND column_name = 'api_symbol'
  ) THEN
    RAISE NOTICE '✅ Column api_symbol added successfully';
  ELSE
    RAISE EXCEPTION '❌ Column api_symbol not found!';
  END IF;

  -- Check values populated
  SELECT COUNT(*) INTO v_count
  FROM public.market_symbols
  WHERE api_symbol IS NOT NULL;

  IF v_count >= 5 THEN
    RAISE NOTICE '✅ % symbols updated with api_symbol values', v_count;
  ELSE
    RAISE WARNING '⚠️ Only % symbols have api_symbol values', v_count;
  END IF;

  -- Check invalid symbols deactivated
  SELECT COUNT(*) INTO v_inactive
  FROM public.market_symbols
  WHERE active = false
    AND symbol IN ('UNKNOWN', 'DJIUSD', 'EURUSD', '1762880625185_IG_NASDAQ', 'US Tech 100 Cash (S100)', 'NASDAQ');

  IF v_inactive >= 5 THEN
    RAISE NOTICE '✅ % invalid symbols deactivated', v_inactive;
  ELSE
    RAISE WARNING '⚠️ Only % invalid symbols deactivated', v_inactive;
  END IF;
END $$;
