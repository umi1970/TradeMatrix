# Database Schema

## Overview

Die chart-img.com Integration erweitert die bestehende `market_symbols` Tabelle um eine JSONB-Spalte für Chart-Konfigurationen und fügt eine neue `chart_snapshots` Tabelle für die Speicherung generierter Charts hinzu.

## Tables

### 1. `market_symbols` (Extended)

Erweitert die bestehende Tabelle um Chart-Konfigurationen.

#### Schema

```sql
-- Extend existing table
ALTER TABLE market_symbols ADD COLUMN IF NOT EXISTS chart_config JSONB DEFAULT '{}'::JSONB;

-- Add comment
COMMENT ON COLUMN market_symbols.chart_config IS 'User-defined chart configuration for chart-img.com API';
```

#### Full Table Structure (after extension)

```sql
CREATE TABLE IF NOT EXISTS market_symbols (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    symbol VARCHAR(20) NOT NULL,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(20) NOT NULL, -- 'index', 'forex', 'crypto', 'stock'
    enabled BOOLEAN DEFAULT true,
    chart_config JSONB DEFAULT '{}'::JSONB, -- NEW
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, symbol)
);
```

#### JSONB Structure (`chart_config`)

```json
{
  "tv_symbol": "XETR:DAX",           // TradingView symbol (required)
  "timeframes": ["M15", "H1", "D1"], // Array of timeframes (required)
  "indicators": ["RSI", "MACD"],     // Array of indicator codes (optional)
  "chart_type": "candles",           // "candles" | "bars" | "line" (default: "candles")
  "theme": "dark",                   // "dark" | "light" (default: "dark")
  "width": 1200,                     // Chart width in pixels (default: 1200)
  "height": 800,                     // Chart height in pixels (default: 800)
  "show_volume": true,               // Show volume bars (default: true)
  "show_legend": true,               // Show legend (default: true)
  "timezone": "Europe/Berlin"        // Timezone (default: "Europe/Berlin")
}
```

#### Supported Values

**Timeframes**:
- `"1"` = 1 minute
- `"5"` = 5 minutes
- `"15"` = 15 minutes (M15)
- `"60"` = 1 hour (H1)
- `"240"` = 4 hours (H4)
- `"D"` = 1 day (D1)
- `"W"` = 1 week
- `"M"` = 1 month

**Indicators** (chart-img.com format):
- `"RSI@tv-basicstudies"` = Relative Strength Index
- `"MACD@tv-basicstudies"` = MACD
- `"BB@tv-basicstudies"` = Bollinger Bands
- `"Stochastic@tv-basicstudies"` = Stochastic
- `"Volume@tv-basicstudies"` = Volume
- `"EMA@tv-basicstudies"` = Exponential Moving Average

**Chart Types**:
- `"candles"` = Candlestick chart (default)
- `"bars"` = OHLC bars
- `"line"` = Line chart
- `"area"` = Area chart

**Themes**:
- `"dark"` = Dark theme (default)
- `"light"` = Light theme

#### Example Data

```sql
-- DAX with RSI and MACD on M15, H1, D1
UPDATE market_symbols SET chart_config = '{
  "tv_symbol": "XETR:DAX",
  "timeframes": ["15", "60", "D"],
  "indicators": ["RSI@tv-basicstudies", "MACD@tv-basicstudies"],
  "chart_type": "candles",
  "theme": "dark",
  "width": 1200,
  "height": 800,
  "show_volume": true
}'::JSONB
WHERE symbol = '^GDAXI';

-- NASDAQ with Bollinger Bands on H1 and D1
UPDATE market_symbols SET chart_config = '{
  "tv_symbol": "NASDAQ:NDX",
  "timeframes": ["60", "D"],
  "indicators": ["BB@tv-basicstudies"],
  "chart_type": "candles",
  "theme": "dark",
  "width": 1200,
  "height": 800
}'::JSONB
WHERE symbol = '^NDX';

-- EUR/USD with no indicators (clean chart)
UPDATE market_symbols SET chart_config = '{
  "tv_symbol": "OANDA:EURUSD",
  "timeframes": ["15", "60"],
  "indicators": [],
  "chart_type": "candles",
  "theme": "light",
  "width": 1400,
  "height": 900
}'::JSONB
WHERE symbol = 'EURUSD=X';
```

