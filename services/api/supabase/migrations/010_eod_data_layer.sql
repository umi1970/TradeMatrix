-- ============================================================
-- TradeMatrix.ai - Complete EOD Data Layer Setup
-- Purpose: Full database setup including symbols table
-- Version: 1.0.1 (includes symbols table creation)
-- ============================================================

-- ============================================================
-- 1. SYMBOLS TABLE (Core dependency)
-- ============================================================
-- This table must exist first as it's referenced by EOD tables

CREATE TABLE IF NOT EXISTS public.symbols (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    symbol VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(20) NOT NULL, -- 'index', 'forex', 'stock', 'crypto'
    exchange VARCHAR(50),
    currency VARCHAR(10) DEFAULT 'USD',
    
    -- Trading configuration
    is_active BOOLEAN DEFAULT TRUE,
    is_tradeable BOOLEAN DEFAULT TRUE,
    
    -- Data source mappings
    stooq_symbol VARCHAR(20),
    yahoo_symbol VARCHAR(20),
    eodhd_symbol VARCHAR(20),
    
    -- Metadata
    description TEXT,
    timezone VARCHAR(50) DEFAULT 'UTC',
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_symbols_symbol ON public.symbols(symbol);
CREATE INDEX IF NOT EXISTS idx_symbols_type ON public.symbols(type);
CREATE INDEX IF NOT EXISTS idx_symbols_is_active ON public.symbols(is_active);

-- Auto-update timestamp trigger
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_symbols_updated_at
    BEFORE UPDATE ON public.symbols
    FOR EACH ROW
    EXECUTE FUNCTION update_timestamp();

COMMENT ON TABLE public.symbols IS 'Market symbols tracked by TradeMatrix';


-- ============================================================
-- 2. INSERT DEFAULT SYMBOLS
-- ============================================================
-- Insert the symbols configured in eod_data_config.yaml

INSERT INTO public.symbols (symbol, name, type, stooq_symbol, yahoo_symbol, eodhd_symbol, is_active, is_tradeable)
VALUES
    ('^GDAXI', 'DAX 40', 'index', '^dax', '^GDAXI', 'DE30.EUR', TRUE, TRUE),
    ('^NDX', 'NASDAQ 100', 'index', '^ndq', '^NDX', 'NDX.INDX', TRUE, TRUE),
    ('^DJI', 'Dow Jones Industrial', 'index', '^dji', '^DJI', 'DJI.INDX', TRUE, TRUE),
    ('EURUSD', 'EUR/USD', 'forex', 'eurusd', 'EURUSD=X', 'EURUSD.FOREX', TRUE, TRUE),
    ('GBPUSD', 'GBP/USD', 'forex', 'gbpusd', 'GBPUSD=X', 'GBPUSD.FOREX', TRUE, FALSE)
ON CONFLICT (symbol) DO NOTHING;


-- ============================================================
-- 3. EOD DATA TABLE
-- ============================================================
-- Stores daily OHLCV data for all tracked symbols
-- One row per symbol per trading day

CREATE TABLE IF NOT EXISTS public.eod_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    symbol_id UUID NOT NULL REFERENCES public.symbols(id) ON DELETE CASCADE,
    trade_date DATE NOT NULL,
    
    -- OHLCV Data
    open DECIMAL(12, 4) NOT NULL,
    high DECIMAL(12, 4) NOT NULL,
    low DECIMAL(12, 4) NOT NULL,
    close DECIMAL(12, 4) NOT NULL,
    volume BIGINT,
    
    -- Metadata
    data_source VARCHAR(50) NOT NULL,  -- 'stooq', 'yahoo', 'eodhd'
    retrieved_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    quality_score DECIMAL(3, 2),  -- 0.00 - 1.00
    is_validated BOOLEAN DEFAULT FALSE,
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT eod_data_symbol_date_unique UNIQUE (symbol_id, trade_date),
    CONSTRAINT eod_data_ohlc_valid CHECK (
        low <= open AND low <= close AND
        high >= open AND high >= close
    )
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_eod_data_symbol_id ON public.eod_data(symbol_id);
CREATE INDEX IF NOT EXISTS idx_eod_data_trade_date ON public.eod_data(trade_date DESC);
CREATE INDEX IF NOT EXISTS idx_eod_data_symbol_date ON public.eod_data(symbol_id, trade_date DESC);
CREATE INDEX IF NOT EXISTS idx_eod_data_retrieved_at ON public.eod_data(retrieved_at DESC);

-- Auto-update timestamp trigger
CREATE TRIGGER trigger_eod_data_updated_at
    BEFORE UPDATE ON public.eod_data
    FOR EACH ROW
    EXECUTE FUNCTION update_timestamp();

COMMENT ON TABLE public.eod_data IS 'End-of-Day OHLCV data for all tracked symbols';
COMMENT ON COLUMN public.eod_data.quality_score IS 'Data quality score (0.00-1.00) based on cross-validation';
COMMENT ON COLUMN public.eod_data.is_validated IS 'TRUE if data passed quality checks and cross-validation';


-- ============================================================
-- 4. DERIVED LEVELS TABLE
-- ============================================================
-- Stores calculated levels (Yesterday High/Low/Close, ATR, etc.)
-- Used by MorningPlanner, USOpenPlanner, ValidationEngine

CREATE TABLE IF NOT EXISTS public.eod_levels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    symbol_id UUID NOT NULL REFERENCES public.symbols(id) ON DELETE CASCADE,
    trade_date DATE NOT NULL,
    
    -- Yesterday Levels (most important for intraday trading)
    yesterday_high DECIMAL(12, 4),
    yesterday_low DECIMAL(12, 4),
    yesterday_close DECIMAL(12, 4),
    yesterday_open DECIMAL(12, 4),
    yesterday_range DECIMAL(12, 4),  -- high - low
    
    -- Multi-Day Levels
    previous_week_high DECIMAL(12, 4),
    previous_week_low DECIMAL(12, 4),
    
    -- Volatility Metrics
    atr_5d DECIMAL(12, 4),  -- Average True Range (5 days)
    atr_20d DECIMAL(12, 4),  -- Average True Range (20 days)
    
    -- Performance Metrics
    daily_change_points DECIMAL(12, 4),  -- close - previous_close
    daily_change_percent DECIMAL(6, 2),  -- ((close - previous_close) / previous_close) * 100
    
    -- Round Numbers (psychological levels)
    nearest_round_number_above DECIMAL(12, 4),
    nearest_round_number_below DECIMAL(12, 4),
    
    -- Metadata
    calculated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    calculation_source VARCHAR(50) DEFAULT 'eod_data_layer',
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT eod_levels_symbol_date_unique UNIQUE (symbol_id, trade_date)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_eod_levels_symbol_id ON public.eod_levels(symbol_id);
CREATE INDEX IF NOT EXISTS idx_eod_levels_trade_date ON public.eod_levels(trade_date DESC);
CREATE INDEX IF NOT EXISTS idx_eod_levels_symbol_date ON public.eod_levels(symbol_id, trade_date DESC);

-- Auto-update timestamp trigger
CREATE TRIGGER trigger_eod_levels_updated_at
    BEFORE UPDATE ON public.eod_levels
    FOR EACH ROW
    EXECUTE FUNCTION update_timestamp();

COMMENT ON TABLE public.eod_levels IS 'Derived levels and metrics calculated from EOD data';
COMMENT ON COLUMN public.eod_levels.yesterday_high IS 'Previous trading day high - used by MorningPlanner';
COMMENT ON COLUMN public.eod_levels.atr_5d IS 'Average True Range over 5 days - volatility indicator';


-- ============================================================
-- 5. EOD FETCH LOG TABLE
-- ============================================================
-- Tracks all EOD data fetch attempts for monitoring and debugging

CREATE TABLE IF NOT EXISTS public.eod_fetch_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    symbol_id UUID REFERENCES public.symbols(id) ON DELETE SET NULL,
    fetch_date DATE NOT NULL,
    
    -- Fetch Details
    data_source VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,  -- 'success', 'failed', 'partial'
    
    -- Timing
    fetch_started_at TIMESTAMPTZ NOT NULL,
    fetch_completed_at TIMESTAMPTZ,
    duration_ms INTEGER,
    
    -- Results
    records_fetched INTEGER DEFAULT 0,
    records_stored INTEGER DEFAULT 0,
    
    -- Error Handling
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    
    -- Quality Metrics
    cross_validation_passed BOOLEAN,
    quality_warnings JSONB,
    
    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    CONSTRAINT eod_fetch_log_status_valid CHECK (
        status IN ('success', 'failed', 'partial', 'skipped')
    )
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_eod_fetch_log_fetch_date ON public.eod_fetch_log(fetch_date DESC);
CREATE INDEX IF NOT EXISTS idx_eod_fetch_log_status ON public.eod_fetch_log(status);
CREATE INDEX IF NOT EXISTS idx_eod_fetch_log_created_at ON public.eod_fetch_log(created_at DESC);

COMMENT ON TABLE public.eod_fetch_log IS 'Audit log for all EOD data fetch operations';


-- ============================================================
-- 6. QUALITY CONTROL VIEW
-- ============================================================
-- Aggregated view for monitoring data quality

CREATE OR REPLACE VIEW public.eod_quality_summary AS
SELECT
    s.symbol,
    COUNT(DISTINCT ed.trade_date) AS total_days,
    AVG(ed.quality_score) AS avg_quality_score,
    SUM(CASE WHEN ed.is_validated THEN 1 ELSE 0 END) AS validated_records,
    MAX(ed.trade_date) AS last_fetch_date,
    MAX(ed.retrieved_at) AS last_retrieved_at,
    ROUND(
        (SUM(CASE WHEN ed.is_validated THEN 1 ELSE 0 END)::DECIMAL / 
         NULLIF(COUNT(*), 0) * 100)::NUMERIC, 
        2
    ) AS validation_rate_percent
FROM public.eod_data ed
JOIN public.symbols s ON s.id = ed.symbol_id
GROUP BY s.symbol
ORDER BY last_fetch_date DESC;

COMMENT ON VIEW public.eod_quality_summary IS 'Summary of EOD data quality metrics per symbol';


-- ============================================================
-- 7. ROW LEVEL SECURITY (RLS)
-- ============================================================
-- Allow read access for authenticated users, write only for service role

ALTER TABLE public.symbols ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.eod_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.eod_levels ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.eod_fetch_log ENABLE ROW LEVEL SECURITY;

-- Read policy: All authenticated users can read
CREATE POLICY "Allow read access to symbols"
    ON public.symbols FOR SELECT
    TO authenticated
    USING (TRUE);

CREATE POLICY "Allow read access to eod_data"
    ON public.eod_data FOR SELECT
    TO authenticated
    USING (TRUE);

CREATE POLICY "Allow read access to eod_levels"
    ON public.eod_levels FOR SELECT
    TO authenticated
    USING (TRUE);

CREATE POLICY "Allow read access to eod_fetch_log"
    ON public.eod_fetch_log FOR SELECT
    TO authenticated
    USING (TRUE);

-- Write policy: Only service role can insert/update
CREATE POLICY "Service role can manage symbols"
    ON public.symbols FOR ALL
    TO service_role
    USING (TRUE);

CREATE POLICY "Service role can insert eod_data"
    ON public.eod_data FOR INSERT
    TO service_role
    WITH CHECK (TRUE);

CREATE POLICY "Service role can update eod_data"
    ON public.eod_data FOR UPDATE
    TO service_role
    USING (TRUE);

CREATE POLICY "Service role can insert eod_levels"
    ON public.eod_levels FOR INSERT
    TO service_role
    WITH CHECK (TRUE);

CREATE POLICY "Service role can update eod_levels"
    ON public.eod_levels FOR UPDATE
    TO service_role
    USING (TRUE);

CREATE POLICY "Service role can insert eod_fetch_log"
    ON public.eod_fetch_log FOR INSERT
    TO service_role
    WITH CHECK (TRUE);


-- ============================================================
-- 8. UTILITY FUNCTIONS
-- ============================================================

-- Function: Get latest EOD data for a symbol
CREATE OR REPLACE FUNCTION get_latest_eod(symbol_name VARCHAR)
RETURNS TABLE (
    trade_date DATE,
    open DECIMAL,
    high DECIMAL,
    low DECIMAL,
    close DECIMAL,
    volume BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        ed.trade_date,
        ed.open,
        ed.high,
        ed.low,
        ed.close,
        ed.volume
    FROM public.eod_data ed
    JOIN public.symbols s ON s.id = ed.symbol_id
    WHERE s.symbol = symbol_name
    ORDER BY ed.trade_date DESC
    LIMIT 1;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION get_latest_eod IS 'Returns the most recent EOD data for a given symbol';


-- Function: Get yesterday's levels for a symbol
CREATE OR REPLACE FUNCTION get_yesterday_levels(symbol_name VARCHAR, for_date DATE DEFAULT CURRENT_DATE)
RETURNS TABLE (
    yesterday_high DECIMAL,
    yesterday_low DECIMAL,
    yesterday_close DECIMAL,
    yesterday_range DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        el.yesterday_high,
        el.yesterday_low,
        el.yesterday_close,
        el.yesterday_range
    FROM public.eod_levels el
    JOIN public.symbols s ON s.id = el.symbol_id
    WHERE s.symbol = symbol_name
      AND el.trade_date = for_date
    LIMIT 1;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION get_yesterday_levels IS 'Returns yesterday levels for a given symbol and date';


-- Function: Calculate ATR for a symbol
CREATE OR REPLACE FUNCTION calculate_atr(
    symbol_name VARCHAR,
    periods INTEGER DEFAULT 5
)
RETURNS DECIMAL AS $$
DECLARE
    atr_value DECIMAL;
BEGIN
    SELECT AVG(high - low) INTO atr_value
    FROM (
        SELECT ed.high, ed.low
        FROM public.eod_data ed
        JOIN public.symbols s ON s.id = ed.symbol_id
        WHERE s.symbol = symbol_name
        ORDER BY ed.trade_date DESC
        LIMIT periods
    ) recent_data;
    
    RETURN COALESCE(atr_value, 0);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION calculate_atr IS 'Calculates Average True Range for specified number of periods';


-- ============================================================
-- 9. VERIFICATION
-- ============================================================
-- Verify tables were created

SELECT 
    table_name,
    (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) AS column_count
FROM information_schema.tables t
WHERE table_schema = 'public'
  AND table_name IN ('symbols', 'eod_data', 'eod_levels', 'eod_fetch_log')
ORDER BY table_name;

-- Show inserted symbols
SELECT symbol, name, type, is_active FROM public.symbols ORDER BY symbol;


-- ============================================================
-- SETUP COMPLETE! 
-- ============================================================
-- Next steps:
-- 1. Verify symbols were inserted: SELECT * FROM symbols;
-- 2. Test utility functions: SELECT * FROM get_latest_eod('^GDAXI');
-- 3. Start EOD data fetcher: python src/eod_data_fetcher.py
-- ============================================================