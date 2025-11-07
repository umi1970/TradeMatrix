-- Migration 025: AI Usage Tracking & Rate Limiting
-- Created: 2025-11-07
-- Purpose: Track OpenAI API usage for cost control and rate limiting

-- ================================================
-- AI Usage Log Table
-- ================================================

CREATE TABLE IF NOT EXISTS public.ai_usage_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID,  -- NULL for system calls, filled for user-triggered calls
    agent_name TEXT NOT NULL,  -- 'chart_watcher', 'journal_bot', 'morning_planner'
    symbol TEXT,  -- Symbol being analyzed (optional)
    model TEXT,  -- OpenAI model used (e.g., 'gpt-4-vision-preview', 'gpt-4')
    cost NUMERIC(6, 4) DEFAULT 0.0,  -- Estimated cost in USD
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ================================================
-- Indexes for Performance
-- ================================================

-- Fast lookups for user daily usage
CREATE INDEX IF NOT EXISTS idx_ai_usage_log_user_date
ON public.ai_usage_log(user_id, created_at);

-- Fast lookups for system-wide budget
CREATE INDEX IF NOT EXISTS idx_ai_usage_log_date
ON public.ai_usage_log(created_at);

-- Agent-specific analytics
CREATE INDEX IF NOT EXISTS idx_ai_usage_log_agent
ON public.ai_usage_log(agent_name, created_at);

-- ================================================
-- Row Level Security (RLS)
-- ================================================

ALTER TABLE public.ai_usage_log ENABLE ROW LEVEL SECURITY;

-- Users can only see their own usage
CREATE POLICY "Users can view own AI usage"
ON public.ai_usage_log
FOR SELECT
USING (auth.uid() = user_id);

-- Only service role can insert (backend only)
CREATE POLICY "Service role can insert AI usage"
ON public.ai_usage_log
FOR INSERT
WITH CHECK (true);

-- Admins can see all usage
CREATE POLICY "Admins can view all AI usage"
ON public.ai_usage_log
FOR SELECT
USING (
    EXISTS (
        SELECT 1 FROM public.profiles
        WHERE id = auth.uid() AND role = 'admin'
    )
);

-- ================================================
-- Helper View: Daily Usage Summary
-- ================================================

CREATE OR REPLACE VIEW public.ai_usage_daily AS
SELECT
    user_id,
    DATE(created_at) as usage_date,
    agent_name,
    COUNT(*) as call_count,
    SUM(cost) as total_cost
FROM public.ai_usage_log
GROUP BY user_id, DATE(created_at), agent_name
ORDER BY usage_date DESC, user_id;

-- Grant access to authenticated users
GRANT SELECT ON public.ai_usage_daily TO authenticated;

-- ================================================
-- Comments for Documentation
-- ================================================

COMMENT ON TABLE public.ai_usage_log IS 'Tracks all OpenAI API calls for cost monitoring and rate limiting';
COMMENT ON COLUMN public.ai_usage_log.user_id IS 'User who triggered the call (NULL for automated system calls)';
COMMENT ON COLUMN public.ai_usage_log.agent_name IS 'AI agent that made the call (chart_watcher, journal_bot, etc.)';
COMMENT ON COLUMN public.ai_usage_log.cost IS 'Estimated cost in USD based on model pricing';