#### Indexes

```sql
-- Index on user_id for faster lookups
CREATE INDEX IF NOT EXISTS idx_market_symbols_user_id ON market_symbols(user_id);

-- Index on enabled symbols (for active charts)
CREATE INDEX IF NOT EXISTS idx_market_symbols_enabled ON market_symbols(enabled) WHERE enabled = true;

-- GIN index on chart_config for JSONB queries
CREATE INDEX IF NOT EXISTS idx_market_symbols_chart_config ON market_symbols USING GIN (chart_config);
```

#### JSONB Query Examples

```sql
-- Find all symbols with RSI indicator
SELECT symbol, name, chart_config
FROM market_symbols
WHERE chart_config @> '{"indicators": ["RSI@tv-basicstudies"]}';

-- Find symbols with D1 timeframe
SELECT symbol, name, chart_config
FROM market_symbols
WHERE chart_config->'timeframes' ? 'D';

-- Find symbols with dark theme
SELECT symbol, name, chart_config
FROM market_symbols
WHERE chart_config->>'theme' = 'dark';

-- Get all configured timeframes for a symbol
SELECT symbol, jsonb_array_elements_text(chart_config->'timeframes') as timeframe
FROM market_symbols
WHERE symbol = '^GDAXI';
```

---

### 2. `chart_snapshots` (New Table)

Speichert generierte Chart-URLs mit Metadaten für spätere Verwendung.

#### Schema

```sql
CREATE TABLE IF NOT EXISTS chart_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    symbol_id UUID NOT NULL REFERENCES market_symbols(id) ON DELETE CASCADE,
    chart_url TEXT NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    created_by_agent VARCHAR(50) NOT NULL,
    metadata JSONB DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '60 days')
);

-- Comments
COMMENT ON TABLE chart_snapshots IS 'Stores generated chart URLs from chart-img.com API';
COMMENT ON COLUMN chart_snapshots.symbol_id IS 'Reference to market_symbols table';
COMMENT ON COLUMN chart_snapshots.chart_url IS 'Full URL to chart image';
COMMENT ON COLUMN chart_snapshots.timeframe IS 'Timeframe used for this chart (e.g., M15, H1, D1)';
COMMENT ON COLUMN chart_snapshots.created_by_agent IS 'Agent that requested this chart (e.g., ChartWatcher, MorningPlanner)';
COMMENT ON COLUMN chart_snapshots.metadata IS 'Additional metadata (indicators, dimensions, etc.)';
COMMENT ON COLUMN chart_snapshots.expires_at IS 'Chart URL expires after 60 days (chart-img.com retention)';
```

#### JSONB Structure (`metadata`)

```json
{
  "indicators": ["RSI@tv-basicstudies", "MACD@tv-basicstudies"],
  "chart_type": "candles",
  "theme": "dark",
  "width": 1200,
  "height": 800,
  "request_timestamp": "2025-11-02T10:30:00Z",
  "api_response_time_ms": 245,
  "trade_id": "uuid-if-related-to-trade",
  "report_id": "uuid-if-related-to-report",
  "analysis_result": {
    "pattern_detected": "double_bottom",
    "confidence": 0.85
  }
}
```

#### Example Data

