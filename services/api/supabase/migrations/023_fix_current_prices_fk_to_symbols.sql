-- =====================================================================
-- Migration: 023_fix_current_prices_fk_to_symbols.sql
-- Description: Fix FK constraint - current_prices should reference symbols, not market_symbols
-- Created: 2025-11-07
-- Reason: Architecture fix - PriceFetcher uses symbols table (^DJI, ^GDAXI, ^NDX)
--         but current_prices FK pointed to market_symbols (DJI, DAX, NDX)
-- =====================================================================

BEGIN;

-- =====================================================================
-- STEP 1: Drop existing FK constraint to market_symbols
-- =====================================================================
ALTER TABLE public.current_prices
    DROP CONSTRAINT IF EXISTS current_prices_symbol_id_fkey;

-- =====================================================================
-- STEP 2: Add new FK constraint to symbols
-- =====================================================================
ALTER TABLE public.current_prices
    ADD CONSTRAINT current_prices_symbol_id_fkey
    FOREIGN KEY (symbol_id)
    REFERENCES public.symbols(id)
    ON DELETE CASCADE;

-- =====================================================================
-- STEP 3: Update table comment
-- =====================================================================
COMMENT ON TABLE public.current_prices IS
    'Current market prices (snapshot table, updated every 60s by PriceFetcher). '
    'References symbols table (^DJI, ^GDAXI, ^NDX, EURUSD, EURGBP, GBPUSD).';

COMMENT ON COLUMN public.current_prices.symbol_id IS
    'Reference to symbols.id (EOD Data Layer: ^GDAXI, ^DJI, ^NDX)';

COMMIT;

-- =====================================================================
-- VERIFICATION
-- =====================================================================
-- Run this after migration:
-- SELECT constraint_name, table_name
-- FROM information_schema.table_constraints
-- WHERE constraint_name = 'current_prices_symbol_id_fkey';
--
-- Should show: current_prices → symbols (not market_symbols)
-- =====================================================================
