-- =====================================================
-- Migration 015: Extend Reports Schema for AI Trading Reports
-- =====================================================
-- Description: Extends report_type and status enums to support
--              automated trading reports (daily, weekly, monthly,
--              trade analysis, risk assessment)
-- Author: TradeMatrix.ai
-- Date: 2025-11-02
-- =====================================================

-- 1. Drop existing CHECK constraints
ALTER TABLE public.reports DROP CONSTRAINT IF EXISTS reports_report_type_check;
ALTER TABLE public.reports DROP CONSTRAINT IF EXISTS reports_status_check;

-- 2. Add new CHECK constraints with extended values
ALTER TABLE public.reports
ADD CONSTRAINT reports_report_type_check
CHECK (report_type IN (
    'daily',           -- Daily trading summary
    'weekly',          -- Weekly performance analysis
    'monthly',         -- Monthly review (NEW)
    'analysis',        -- General analysis (existing)
    'custom',          -- Custom reports (existing)
    'trade_analysis',  -- Individual trade breakdown (NEW)
    'risk_assessment'  -- Portfolio risk evaluation (NEW)
));

ALTER TABLE public.reports
ADD CONSTRAINT reports_status_check
CHECK (status IN (
    'draft',       -- Report in draft mode (existing)
    'published',   -- Published to blog (existing)
    'archived',    -- Archived (existing)
    'processing',  -- AI is generating report (NEW)
    'completed',   -- Report generated successfully (NEW)
    'failed'       -- Generation failed (NEW)
));

-- 3. Add metrics column for structured data
ALTER TABLE public.reports
ADD COLUMN IF NOT EXISTS metrics JSONB DEFAULT '{}'::jsonb;

-- Add comment
COMMENT ON COLUMN public.reports.metrics IS 'Structured trading metrics (win_rate, profit_loss, roi, etc.)';

-- 4. Create index on status for faster queries
CREATE INDEX IF NOT EXISTS idx_reports_status ON public.reports(status);
CREATE INDEX IF NOT EXISTS idx_reports_report_type ON public.reports(report_type);
CREATE INDEX IF NOT EXISTS idx_reports_created_at ON public.reports(created_at DESC);

-- 5. Update existing reports to use new status if needed
-- (Safe migration - only updates NULL status)
UPDATE public.reports
SET status = 'completed'
WHERE status IS NULL;

-- =====================================================
-- End of Migration 015
-- =====================================================