```sql
-- ChartWatcher snapshot
INSERT INTO chart_snapshots (symbol_id, chart_url, timeframe, created_by_agent, metadata)
VALUES (
    'c8f3a5d7-4f2e-4c6d-8a9b-1e2f3a4b5c6d', -- DAX symbol_id
    'https://api.chart-img.com/tradingview/advanced-chart?symbol=XETR:DAX&interval=15&...',
    'M15',
    'ChartWatcher',
    '{
        "indicators": ["RSI@tv-basicstudies"],
        "chart_type": "candles",
        "theme": "dark",
        "width": 1200,
        "height": 800,
        "request_timestamp": "2025-11-02T10:30:00Z",
        "api_response_time_ms": 210
    }'::JSONB
);

-- MorningPlanner snapshot
INSERT INTO chart_snapshots (symbol_id, chart_url, timeframe, created_by_agent, metadata)
VALUES (
    'c8f3a5d7-4f2e-4c6d-8a9b-1e2f3a4b5c6d',
    'https://api.chart-img.com/tradingview/advanced-chart?symbol=XETR:DAX&interval=60&...',
    'H1',
    'MorningPlanner',
    '{
        "indicators": ["MACD@tv-basicstudies"],
        "chart_type": "candles",
        "theme": "dark",
        "width": 1400,
        "height": 900,
        "report_id": "morning-report-2025-11-02"
    }'::JSONB
);

-- JournalBot snapshot (linked to trade)
INSERT INTO chart_snapshots (symbol_id, chart_url, timeframe, created_by_agent, metadata)
VALUES (
    'c8f3a5d7-4f2e-4c6d-8a9b-1e2f3a4b5c6d',
    'https://api.chart-img.com/tradingview/advanced-chart?symbol=XETR:DAX&interval=15&...',
    'M15',
    'JournalBot',
    '{
        "indicators": [],
        "chart_type": "candles",
        "theme": "light",
        "width": 1200,
        "height": 800,
        "trade_id": "trade-uuid-12345",
        "entry_price": 18500.50,
        "analysis_result": {
            "pattern_detected": "bull_flag",
            "confidence": 0.92
        }
    }'::JSONB
);
```

#### Indexes

```sql
-- Index on symbol_id for quick lookup by symbol
CREATE INDEX IF NOT EXISTS idx_chart_snapshots_symbol_id ON chart_snapshots(symbol_id);

-- Index on created_by_agent for agent-specific queries
CREATE INDEX IF NOT EXISTS idx_chart_snapshots_agent ON chart_snapshots(created_by_agent);

-- Composite index on symbol_id + created_at for recent charts
CREATE INDEX IF NOT EXISTS idx_chart_snapshots_symbol_created
ON chart_snapshots(symbol_id, created_at DESC);

-- Composite index on agent + created_at for agent dashboards
CREATE INDEX IF NOT EXISTS idx_chart_snapshots_agent_created
ON chart_snapshots(created_by_agent, created_at DESC);

-- Index on expires_at for cleanup jobs
CREATE INDEX IF NOT EXISTS idx_chart_snapshots_expires_at ON chart_snapshots(expires_at);

-- GIN index on metadata for JSONB queries
CREATE INDEX IF NOT EXISTS idx_chart_snapshots_metadata ON chart_snapshots USING GIN (metadata);
```

#### JSONB Query Examples

```sql
-- Find charts with specific indicator
SELECT cs.id, ms.symbol, cs.timeframe, cs.chart_url
FROM chart_snapshots cs
JOIN market_symbols ms ON cs.symbol_id = ms.id
WHERE cs.metadata @> '{"indicators": ["RSI@tv-basicstudies"]}';

-- Find charts linked to a specific trade
SELECT *
FROM chart_snapshots
WHERE metadata->>'trade_id' = 'trade-uuid-12345';

-- Find charts by pattern detection
SELECT cs.id, ms.symbol, cs.metadata->'analysis_result'->>'pattern_detected' as pattern
FROM chart_snapshots cs
JOIN market_symbols ms ON cs.symbol_id = ms.id
WHERE cs.metadata->'analysis_result'->>'pattern_detected' IS NOT NULL;

-- Get latest chart per symbol
SELECT DISTINCT ON (symbol_id)
    symbol_id,
    chart_url,
    timeframe,
    created_at
FROM chart_snapshots
ORDER BY symbol_id, created_at DESC;
```

---

## Row Level Security (RLS)

### Policies for `market_symbols`

```sql
-- Enable RLS
ALTER TABLE market_symbols ENABLE ROW LEVEL SECURITY;

-- Policy: Users can read their own symbols
CREATE POLICY "Users can read own symbols"
ON market_symbols FOR SELECT
USING (auth.uid() = user_id);

-- Policy: Users can insert their own symbols
CREATE POLICY "Users can insert own symbols"
ON market_symbols FOR INSERT
WITH CHECK (auth.uid() = user_id);

-- Policy: Users can update their own symbols
CREATE POLICY "Users can update own symbols"
ON market_symbols FOR UPDATE
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

-- Policy: Users can delete their own symbols
CREATE POLICY "Users can delete own symbols"
ON market_symbols FOR DELETE
USING (auth.uid() = user_id);

-- Policy: Service role can access all (for AI agents)
CREATE POLICY "Service role has full access"
ON market_symbols FOR ALL
USING (auth.jwt()->>'role' = 'service_role');
```

