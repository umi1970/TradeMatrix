-- Migration 028: Fix eod_levels FK to reference market_symbols
-- Created: 2025-11-07
-- Problem: eod_levels still references deleted 'symbols' table
--          Dashboard cards fail with "Could not find relationship" error
-- =====================================================================

BEGIN;

-- Drop old FK to symbols (if it still exists)
ALTER TABLE public.eod_levels
    DROP CONSTRAINT IF EXISTS eod_levels_symbol_id_fkey;

-- Delete orphaned records (symbol_id not in market_symbols)
-- These are old records pointing to deleted symbols table
DELETE FROM public.eod_levels
WHERE symbol_id NOT IN (SELECT id FROM public.market_symbols);

-- Add new FK to market_symbols
ALTER TABLE public.eod_levels
    ADD CONSTRAINT eod_levels_symbol_id_fkey
    FOREIGN KEY (symbol_id)
    REFERENCES public.market_symbols(id)
    ON DELETE CASCADE;

-- Update comment
COMMENT ON COLUMN public.eod_levels.symbol_id IS
    'Reference to market_symbols.id (Active Trading Assets: DAX, NDX, DJI, EUR/USD, etc.)';

COMMIT;

-- =====================================================================
-- Verification
-- =====================================================================

DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.table_constraints
    WHERE constraint_name = 'eod_levels_symbol_id_fkey'
      AND table_name = 'eod_levels'
  ) THEN
    RAISE NOTICE '✅ eod_levels FK updated to reference market_symbols';
  ELSE
    RAISE EXCEPTION '❌ eod_levels FK not found!';
  END IF;
END $$;
