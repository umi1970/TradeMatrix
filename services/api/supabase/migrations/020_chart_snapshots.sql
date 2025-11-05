-- =============================================
-- Migration 020: Create chart_snapshots table
-- Created: 2025-11-05
-- Description: Stores generated chart URLs from chart-img.com API with metadata
-- =============================================

BEGIN;

-- Create table
CREATE TABLE IF NOT EXISTS chart_snapshots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol_id UUID NOT NULL REFERENCES market_symbols(id) ON DELETE CASCADE,
    chart_url TEXT NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    created_by_agent VARCHAR(50) NOT NULL,
    metadata JSONB DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '60 days')
);

-- Add comments
COMMENT ON TABLE chart_snapshots
IS 'Stores generated chart URLs from chart-img.com API with metadata for AI agents';

COMMENT ON COLUMN chart_snapshots.symbol_id
IS 'Reference to market_symbols table';

COMMENT ON COLUMN chart_snapshots.chart_url
IS 'Full URL to chart image (PNG format)';

COMMENT ON COLUMN chart_snapshots.timeframe
IS 'Timeframe used for this chart (e.g., 5m, 15m, 1h, D)';

COMMENT ON COLUMN chart_snapshots.created_by_agent
IS 'Agent that requested this chart (e.g., ChartWatcher, MorningPlanner, JournalBot)';

COMMENT ON COLUMN chart_snapshots.metadata
IS 'Additional metadata (indicators, dimensions, trade_id, report_id, analysis_result, etc.)';

COMMENT ON COLUMN chart_snapshots.expires_at
IS 'Chart URL expires after 60 days (chart-img.com retention policy)';

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_chart_snapshots_symbol_id
ON chart_snapshots(symbol_id);

CREATE INDEX IF NOT EXISTS idx_chart_snapshots_agent
ON chart_snapshots(created_by_agent);

CREATE INDEX IF NOT EXISTS idx_chart_snapshots_symbol_created
ON chart_snapshots(symbol_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_chart_snapshots_agent_created
ON chart_snapshots(created_by_agent, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_chart_snapshots_expires_at
ON chart_snapshots(expires_at);

CREATE INDEX IF NOT EXISTS idx_chart_snapshots_metadata
ON chart_snapshots USING GIN (metadata);

-- Enable RLS
ALTER TABLE chart_snapshots ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Users can read their own chart snapshots
CREATE POLICY "Users can read own chart snapshots"
ON chart_snapshots FOR SELECT
USING (
    symbol_id IN (
        SELECT id FROM market_symbols WHERE user_id = auth.uid()
    )
);

-- RLS Policy: Users can insert chart snapshots for their symbols
CREATE POLICY "Users can insert own chart snapshots"
ON chart_snapshots FOR INSERT
WITH CHECK (
    symbol_id IN (
        SELECT id FROM market_symbols WHERE user_id = auth.uid()
    )
);

-- RLS Policy: Users can delete their own chart snapshots
CREATE POLICY "Users can delete own chart snapshots"
ON chart_snapshots FOR DELETE
USING (
    symbol_id IN (
        SELECT id FROM market_symbols WHERE user_id = auth.uid()
    )
);

-- RLS Policy: Service role can access all (for AI agents)
CREATE POLICY "Service role has full access to chart snapshots"
ON chart_snapshots FOR ALL
USING (auth.jwt()->>'role' = 'service_role');

-- Verify migration
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public'
          AND table_name = 'chart_snapshots'
    ) THEN
        RAISE NOTICE '✅ Table chart_snapshots created successfully';
    ELSE
        RAISE EXCEPTION '❌ Table chart_snapshots not found!';
    END IF;

    -- Verify indexes
    IF EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE tablename = 'chart_snapshots'
          AND indexname = 'idx_chart_snapshots_symbol_id'
    ) THEN
        RAISE NOTICE '✅ Indexes created successfully';
    ELSE
        RAISE WARNING '⚠️ Some indexes may be missing';
    END IF;

    -- Verify RLS enabled
    IF EXISTS (
        SELECT 1 FROM pg_tables
        WHERE schemaname = 'public'
          AND tablename = 'chart_snapshots'
          AND rowsecurity = true
    ) THEN
        RAISE NOTICE '✅ RLS enabled successfully';
    ELSE
        RAISE WARNING '⚠️ RLS not enabled!';
    END IF;
END $$;

COMMIT;

-- =============================================
-- HELPER FUNCTIONS
-- =============================================

-- Get latest chart for symbol
CREATE OR REPLACE FUNCTION get_latest_chart(p_symbol_id UUID, p_timeframe VARCHAR DEFAULT NULL)
RETURNS TABLE (
    id UUID,
    chart_url TEXT,
    timeframe VARCHAR,
    created_by_agent VARCHAR,
    metadata JSONB,
    created_at TIMESTAMPTZ
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    RETURN QUERY
    SELECT
        cs.id,
        cs.chart_url,
        cs.timeframe,
        cs.created_by_agent,
        cs.metadata,
        cs.created_at
    FROM chart_snapshots cs
    WHERE cs.symbol_id = p_symbol_id
        AND (p_timeframe IS NULL OR cs.timeframe = p_timeframe)
    ORDER BY cs.created_at DESC
    LIMIT 1;
END;
$$;

COMMENT ON FUNCTION get_latest_chart IS 'Get most recent chart snapshot for a symbol (optionally filtered by timeframe)';

-- Get chart count by agent
CREATE OR REPLACE FUNCTION get_chart_count_by_agent(p_days INTEGER DEFAULT 7)
RETURNS TABLE (
    agent_name VARCHAR,
    chart_count BIGINT
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    RETURN QUERY
    SELECT
        created_by_agent,
        COUNT(*)::BIGINT
    FROM chart_snapshots
    WHERE created_at >= NOW() - (p_days || ' days')::INTERVAL
    GROUP BY created_by_agent
    ORDER BY COUNT(*) DESC;
END;
$$;

COMMENT ON FUNCTION get_chart_count_by_agent IS 'Get chart generation statistics per agent for last N days';

-- =============================================
-- USAGE EXAMPLES
-- =============================================

-- Insert chart snapshot
-- INSERT INTO chart_snapshots (symbol_id, chart_url, timeframe, created_by_agent, metadata)
-- VALUES (
--     'symbol-uuid-here',
--     'https://api.chart-img.com/tradingview/advanced-chart?...',
--     '1h',
--     'ChartWatcher',
--     '{"indicators": ["RSI", "MACD"], "width": 1200, "height": 800}'::JSONB
-- );

-- Get latest chart for DAX on 1h timeframe
-- SELECT * FROM get_latest_chart('dax-symbol-uuid', '1h');

-- Get chart count by agent (last 7 days)
-- SELECT * FROM get_chart_count_by_agent();

-- Find charts with specific indicator
-- SELECT cs.id, ms.symbol, cs.timeframe, cs.chart_url
-- FROM chart_snapshots cs
-- JOIN market_symbols ms ON cs.symbol_id = ms.id
-- WHERE cs.metadata @> '{"indicators": ["Relative Strength Index"]}';
