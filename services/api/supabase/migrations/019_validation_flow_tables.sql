-- Migration 019: Validation & Risk Flow Tables
-- Creates tables for TradeDecisionEngine, RiskContextEvaluator, and ReportBridge
-- Date: 2025-11-05
-- Phase: 4B - AI Agent Integration

-- ============================================================================
-- 1. TRADE_DECISIONS TABLE
-- ============================================================================
-- Stores all trade decisions made by TradeDecisionEngine
-- Provides audit trail of EXECUTE/REJECT/WAIT/HALT/REDUCE decisions

CREATE TABLE IF NOT EXISTS trade_decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trade_id UUID REFERENCES trades(id) ON DELETE SET NULL,
    user_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
    symbol_id UUID REFERENCES market_symbols(id) ON DELETE SET NULL,

    -- Decision data
    decision TEXT NOT NULL CHECK (decision IN ('EXECUTE', 'REJECT', 'WAIT', 'HALT', 'REDUCE')),
    reason TEXT NOT NULL,
    bias_score DECIMAL(5,2),  -- 0.00 to 1.00
    rr_ratio DECIMAL(5,2),     -- Risk/Reward ratio

    -- Context (JSONB for flexibility)
    context JSONB DEFAULT '{}',  -- risk_context, validation_warnings, high_risk_event, trade_proposal

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_trade_decisions_user_id ON trade_decisions(user_id);
CREATE INDEX idx_trade_decisions_symbol_id ON trade_decisions(symbol_id);
CREATE INDEX idx_trade_decisions_decision ON trade_decisions(decision);
CREATE INDEX idx_trade_decisions_created_at ON trade_decisions(created_at DESC);

-- RLS Policies
ALTER TABLE trade_decisions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own trade decisions"
    ON trade_decisions FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own trade decisions"
    ON trade_decisions FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Updated_at trigger
CREATE TRIGGER update_trade_decisions_updated_at
    BEFORE UPDATE ON trade_decisions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();


-- ============================================================================
-- 2. JOURNAL_ENTRIES TABLE
-- ============================================================================
-- Stores journal entries for all trading activities
-- Used by ReportBridge and JournalBot for audit trail and reporting

CREATE TABLE IF NOT EXISTS journal_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
    symbol_id UUID REFERENCES market_symbols(id) ON DELETE SET NULL,
    trade_id UUID REFERENCES trades(id) ON DELETE SET NULL,

    -- Entry data
    entry_type TEXT NOT NULL DEFAULT 'decision',  -- 'decision', 'trade', 'analysis', 'note'
    decision TEXT,  -- EXECUTE, REJECT, WAIT, HALT, REDUCE (if entry_type = 'decision')
    content TEXT NOT NULL,  -- Main journal content

    -- Context (JSONB for flexibility)
    context JSONB DEFAULT '{}',  -- Additional structured data
    metadata JSONB DEFAULT '{}', -- Source, version, etc.

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_journal_entries_user_id ON journal_entries(user_id);
CREATE INDEX idx_journal_entries_symbol_id ON journal_entries(symbol_id);
CREATE INDEX idx_journal_entries_trade_id ON journal_entries(trade_id);
CREATE INDEX idx_journal_entries_entry_type ON journal_entries(entry_type);
CREATE INDEX idx_journal_entries_created_at ON journal_entries(created_at DESC);

-- RLS Policies
ALTER TABLE journal_entries ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own journal entries"
    ON journal_entries FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own journal entries"
    ON journal_entries FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own journal entries"
    ON journal_entries FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own journal entries"
    ON journal_entries FOR DELETE
    USING (auth.uid() = user_id);

-- Updated_at trigger
CREATE TRIGGER update_journal_entries_updated_at
    BEFORE UPDATE ON journal_entries
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();


-- ============================================================================
-- 3. REPORT_QUEUE TABLE
-- ============================================================================
-- Queue for report generation by JournalBot
-- Stores decisions and events pending inclusion in daily/weekly/monthly reports

CREATE TABLE IF NOT EXISTS report_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
    symbol_id UUID REFERENCES market_symbols(id) ON DELETE SET NULL,

    -- Queue data
    queue_type TEXT NOT NULL DEFAULT 'decision',  -- 'decision', 'alert', 'analysis', 'event'
    priority INTEGER DEFAULT 2,  -- 1 = high, 2 = normal, 3 = low
    payload JSONB NOT NULL,  -- Decision data, content, tags, metadata

    -- Processing status
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    processed_at TIMESTAMPTZ,
    error_message TEXT,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_report_queue_user_id ON report_queue(user_id);
