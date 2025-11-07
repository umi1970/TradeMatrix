-- =====================================================================
-- Migration: 022_fix_chart_snapshots_fk.sql
-- Description: Fix chart_snapshots foreign key to reference market_symbols
-- Created: 2025-11-06
-- Session: Phase 4 Restart - Correct Schema Fix
--
-- Context:
--   Migration 013 created chart_snapshots with FK to symbols.id
--   BUT: All AI Agents use market_symbols table (not symbols)
--   FIX: Change FK to reference market_symbols.id
--
-- Architecture Decision:
--   - market_symbols = PRIMARY table for AI Agents (DAX, NDX, EUR/USD)
--   - symbols = EOD Data Layer only (^GDAXI, ^NDX, EURUSD)
--   - chart_snapshots is used by Agents → must reference market_symbols
--
-- Rollback Instructions:
--   -- Revert FK back to symbols
--   ALTER TABLE public.chart_snapshots
--     DROP CONSTRAINT IF EXISTS chart_snapshots_symbol_id_fkey;
--   ALTER TABLE public.chart_snapshots
--     ADD CONSTRAINT chart_snapshots_symbol_id_fkey
--     FOREIGN KEY (symbol_id) REFERENCES public.symbols(id) ON DELETE CASCADE;
-- =====================================================================

BEGIN;

-- =====================================================================
-- SAFETY CHECK: Verify table exists
-- =====================================================================
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_name = 'chart_snapshots'
    ) THEN
        RAISE EXCEPTION 'Table chart_snapshots does not exist. Run migration 013 first.';
    END IF;
END $$;

-- =====================================================================
-- CHECK: Any existing data?
-- =====================================================================
DO $$
DECLARE
    record_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO record_count FROM public.chart_snapshots;

    IF record_count > 0 THEN
        RAISE NOTICE 'WARNING: chart_snapshots has % existing records', record_count;
        RAISE NOTICE 'These records may become orphaned if symbol_id does not exist in market_symbols';
    ELSE
        RAISE NOTICE 'chart_snapshots is empty - safe to modify FK';
    END IF;
END $$;

-- =====================================================================
-- STEP 1: Drop existing FK constraint (if exists)
-- =====================================================================
DO $$
BEGIN
    ALTER TABLE public.chart_snapshots
        DROP CONSTRAINT IF EXISTS chart_snapshots_symbol_id_fkey;

    RAISE NOTICE 'Dropped old FK constraint (if it existed)';
END $$;

-- =====================================================================
-- STEP 2: Add new FK constraint to market_symbols
-- =====================================================================
DO $$
BEGIN
    ALTER TABLE public.chart_snapshots
        ADD CONSTRAINT chart_snapshots_symbol_id_fkey
        FOREIGN KEY (symbol_id)
        REFERENCES public.market_symbols(id)
        ON DELETE CASCADE;

    RAISE NOTICE 'Added new FK constraint: chart_snapshots.symbol_id → market_symbols.id';
END $$;

-- =====================================================================
-- STEP 3: Update table comment
-- =====================================================================
COMMENT ON TABLE public.chart_snapshots IS
    'Stores generated chart snapshots from chart-img.com API. '
    'References market_symbols (used by AI Agents). '
    '60-day retention period.';

COMMENT ON COLUMN public.chart_snapshots.symbol_id IS
    'Reference to market_symbols.id (PRIMARY agent table: DAX, NDX, EUR/USD)';

-- =====================================================================
-- VERIFICATION: Check FK constraint
-- =====================================================================
DO $$
DECLARE
    fk_exists BOOLEAN;
BEGIN
    SELECT EXISTS (
        SELECT 1
        FROM information_schema.table_constraints tc
        JOIN information_schema.constraint_column_usage ccu
            ON tc.constraint_name = ccu.constraint_name
        WHERE tc.table_schema = 'public'
            AND tc.table_name = 'chart_snapshots'
            AND tc.constraint_type = 'FOREIGN KEY'
            AND ccu.table_name = 'market_symbols'
    ) INTO fk_exists;

    IF fk_exists THEN
        RAISE NOTICE '✅ FK constraint verified: chart_snapshots → market_symbols';
    ELSE
        RAISE EXCEPTION '❌ FK constraint NOT found! Migration failed.';
    END IF;
END $$;

COMMIT;

-- =====================================================================
-- MIGRATION COMPLETE
-- =====================================================================
-- Summary:
-- ✅ chart_snapshots.symbol_id now references market_symbols.id
-- ✅ All AI Agents (ChartWatcher, MorningPlanner, etc.) compatible
-- ✅ Backward compatibility: ChartService SYMBOL_MAPPING supports both formats
--
-- Next Steps:
-- 1. Verify agents can generate charts
-- 2. Test ChartWatcher execution
-- 3. Check chart_snapshots inserts work correctly
-- =====================================================================
