-- ================================================
-- Migration 004: Add US Open Planner to agent_logs
-- ================================================
-- Purpose: Update agent_logs table constraint to include 'us_open_planner' agent type
-- Created: 2025-10-29
-- Author: TradeMatrix.ai Development Team
-- ================================================

-- Drop existing CHECK constraint on agent_type
ALTER TABLE public.agent_logs
DROP CONSTRAINT IF EXISTS agent_logs_agent_type_check;

-- Add updated CHECK constraint with us_open_planner included
ALTER TABLE public.agent_logs
ADD CONSTRAINT agent_logs_agent_type_check
CHECK (agent_type IN (
    'chart_watcher',
    'signal_bot',
    'risk_manager',
    'journal_bot',
    'publisher',
    'us_open_planner'
));

-- Add comment
COMMENT ON CONSTRAINT agent_logs_agent_type_check ON public.agent_logs IS 'Valid agent types including US Open Planner';

-- ================================================
-- END OF MIGRATION 004
-- ================================================
