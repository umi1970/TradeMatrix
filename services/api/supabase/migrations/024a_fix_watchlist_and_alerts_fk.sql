-- =====================================================================
-- Migration: 024a_fix_watchlist_and_alerts_fk.sql
-- Description: Fix missing FK updates for user_watchlist and alert_subscriptions
-- Created: 2025-11-07
-- Reason: Migration 024 forgot to update these 2 tables - they still reference symbols
--         symbols table was already deleted by Migration 024, so we can't migrate data
--         Solution: Delete orphaned records, update FK constraints
-- =====================================================================

BEGIN;

-- =====================================================================
-- STEP 1: Fix user_watchlist FK (symbols → market_symbols)
-- =====================================================================

-- symbols table no longer exists (deleted in Migration 024)
-- Delete all orphaned records (symbol_id points to deleted symbols)
DELETE FROM public.user_watchlist
WHERE symbol_id NOT IN (SELECT id FROM public.market_symbols);

-- Drop old FK to symbols (if it still exists)
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

-- Delete all orphaned records (symbol_id points to deleted symbols)
DELETE FROM public.alert_subscriptions
WHERE symbol_id NOT IN (SELECT id FROM public.market_symbols);

-- Drop old FK to symbols (if it still exists)
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