CREATE INDEX idx_report_queue_status ON report_queue(status);
CREATE INDEX idx_report_queue_priority ON report_queue(priority);
CREATE INDEX idx_report_queue_created_at ON report_queue(created_at DESC);
CREATE INDEX idx_report_queue_pending_priority ON report_queue(status, priority) WHERE status = 'pending';

-- RLS Policies
ALTER TABLE report_queue ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own report queue"
    ON report_queue FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "System can insert into report queue"
    ON report_queue FOR INSERT
    WITH CHECK (true);  -- Allow system inserts (from agents)

CREATE POLICY "System can update report queue"
    ON report_queue FOR UPDATE
    USING (true);  -- Allow system updates (status changes)

-- Updated_at trigger
CREATE TRIGGER update_report_queue_updated_at
    BEFORE UPDATE ON report_queue
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();


-- ============================================================================
-- 4. HELPER VIEWS
-- ============================================================================

-- View: Recent trade decisions (last 24 hours)
CREATE OR REPLACE VIEW recent_trade_decisions AS
SELECT
    td.*,
    ms.symbol,
    ms.alias AS symbol_name
FROM trade_decisions td
LEFT JOIN market_symbols ms ON td.symbol_id = ms.id
WHERE td.created_at >= NOW() - INTERVAL '24 hours'
ORDER BY td.created_at DESC;

-- View: Pending report queue items
CREATE OR REPLACE VIEW pending_reports AS
SELECT
    rq.*,
    ms.symbol,
    ms.alias AS symbol_name
FROM report_queue rq
LEFT JOIN market_symbols ms ON rq.symbol_id = ms.id
WHERE rq.status = 'pending'
ORDER BY rq.priority ASC, rq.created_at ASC;


-- ============================================================================
-- 5. HELPER FUNCTIONS
-- ============================================================================

-- Function: Get decision statistics for a user
CREATE OR REPLACE FUNCTION get_decision_stats(
    p_user_id UUID,
    p_days INTEGER DEFAULT 7
)
RETURNS TABLE(
    total_decisions INTEGER,
    execute_count INTEGER,
    reject_count INTEGER,
    wait_count INTEGER,
    halt_count INTEGER,
    reduce_count INTEGER,
    execute_rate DECIMAL(5,2),
    avg_bias_score DECIMAL(5,2),
    avg_rr_ratio DECIMAL(5,2)
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(*)::INTEGER AS total_decisions,
        COUNT(*) FILTER (WHERE decision = 'EXECUTE')::INTEGER AS execute_count,
        COUNT(*) FILTER (WHERE decision = 'REJECT')::INTEGER AS reject_count,
        COUNT(*) FILTER (WHERE decision = 'WAIT')::INTEGER AS wait_count,
        COUNT(*) FILTER (WHERE decision = 'HALT')::INTEGER AS halt_count,
        COUNT(*) FILTER (WHERE decision = 'REDUCE')::INTEGER AS reduce_count,
        (COUNT(*) FILTER (WHERE decision = 'EXECUTE')::DECIMAL / NULLIF(COUNT(*), 0) * 100)::DECIMAL(5,2) AS execute_rate,
        AVG(bias_score)::DECIMAL(5,2) AS avg_bias_score,
        AVG(rr_ratio)::DECIMAL(5,2) AS avg_rr_ratio
    FROM trade_decisions
    WHERE user_id = p_user_id
    AND created_at >= NOW() - (p_days || ' days')::INTERVAL;
END;
$$;

-- Function: Clean old report queue entries (older than 30 days)
CREATE OR REPLACE FUNCTION cleanup_report_queue()
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM report_queue
    WHERE status = 'completed'
    AND processed_at < NOW() - INTERVAL '30 days';

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$;


-- ============================================================================
-- 6. COMMENTS
-- ============================================================================

COMMENT ON TABLE trade_decisions IS 'Audit trail of all trade decisions made by TradeDecisionEngine (Phase 4B)';
COMMENT ON TABLE journal_entries IS 'Trading journal entries for audit trail and reporting (Phase 4B)';
COMMENT ON TABLE report_queue IS 'Queue for JournalBot report generation (Phase 4B)';

COMMENT ON COLUMN trade_decisions.decision IS 'Final decision: EXECUTE, REJECT, WAIT, HALT, REDUCE';
COMMENT ON COLUMN trade_decisions.context IS 'JSONB: risk_context, validation_warnings, high_risk_event, trade_proposal';
COMMENT ON COLUMN journal_entries.entry_type IS 'Entry type: decision, trade, analysis, note';
COMMENT ON COLUMN report_queue.queue_type IS 'Queue type: decision, alert, analysis, event';
COMMENT ON COLUMN report_queue.priority IS 'Priority: 1=high, 2=normal, 3=low';
