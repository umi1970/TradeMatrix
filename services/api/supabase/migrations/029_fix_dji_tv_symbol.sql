-- Migration 029: Fix Dow Jones tv_symbol for FREE TradingView widgets
-- Created: 2025-11-07
-- Problem: TVC:DJI only available in PAID TradingView widget plans
--          We have FREE plan, need alternative symbol
-- Solution: OANDA:US30USD (CFD proxy for Dow Jones - works in FREE plan!)
-- =====================================================================

UPDATE public.market_symbols SET tv_symbol = 'OANDA:US30USD' WHERE symbol = 'DJI';

-- Verification
SELECT symbol, tv_symbol
FROM public.market_symbols
WHERE symbol = 'DJI';
