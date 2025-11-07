-- Migration 026: Fix create_default_watchlist() to use market_symbols
-- Created: 2025-11-07
-- Problem: Function still references old 'symbols' table (deleted in Migration 024)
--          Should use 'market_symbols' instead
-- =====================================================================

-- Drop old function
DROP FUNCTION IF EXISTS public.create_default_watchlist(UUID);

-- Recreate with correct table reference
CREATE OR REPLACE FUNCTION public.create_default_watchlist(p_user_id UUID)
RETURNS VOID AS $$
DECLARE
  v_symbols UUID[];
BEGIN
  -- Get top 5 market symbols (DAX, NDX, DJI, EUR/USD, EUR/GBP)
  SELECT ARRAY_AGG(id ORDER BY symbol)
  INTO v_symbols
  FROM public.market_symbols
  WHERE symbol IN ('DAX', 'NDX', 'DJI', 'EUR/USD', 'EUR/GBP')
    AND active = TRUE
  LIMIT 5;

  -- Insert default watchlist (positions 1-5)
  IF v_symbols IS NOT NULL AND ARRAY_LENGTH(v_symbols, 1) > 0 THEN
    INSERT INTO public.user_watchlist (user_id, symbol_id, position)
    SELECT p_user_id, symbol_id, ROW_NUMBER() OVER ()
    FROM UNNEST(v_symbols) AS symbol_id
    ON CONFLICT (user_id, symbol_id) DO NOTHING;

    RAISE NOTICE 'Default watchlist created for user % (% symbols)', p_user_id, ARRAY_LENGTH(v_symbols, 1);
  ELSE
    RAISE WARNING 'No active market symbols found - cannot create default watchlist for user %', p_user_id;
  END IF;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION public.create_default_watchlist IS
  'Initialize new user with 5 default market symbols (DAX, NDX, DJI, EUR/USD, EUR/GBP) from market_symbols table';

-- =====================================================================
-- Verification
-- =====================================================================

DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM pg_proc
    WHERE proname = 'create_default_watchlist'
  ) THEN
    RAISE NOTICE '✅ Function create_default_watchlist() updated successfully (now uses market_symbols)';
  ELSE
    RAISE EXCEPTION '❌ Function create_default_watchlist() not found!';
  END IF;
END $$;
