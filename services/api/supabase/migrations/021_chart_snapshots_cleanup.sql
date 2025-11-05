-- =============================================
-- Migration 021: Auto-cleanup expired chart snapshots
-- Created: 2025-11-05
-- Description: Function to delete expired chart snapshots (60+ days old)
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
    -- Delete snapshots where expires_at is in the past
    DELETE FROM chart_snapshots
    WHERE expires_at < NOW();

    -- Get count of deleted rows
    GET DIAGNOSTICS deleted_count = ROW_COUNT;

    -- Log the operation
    RAISE NOTICE 'Deleted % expired chart snapshots', deleted_count;

    RETURN deleted_count;
END;
$$;

COMMENT ON FUNCTION cleanup_expired_chart_snapshots
IS 'Deletes chart snapshots where expires_at < NOW(). Returns count of deleted rows. Run daily via pg_cron or manually.';

-- Verify function creation
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_proc
        WHERE proname = 'cleanup_expired_chart_snapshots'
    ) THEN
        RAISE NOTICE '✅ Function cleanup_expired_chart_snapshots created successfully';
    ELSE
        RAISE EXCEPTION '❌ Function cleanup_expired_chart_snapshots not found!';
    END IF;
END $$;

COMMIT;

-- =============================================
-- USAGE INSTRUCTIONS
-- =============================================

-- Manual execution:
-- SELECT cleanup_expired_chart_snapshots();

-- Schedule daily cleanup (requires pg_cron extension):
-- If pg_cron is available in Supabase, run this in SQL Editor:
-- SELECT cron.schedule(
--     'cleanup-chart-snapshots',           -- Job name
--     '0 2 * * *',                         -- Cron schedule (daily at 2:00 AM UTC)
--     'SELECT cleanup_expired_chart_snapshots();'
-- );

-- Check scheduled jobs (if pg_cron is available):
-- SELECT * FROM cron.job WHERE jobname = 'cleanup-chart-snapshots';

-- Unschedule job (if needed):
-- SELECT cron.unschedule('cleanup-chart-snapshots');

-- =============================================
-- ALTERNATIVE: Manual cleanup via Edge Function
-- =============================================

-- If pg_cron is not available, create a Supabase Edge Function
-- that runs daily via GitHub Actions or external cron service:
--
-- 1. Create file: supabase/functions/cleanup-charts/index.ts
-- 2. Deploy: supabase functions deploy cleanup-charts
-- 3. Schedule via GitHub Actions or external cron (e.g., cron-job.org)
--
-- Edge Function code:
-- import { createClient } from '@supabase/supabase-js'
--
-- Deno.serve(async (req) => {
--   const supabase = createClient(
--     Deno.env.get('SUPABASE_URL')!,
--     Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
--   )
--
--   const { data, error } = await supabase.rpc('cleanup_expired_chart_snapshots')
--
--   return new Response(
--     JSON.stringify({ deleted: data, error }),
--     { headers: { 'Content-Type': 'application/json' } }
--   )
-- })

-- =============================================
-- TEST QUERIES
-- =============================================

-- Count expired snapshots (without deleting)
-- SELECT COUNT(*) AS expired_count
-- FROM chart_snapshots
-- WHERE expires_at < NOW();

-- View expired snapshots (without deleting)
-- SELECT id, symbol_id, timeframe, created_by_agent, created_at, expires_at
-- FROM chart_snapshots
-- WHERE expires_at < NOW()
-- ORDER BY expires_at ASC
-- LIMIT 10;

-- Manually set expiration date for testing
-- UPDATE chart_snapshots
-- SET expires_at = NOW() - INTERVAL '1 day'
-- WHERE id = 'test-snapshot-uuid';

-- Test cleanup function
-- SELECT cleanup_expired_chart_snapshots();