### Policies for `chart_snapshots`

```sql
-- Enable RLS
ALTER TABLE chart_snapshots ENABLE ROW LEVEL SECURITY;

-- Policy: Users can read their own chart snapshots
CREATE POLICY "Users can read own chart snapshots"
ON chart_snapshots FOR SELECT
USING (
    symbol_id IN (
        SELECT id FROM market_symbols WHERE user_id = auth.uid()
    )
);

-- Policy: Users can insert chart snapshots for their symbols
CREATE POLICY "Users can insert own chart snapshots"
ON chart_snapshots FOR INSERT
WITH CHECK (
    symbol_id IN (
        SELECT id FROM market_symbols WHERE user_id = auth.uid()
    )
);

-- Policy: Users can delete their own chart snapshots
CREATE POLICY "Users can delete own chart snapshots"
ON chart_snapshots FOR DELETE
USING (
    symbol_id IN (
        SELECT id FROM market_symbols WHERE user_id = auth.uid()
    )
);

-- Policy: Service role can access all (for AI agents)
CREATE POLICY "Service role has full access"
ON chart_snapshots FOR ALL
USING (auth.jwt()->>'role' = 'service_role');
```

---

## Migrations

### Migration 001: Extend market_symbols

**File**: `services/api/supabase/migrations/016_chart_config.sql`

```sql
-- =============================================
-- Migration 016: Add chart_config to market_symbols
-- Created: 2025-11-02
-- Description: Extends market_symbols with JSONB chart configuration
-- =============================================

BEGIN;

-- Add chart_config column
ALTER TABLE market_symbols
ADD COLUMN IF NOT EXISTS chart_config JSONB DEFAULT '{}'::JSONB;

-- Add comment
COMMENT ON COLUMN market_symbols.chart_config
IS 'User-defined chart configuration for chart-img.com API';

-- Create GIN index for JSONB queries
CREATE INDEX IF NOT EXISTS idx_market_symbols_chart_config
ON market_symbols USING GIN (chart_config);

-- Set default chart_config for existing symbols
UPDATE market_symbols
SET chart_config = jsonb_build_object(
    'tv_symbol', CASE symbol
        WHEN '^GDAXI' THEN 'XETR:DAX'
        WHEN '^NDX' THEN 'NASDAQ:NDX'
        WHEN '^DJI' THEN 'DJCFD:DJI'
        WHEN 'EURUSD=X' THEN 'OANDA:EURUSD'
        WHEN 'EURGBP=X' THEN 'OANDA:EURGBP'
        ELSE symbol
    END,
    'timeframes', ARRAY['15', '60', 'D']::TEXT[],
    'indicators', ARRAY['RSI@tv-basicstudies']::TEXT[],
    'chart_type', 'candles',
    'theme', 'dark',
    'width', 1200,
    'height', 800,
    'show_volume', true
)
WHERE chart_config = '{}'::JSONB;

COMMIT;
```

### Migration 002: Create chart_snapshots table

**File**: `services/api/supabase/migrations/017_chart_snapshots.sql`

