-- Migration 016: Allow 'twelvedata' in price_cache.data_source
-- Date: 2025-11-03

-- Drop old constraint
ALTER TABLE public.price_cache DROP CONSTRAINT IF EXISTS price_cache_data_source_check;

-- Add new constraint with 'twelvedata' included
ALTER TABLE public.price_cache
ADD CONSTRAINT price_cache_data_source_check
CHECK (data_source IN ('finnhub', 'alpha_vantage', 'twelvedata', 'yfinance', 'manual'));

-- Comment
COMMENT ON CONSTRAINT price_cache_data_source_check ON public.price_cache IS 'Allowed data sources: finnhub, alpha_vantage, twelvedata, yfinance, manual';
