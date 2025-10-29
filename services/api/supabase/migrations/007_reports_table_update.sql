-- ================================================
-- Migration 007: Reports Table Update
-- ================================================
-- Purpose: Add missing columns for JournalBot automated reports
-- Created: 2025-10-29
-- Author: TradeMatrix.ai Development Team
-- ================================================

-- Add report_date column if it doesn't exist
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public'
    AND table_name = 'reports'
    AND column_name = 'report_date'
  ) THEN
    ALTER TABLE public.reports ADD COLUMN report_date DATE;
  END IF;
END $$;

-- Add file_url_docx column if it doesn't exist
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public'
    AND table_name = 'reports'
    AND column_name = 'file_url_docx'
  ) THEN
    ALTER TABLE public.reports ADD COLUMN file_url_docx TEXT;
  END IF;
END $$;

-- Add metrics column if it doesn't exist
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public'
    AND table_name = 'reports'
    AND column_name = 'metrics'
  ) THEN
    ALTER TABLE public.reports ADD COLUMN metrics JSONB DEFAULT '{}';
  END IF;
END $$;

-- Create indexes if they don't exist
CREATE INDEX IF NOT EXISTS idx_reports_user_id ON public.reports(user_id);
CREATE INDEX IF NOT EXISTS idx_reports_date ON public.reports(report_date DESC);
CREATE INDEX IF NOT EXISTS idx_reports_type ON public.reports(report_type);
CREATE INDEX IF NOT EXISTS idx_reports_created_at ON public.reports(created_at DESC);

-- Update report_type constraint to include 'monthly'
ALTER TABLE public.reports DROP CONSTRAINT IF EXISTS reports_report_type_check;
ALTER TABLE public.reports ADD CONSTRAINT reports_report_type_check
  CHECK (report_type IN ('daily', 'weekly', 'monthly', 'analysis', 'custom'));

-- ================================================
-- COMMENTS
-- ================================================

COMMENT ON COLUMN public.reports.report_date IS 'Date for which report was generated (for automated reports)';
COMMENT ON COLUMN public.reports.file_url_docx IS 'Public URL to DOCX report in Supabase Storage';
COMMENT ON COLUMN public.reports.metrics IS 'Performance metrics JSON (total_trades, win_rate, pnl, etc.)';

-- ================================================
-- END OF MIGRATION 007
-- ================================================
