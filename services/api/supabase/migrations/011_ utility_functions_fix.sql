-- ============================================================
-- TradeMatrix.ai - Utility Functions Fix
-- Purpose: Add missing utility functions for symbols table
-- Version: 1.0.0
-- Run this if functions are missing after COMPLETE migration
-- ============================================================

-- ============================================================
-- 1. GET ACTIVE SYMBOLS FUNCTION
-- ============================================================

CREATE OR REPLACE FUNCTION get_active_symbols()
RETURNS TABLE (
    symbol VARCHAR,
    name VARCHAR,
    type VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT s.symbol, s.name, s.type
    FROM public.symbols s
    WHERE s.is_active = TRUE
    ORDER BY s.type, s.symbol;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION get_active_symbols IS 'Returns all active symbols for data fetching';


-- ============================================================
-- 2. GET SYMBOL BY NAME FUNCTION
-- ============================================================

CREATE OR REPLACE FUNCTION get_symbol_by_name(symbol_name VARCHAR)
RETURNS TABLE (
    id UUID,
    symbol VARCHAR,
    name VARCHAR,
    type VARCHAR,
    stooq_symbol VARCHAR,
    yahoo_symbol VARCHAR,
    eodhd_symbol VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        s.id,
        s.symbol,
        s.name,
        s.type,
        s.stooq_symbol,
        s.yahoo_symbol,
        s.eodhd_symbol
    FROM public.symbols s
    WHERE s.symbol = symbol_name
    LIMIT 1;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION get_symbol_by_name IS 'Returns symbol details by symbol name';


-- ============================================================
-- 3. GET SYMBOL ID FUNCTION
-- ============================================================
-- Helper function to easily get symbol UUID by name

CREATE OR REPLACE FUNCTION get_symbol_id(symbol_name VARCHAR)
RETURNS UUID AS $$
DECLARE
    symbol_uuid UUID;
BEGIN
    SELECT id INTO symbol_uuid
    FROM public.symbols
    WHERE symbol = symbol_name
    LIMIT 1;
    
    RETURN symbol_uuid;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION get_symbol_id IS 'Returns UUID for a given symbol name';


-- ============================================================
-- 4. GET ALL SYMBOLS WITH DETAILS FUNCTION
-- ============================================================

CREATE OR REPLACE FUNCTION get_all_symbols()
RETURNS TABLE (
    id UUID,
    symbol VARCHAR,
    name VARCHAR,
    type VARCHAR,
    is_active BOOLEAN,
    is_tradeable BOOLEAN,
    stooq_symbol VARCHAR,
    yahoo_symbol VARCHAR,
    eodhd_symbol VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        s.id,
        s.symbol,
        s.name,
        s.type,
        s.is_active,
        s.is_tradeable,
        s.stooq_symbol,
        s.yahoo_symbol,
        s.eodhd_symbol
    FROM public.symbols s
    ORDER BY s.type, s.symbol;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION get_all_symbols IS 'Returns all symbols with full details';


-- ============================================================
-- 5. VERIFICATION
-- ============================================================

-- Test all functions
DO $$
BEGIN
    RAISE NOTICE 'Testing utility functions...';
    
    -- Test 1: get_active_symbols
    IF EXISTS (SELECT * FROM get_active_symbols()) THEN
        RAISE NOTICE '✓ get_active_symbols() - Working';
    ELSE
        RAISE WARNING '✗ get_active_symbols() - No results';
    END IF;
    
    -- Test 2: get_symbol_by_name
    IF EXISTS (SELECT * FROM get_symbol_by_name('^GDAXI')) THEN
        RAISE NOTICE '✓ get_symbol_by_name() - Working';
    ELSE
        RAISE WARNING '✗ get_symbol_by_name() - No results';
    END IF;
    
    -- Test 3: get_symbol_id
    IF get_symbol_id('^GDAXI') IS NOT NULL THEN
        RAISE NOTICE '✓ get_symbol_id() - Working';
    ELSE
        RAISE WARNING '✗ get_symbol_id() - No results';
    END IF;
    
    RAISE NOTICE 'All utility functions created successfully!';
END $$;

-- Display function list
SELECT 
    routine_name as function_name,
    routine_type as type
FROM information_schema.routines
WHERE routine_schema = 'public'
  AND routine_name LIKE 'get_%'
ORDER BY routine_name;


-- ============================================================
-- FIX COMPLETE!
-- ============================================================
-- Run these test queries to verify:
--
-- SELECT * FROM get_active_symbols();
-- SELECT * FROM get_symbol_by_name('^GDAXI');
-- SELECT get_symbol_id('^GDAXI');
-- SELECT * FROM get_all_symbols();
-- ============================================================
