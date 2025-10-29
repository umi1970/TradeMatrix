-- TradeMatrix.ai - Chart Analyses Table Migration
-- Stores AI-powered chart pattern analysis results from ChartWatcher agent

-- Chart Analyses table
CREATE TABLE IF NOT EXISTS public.chart_analyses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Reference to symbol
    symbol_id UUID NOT NULL REFERENCES public.market_symbols(id) ON DELETE CASCADE,

    -- Chart metadata
    timeframe TEXT NOT NULL CHECK (timeframe IN ('1m', '5m', '15m', '1h', '4h', '1d', '1w')),
    chart_url TEXT NOT NULL,

    -- Pattern detection results
    patterns_detected JSONB DEFAULT '[]'::jsonb, -- Array of detected patterns
    trend TEXT CHECK (trend IN ('bullish', 'bearish', 'sideways', 'unknown')),

    -- Key levels
    support_levels DECIMAL(20, 8)[] DEFAULT ARRAY[]::DECIMAL[],
    resistance_levels DECIMAL(20, 8)[] DEFAULT ARRAY[]::DECIMAL[],

    -- Analysis quality
    confidence_score DECIMAL(5, 2) DEFAULT 0.0 CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
    analysis_summary TEXT,

    -- Full analysis payload
    payload JSONB DEFAULT '{}'::jsonb,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_chart_analyses_symbol_id ON public.chart_analyses(symbol_id);
CREATE INDEX IF NOT EXISTS idx_chart_analyses_timeframe ON public.chart_analyses(timeframe);
CREATE INDEX IF NOT EXISTS idx_chart_analyses_created_at ON public.chart_analyses(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_chart_analyses_trend ON public.chart_analyses(trend);
CREATE INDEX IF NOT EXISTS idx_chart_analyses_confidence ON public.chart_analyses(confidence_score DESC);

-- Composite index for common queries
CREATE INDEX IF NOT EXISTS idx_chart_analyses_symbol_timeframe
ON public.chart_analyses(symbol_id, timeframe, created_at DESC);

-- GIN index for JSONB pattern searches
CREATE INDEX IF NOT EXISTS idx_chart_analyses_patterns
ON public.chart_analyses USING GIN (patterns_detected);

-- Enable Row Level Security
ALTER TABLE public.chart_analyses ENABLE ROW LEVEL SECURITY;

-- RLS Policies

-- Public read access (all users can view chart analyses)
CREATE POLICY "Public read access for chart analyses"
ON public.chart_analyses
FOR SELECT
USING (true);

-- Service role only for insert/update/delete (agents use service role)
CREATE POLICY "Service role full access to chart analyses"
ON public.chart_analyses
FOR ALL
USING (auth.role() = 'service_role');

-- Update timestamp trigger
CREATE OR REPLACE FUNCTION update_chart_analyses_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER chart_analyses_updated_at
BEFORE UPDATE ON public.chart_analyses
FOR EACH ROW
EXECUTE FUNCTION update_chart_analyses_updated_at();

-- Comments
COMMENT ON TABLE public.chart_analyses IS 'Stores AI-powered chart pattern analysis results from ChartWatcher agent';
COMMENT ON COLUMN public.chart_analyses.patterns_detected IS 'Array of detected patterns with confidence scores (JSON)';
COMMENT ON COLUMN public.chart_analyses.support_levels IS 'Identified support price levels';
COMMENT ON COLUMN public.chart_analyses.resistance_levels IS 'Identified resistance price levels';
COMMENT ON COLUMN public.chart_analyses.confidence_score IS 'Overall confidence of the analysis (0.0-1.0)';
COMMENT ON COLUMN public.chart_analyses.payload IS 'Full analysis results including price data and metadata';
