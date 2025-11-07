-- =====================================================================
-- Migration: 024a_fix_watchlist_and_alerts_fk.sql
-- Description: Fix missing FK updates for user_watchlist and alert_subscriptions
-- Created: 2025-11-07
-- Reason: Migration 024 forgot to update these 2 tables - they still reference symbols
-- =====================================================================

BEGIN;

-- =====================================================================
-- STEP 1: Fix user_watchlist FK (symbols → market_symbols)
-- =====================================================================

-- First, migrate existing records to point to market_symbols
UPDATE public.user_watchlist uw
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
WHERE uw.symbol_id = s.id;

-- Drop old FK to symbols
ALTER TABLE public.user_watchlist
    DROP CONSTRAINT IF EXISTS user_watchlist_symbol_id_fkey;

-- Add new FK to market_symbols
ALTER TABLE public.user_watchlist
    ADD CONSTRAINT user_watchlist_symbol_id_fkey
    FOREIGN KEY (symbol_id)
    REFERENCES public.market_symbols(id)
    ON DELETE CASCADE;

-- =====================================================================
-- STEP 2: Fix alert_subscriptions FK (symbols → market_symbols)
-- =====================================================================

-- First, migrate existing records to point to market_symbols
UPDATE public.alert_subscriptions asub
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
WHERE asub.symbol_id = s.id;

-- Drop old FK to symbols
ALTER TABLE public.alert_subscriptions
    DROP CONSTRAINT IF EXISTS alert_subscriptions_symbol_id_fkey;

-- Add new FK to market_symbols
ALTER TABLE public.alert_subscriptions
    ADD CONSTRAINT alert_subscriptions_symbol_id_fkey
    FOREIGN KEY (symbol_id)
    REFERENCES public.market_symbols(id)
    ON DELETE CASCADE;

-- =====================================================================
-- STEP 3: Update comments
-- =====================================================================

COMMENT ON COLUMN public.user_watchlist.symbol_id IS
    'Reference to market_symbols.id (Active Trading Assets: DAX, NDX, DJI, EUR/USD, etc.)';

COMMENT ON COLUMN public.alert_subscriptions.symbol_id IS
    'Reference to market_symbols.id (Active Trading Assets: DAX, NDX, DJI, EUR/USD, etc.)';

COMMIT;

-- =====================================================================
-- VERIFICATION
-- =====================================================================
-- Run after migration:
--
-- SELECT constraint_name, table_name
-- FROM information_schema.table_constraints
-- WHERE constraint_name IN ('user_watchlist_symbol_id_fkey', 'alert_subscriptions_symbol_id_fkey');
--
-- Should show both pointing to market_symbols
-- =====================================================================
