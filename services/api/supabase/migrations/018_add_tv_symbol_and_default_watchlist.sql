-- Migration 018: Add tv_symbol column to symbols table + default watchlist function
-- Created: 2025-11-03
-- Purpose: Support TradingView widgets with proper symbol format

-- ============================================================================
-- 1. Add tv_symbol column to symbols table
-- ============================================================================

ALTER TABLE public.symbols
ADD COLUMN IF NOT EXISTS tv_symbol TEXT;

COMMENT ON COLUMN public.symbols.tv_symbol IS 'TradingView widget symbol format (e.g., "XETR:DAX", "FX:EURUSD")';

-- ============================================================================
-- 2. Update existing symbols with TradingView format
-- ============================================================================

-- Indices
UPDATE public.symbols SET tv_symbol = 'XETR:DAX' WHERE symbol = '^GDAXI';
UPDATE public.symbols SET tv_symbol = 'NASDAQ:NDX' WHERE symbol = '^NDX';
UPDATE public.symbols SET tv_symbol = 'DJ:DJI' WHERE symbol = '^DJI';

-- Forex
UPDATE public.symbols SET tv_symbol = 'FX:EURUSD' WHERE symbol = 'EURUSD';
UPDATE public.symbols SET tv_symbol = 'FX:EURGBP' WHERE symbol = 'EURGBP';
UPDATE public.symbols SET tv_symbol = 'FX:GBPUSD' WHERE symbol = 'GBPUSD';

-- ============================================================================
-- 3. Create default watchlist function
-- ============================================================================

CREATE OR REPLACE FUNCTION public.create_default_watchlist(p_user_id UUID)
RETURNS VOID AS $$
DECLARE
  v_symbols UUID[];
BEGIN
  -- Get top 5 most popular symbols (DAX, NASDAQ, DOW, EURUSD, EURGBP)
  SELECT ARRAY_AGG(id ORDER BY symbol)
  INTO v_symbols
  FROM public.symbols
  WHERE symbol IN ('^GDAXI', '^NDX', '^DJI', 'EURUSD', 'EURGBP')
  LIMIT 5;

  -- Insert default watchlist (positions 1-5)
  INSERT INTO public.user_watchlist (user_id, symbol_id, position)
  SELECT p_user_id, symbol_id, ROW_NUMBER() OVER ()
  FROM UNNEST(v_symbols) AS symbol_id
  ON CONFLICT (user_id, symbol_id) DO NOTHING;

  RAISE NOTICE 'Default watchlist created for user %', p_user_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION public.create_default_watchlist IS 'Initialize new user with 5 default symbols (DAX, NASDAQ, DOW, EURUSD, EURGBP)';

-- ============================================================================
-- 4. Verify migration
-- ============================================================================

-- Check tv_symbol column exists
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public'
      AND table_name = 'symbols'
      AND column_name = 'tv_symbol'
  ) THEN
    RAISE NOTICE '✅ Column tv_symbol added successfully';
  ELSE
    RAISE EXCEPTION '❌ Column tv_symbol not found!';
  END IF;
END $$;

-- Check if symbols were updated
DO $$
DECLARE
  v_count INT;
BEGIN
  SELECT COUNT(*) INTO v_count
  FROM public.symbols
  WHERE tv_symbol IS NOT NULL;

  IF v_count >= 6 THEN
    RAISE NOTICE '✅ % symbols updated with tv_symbol values', v_count;
  ELSE
    RAISE WARNING '⚠️ Only % symbols have tv_symbol values', v_count;
  END IF;
END $$;

-- Check if function exists
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM pg_proc
    WHERE proname = 'create_default_watchlist'
  ) THEN
    RAISE NOTICE '✅ Function create_default_watchlist created successfully';
  ELSE
    RAISE EXCEPTION '❌ Function create_default_watchlist not found!';
  END IF;
END $$;

RAISE NOTICE '🚀 Migration 018 completed successfully!';