```sql
-- =============================================
-- Migration 017: Create chart_snapshots table
-- Created: 2025-11-02
-- Description: Stores generated chart URLs from chart-img.com
-- =============================================

BEGIN;

-- Create table
CREATE TABLE IF NOT EXISTS chart_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
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
IS 'Stores generated chart URLs from chart-img.com API';

COMMENT ON COLUMN chart_snapshots.symbol_id
IS 'Reference to market_symbols table';

COMMENT ON COLUMN chart_snapshots.chart_url
IS 'Full URL to chart image';

COMMENT ON COLUMN chart_snapshots.timeframe
IS 'Timeframe used for this chart (e.g., M15, H1, D1)';

COMMENT ON COLUMN chart_snapshots.created_by_agent
IS 'Agent that requested this chart (e.g., ChartWatcher, MorningPlanner)';

COMMENT ON COLUMN chart_snapshots.metadata
IS 'Additional metadata (indicators, dimensions, etc.)';

COMMENT ON COLUMN chart_snapshots.expires_at
IS 'Chart URL expires after 60 days (chart-img.com retention)';

-- Create indexes
CREATE INDEX idx_chart_snapshots_symbol_id ON chart_snapshots(symbol_id);
CREATE INDEX idx_chart_snapshots_agent ON chart_snapshots(created_by_agent);
CREATE INDEX idx_chart_snapshots_symbol_created ON chart_snapshots(symbol_id, created_at DESC);
CREATE INDEX idx_chart_snapshots_agent_created ON chart_snapshots(created_by_agent, created_at DESC);
CREATE INDEX idx_chart_snapshots_expires_at ON chart_snapshots(expires_at);
CREATE INDEX idx_chart_snapshots_metadata ON chart_snapshots USING GIN (metadata);

-- Enable RLS
ALTER TABLE chart_snapshots ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY "Users can read own chart snapshots"
ON chart_snapshots FOR SELECT
USING (
    symbol_id IN (
        SELECT id FROM market_symbols WHERE user_id = auth.uid()
    )
);

CREATE POLICY "Users can insert own chart snapshots"
ON chart_snapshots FOR INSERT
WITH CHECK (
    symbol_id IN (
        SELECT id FROM market_symbols WHERE user_id = auth.uid()
    )
);

CREATE POLICY "Users can delete own chart snapshots"
ON chart_snapshots FOR DELETE
USING (
    symbol_id IN (
        SELECT id FROM market_symbols WHERE user_id = auth.uid()
    )
);

CREATE POLICY "Service role has full access"
ON chart_snapshots FOR ALL
USING (auth.jwt()->>'role' = 'service_role');

COMMIT;
```

### Migration 003: Cleanup expired snapshots (Function)

**File**: `services/api/supabase/migrations/018_chart_snapshots_cleanup.sql`

```sql
-- =============================================
-- Migration 018: Auto-cleanup expired chart snapshots
-- Created: 2025-11-02
-- Description: Function to delete expired chart snapshots
-- =============================================

BEGIN;

-- Create function to cleanup expired snapshots
CREATE OR REPLACE FUNCTION cleanup_expired_chart_snapshots()
RETURNS INTEGER
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM chart_snapshots
    WHERE expires_at < NOW();

    GET DIAGNOSTICS deleted_count = ROW_COUNT;

    RAISE NOTICE 'Deleted % expired chart snapshots', deleted_count;

    RETURN deleted_count;
END;
$$;

-- Schedule daily cleanup (requires pg_cron extension)
-- Run this manually in Supabase SQL Editor if pg_cron is available:
-- SELECT cron.schedule('cleanup-chart-snapshots', '0 2 * * *', 'SELECT cleanup_expired_chart_snapshots()');

COMMIT;
```

---

## Helper Functions

### Get Latest Chart for Symbol

```sql
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

-- Usage:
-- SELECT * FROM get_latest_chart('symbol-uuid');
-- SELECT * FROM get_latest_chart('symbol-uuid', 'M15');
```

### Get Chart Count by Agent

```sql
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

-- Usage:
-- SELECT * FROM get_chart_count_by_agent(); -- Last 7 days
-- SELECT * FROM get_chart_count_by_agent(30); -- Last 30 days
```

---

## Testing Queries

### Validate chart_config JSONB

```sql
-- Check if all required fields exist
SELECT
    id,
    symbol,
    CASE
        WHEN chart_config ? 'tv_symbol' THEN 'OK'
        ELSE 'MISSING tv_symbol'
    END as tv_symbol_check,
    CASE
        WHEN chart_config ? 'timeframes' THEN 'OK'
        ELSE 'MISSING timeframes'
    END as timeframes_check
FROM market_symbols
WHERE enabled = true;
```

### Test RLS Policies

```sql
-- Test as authenticated user
SET ROLE authenticated;
SET request.jwt.claims.sub TO 'user-uuid-here';

-- Should return only user's symbols
SELECT * FROM market_symbols;

-- Should return only user's chart snapshots
SELECT * FROM chart_snapshots;

-- Reset role
RESET ROLE;
```

---

## Next Steps

1. Run migrations in Supabase SQL Editor
2. Review [API Endpoints](./03_API_ENDPOINTS.md)
3. Implement [Frontend Components](./04_FRONTEND_COMPONENTS.md)

---

**Last Updated**: 2025-11-02
**Migration Status**: Ready for execution
