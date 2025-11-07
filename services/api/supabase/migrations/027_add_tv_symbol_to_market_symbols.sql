-- Migration 027: Add tv_symbol to market_symbols
-- Created: 2025-11-07
-- Problem: Migration 024 deleted symbols table but forgot to migrate tv_symbol column
--          Dashboard watchlist needs tv_symbol for TradingView widgets
-- =====================================================================

-- Add tv_symbol column to market_symbols
ALTER TABLE public.market_symbols
    ADD COLUMN IF NOT EXISTS tv_symbol TEXT;

COMMENT ON COLUMN public.market_symbols.tv_symbol IS
    'TradingView widget symbol format (e.g., "XETR:DAX", "FX:EURUSD", "NASDAQ:NDX")';

-- Populate tv_symbol for existing symbols
UPDATE public.market_symbols SET tv_symbol = 'XETR:DAX' WHERE symbol = 'DAX';
UPDATE public.market_symbols SET tv_symbol = 'NASDAQ:NDX' WHERE symbol = 'NDX';
UPDATE public.market_symbols SET tv_symbol = 'DJ:DJI' WHERE symbol = 'DJI';
UPDATE public.market_symbols SET tv_symbol = 'FX:EURUSD' WHERE symbol = 'EUR/USD';
UPDATE public.market_symbols SET tv_symbol = 'FX:EURGBP' WHERE symbol = 'EUR/GBP';
UPDATE public.market_symbols SET tv_symbol = 'FX:GBPUSD' WHERE symbol = 'GBP/USD';

-- =====================================================================
-- Verification
-- =====================================================================

DO $$
DECLARE
  v_count INTEGER;
BEGIN
  -- Check column exists
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public'
      AND table_name = 'market_symbols'
      AND column_name = 'tv_symbol'
  ) THEN
    RAISE NOTICE '✅ Column tv_symbol added successfully';
  ELSE
    RAISE EXCEPTION '❌ Column tv_symbol not found!';
  END IF;

  -- Check values populated
  SELECT COUNT(*) INTO v_count
  FROM public.market_symbols
  WHERE tv_symbol IS NOT NULL;

  IF v_count >= 5 THEN
    RAISE NOTICE '✅ % symbols updated with tv_symbol values', v_count;
  ELSE
    RAISE WARNING '⚠️ Only % symbols have tv_symbol values', v_count;
  END IF;
END $$;
