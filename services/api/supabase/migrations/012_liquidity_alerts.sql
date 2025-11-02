-- =====================================================================
-- Migration: 012_liquidity_alerts.sql
-- Description: Liquidity Level Alert System
-- Created: 2025-11-01
--
-- Purpose:
--   - Enable realtime browser push notifications when price reaches
--     key liquidity levels (Yesterday High, Yesterday Low, Pivot Point)
--   - Support aggressive 1-minute price monitoring
--   - Manage user alert preferences and push subscriptions
--
-- Tables Created:
--   1. alerts - Stores alert rules and their current status
--   2. price_cache - Caches realtime prices to reduce API calls
--   3. alert_subscriptions - User alert preferences per symbol
--   4. user_push_subscriptions - Browser push notification subscriptions
--
-- Tables Modified:
--   1. eod_levels - Add pivot_point column
-- =====================================================================

-- =====================================================================
-- CLEANUP: Drop existing objects if they exist (from failed migrations)
-- =====================================================================

-- Drop tables first (CASCADE removes triggers, policies, and constraints automatically)
DROP TABLE IF EXISTS public.user_push_subscriptions CASCADE;
DROP TABLE IF EXISTS public.alert_subscriptions CASCADE;
DROP TABLE IF EXISTS public.price_cache CASCADE;
DROP TABLE IF EXISTS public.alerts CASCADE;

-- Drop functions (they depend on tables)
DROP FUNCTION IF EXISTS expire_old_alerts();
DROP FUNCTION IF EXISTS get_latest_eod_levels(UUID);
DROP FUNCTION IF EXISTS get_current_price(UUID);

-- Drop trigger functions
DROP FUNCTION IF EXISTS update_alerts_updated_at();
DROP FUNCTION IF EXISTS update_price_cache_updated_at();
DROP FUNCTION IF EXISTS update_alert_subscriptions_updated_at();

-- =====================================================================
-- 1. ALERTS TABLE
-- Stores alert rules and their current status
-- =====================================================================

CREATE TABLE public.alerts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  symbol_id UUID NOT NULL REFERENCES public.symbols(id) ON DELETE CASCADE,
  level_type TEXT NOT NULL CHECK (level_type IN ('yesterday_high', 'yesterday_low', 'pivot_point')),
  target_price NUMERIC(18,5) NOT NULL,
  direction TEXT NOT NULL CHECK (direction IN ('above', 'below', 'touch')),
  status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'triggered', 'cancelled', 'expired')),
  triggered_at TIMESTAMPTZ,
  expires_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_alerts_user_symbol ON public.alerts(user_id, symbol_id);
CREATE INDEX IF NOT EXISTS idx_alerts_status ON public.alerts(status);
CREATE INDEX IF NOT EXISTS idx_alerts_level_type ON public.alerts(level_type);
CREATE INDEX IF NOT EXISTS idx_alerts_triggered_at ON public.alerts(triggered_at);

-- Updated_at trigger
CREATE OR REPLACE FUNCTION update_alerts_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_alerts_updated_at ON public.alerts;
CREATE TRIGGER trigger_alerts_updated_at
  BEFORE UPDATE ON public.alerts
  FOR EACH ROW
  EXECUTE FUNCTION update_alerts_updated_at();

-- RLS Policies
ALTER TABLE public.alerts ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view own alerts" ON public.alerts;
CREATE POLICY "Users can view own alerts"
  ON public.alerts FOR SELECT
  USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can create own alerts" ON public.alerts;
CREATE POLICY "Users can create own alerts"
  ON public.alerts FOR INSERT
  WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own alerts" ON public.alerts;
CREATE POLICY "Users can update own alerts"
  ON public.alerts FOR UPDATE
  USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete own alerts" ON public.alerts;
CREATE POLICY "Users can delete own alerts"
  ON public.alerts FOR DELETE
  USING (auth.uid() = user_id);

-- =====================================================================
-- 2. PRICE_CACHE TABLE
-- Caches latest realtime prices to reduce API calls
-- =====================================================================

CREATE TABLE public.price_cache (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  symbol_id UUID NOT NULL REFERENCES public.symbols(id) ON DELETE CASCADE,
  current_price NUMERIC(18,5) NOT NULL,
  high_today NUMERIC(18,5),
  low_today NUMERIC(18,5),
  open_today NUMERIC(18,5),
  volume_today BIGINT,
  data_source TEXT NOT NULL CHECK (data_source IN ('finnhub', 'alpha_vantage')),
  fetched_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT unique_symbol_cache UNIQUE(symbol_id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_price_cache_symbol ON public.price_cache(symbol_id);
CREATE INDEX IF NOT EXISTS idx_price_cache_updated ON public.price_cache(updated_at);
CREATE INDEX IF NOT EXISTS idx_price_cache_data_source ON public.price_cache(data_source);

-- Updated_at trigger
CREATE OR REPLACE FUNCTION update_price_cache_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_price_cache_updated_at ON public.price_cache;
CREATE TRIGGER trigger_price_cache_updated_at
  BEFORE UPDATE ON public.price_cache
  FOR EACH ROW
  EXECUTE FUNCTION update_price_cache_updated_at();

-- RLS Policies
ALTER TABLE public.price_cache ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Anyone can read price cache" ON public.price_cache;
CREATE POLICY "Anyone can read price cache"
  ON public.price_cache FOR SELECT
  USING (true);

-- Only service role can insert/update price cache (backend only)
DROP POLICY IF EXISTS "Service role can manage price cache" ON public.price_cache;
CREATE POLICY "Service role can manage price cache"
  ON public.price_cache FOR ALL
  USING (auth.role() = 'service_role');

-- =====================================================================
-- 3. ALERT_SUBSCRIPTIONS TABLE
-- Tracks which alert types users want to receive
-- =====================================================================

CREATE TABLE public.alert_subscriptions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  symbol_id UUID NOT NULL REFERENCES public.symbols(id) ON DELETE CASCADE,
  yesterday_high_enabled BOOLEAN NOT NULL DEFAULT true,
  yesterday_low_enabled BOOLEAN NOT NULL DEFAULT true,
  pivot_point_enabled BOOLEAN NOT NULL DEFAULT false,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT unique_user_symbol_subscription UNIQUE(user_id, symbol_id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_alert_subs_user ON public.alert_subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_alert_subs_symbol ON public.alert_subscriptions(symbol_id);
CREATE INDEX IF NOT EXISTS idx_alert_subs_user_symbol ON public.alert_subscriptions(user_id, symbol_id);

-- Updated_at trigger
CREATE OR REPLACE FUNCTION update_alert_subscriptions_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_alert_subscriptions_updated_at ON public.alert_subscriptions;
CREATE TRIGGER trigger_alert_subscriptions_updated_at
  BEFORE UPDATE ON public.alert_subscriptions
  FOR EACH ROW
  EXECUTE FUNCTION update_alert_subscriptions_updated_at();

-- RLS Policies
ALTER TABLE public.alert_subscriptions ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can manage own subscriptions" ON public.alert_subscriptions;
CREATE POLICY "Users can manage own subscriptions"
  ON public.alert_subscriptions FOR ALL
  USING (auth.uid() = user_id);

-- =====================================================================
-- 4. USER_PUSH_SUBSCRIPTIONS TABLE
-- Stores browser push notification subscriptions (Web Push API)
-- =====================================================================

CREATE TABLE public.user_push_subscriptions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  endpoint TEXT NOT NULL,
  p256dh TEXT NOT NULL,  -- Public key for encryption
  auth TEXT NOT NULL,    -- Auth secret for encryption
  user_agent TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  last_used_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT unique_endpoint UNIQUE(endpoint)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_push_subs_user ON public.user_push_subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_push_subs_endpoint ON public.user_push_subscriptions(endpoint);
CREATE INDEX IF NOT EXISTS idx_push_subs_last_used ON public.user_push_subscriptions(last_used_at);

-- RLS Policies
ALTER TABLE public.user_push_subscriptions ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can manage own push subscriptions" ON public.user_push_subscriptions;
CREATE POLICY "Users can manage own push subscriptions"
  ON public.user_push_subscriptions FOR ALL
  USING (auth.uid() = user_id);

-- =====================================================================
-- 5. UPDATE EOD_LEVELS TABLE
-- Add Pivot Point calculation (if not already present)
-- =====================================================================

-- Add pivot_point column
ALTER TABLE public.eod_levels
ADD COLUMN IF NOT EXISTS pivot_point NUMERIC(18,5);

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_eod_levels_pivot_point ON public.eod_levels(pivot_point);

-- Update existing records with Pivot Point calculation
-- Pivot Point = (High + Low + Close) / 3
UPDATE public.eod_levels
SET pivot_point = (yesterday_high + yesterday_low + yesterday_close) / 3
WHERE pivot_point IS NULL;

-- =====================================================================
-- 6. UTILITY FUNCTIONS
-- Helper functions for alert system
-- =====================================================================

-- Function to automatically expire old alerts
CREATE OR REPLACE FUNCTION expire_old_alerts()
RETURNS void AS $$
BEGIN
  UPDATE public.alerts
  SET status = 'expired'
  WHERE status = 'active'
    AND expires_at IS NOT NULL
    AND expires_at < NOW();
END;
$$ LANGUAGE plpgsql;

-- Function to get latest EOD levels for a symbol
CREATE OR REPLACE FUNCTION get_latest_eod_levels(p_symbol_id UUID)
RETURNS TABLE (
  trade_date DATE,
  yesterday_high NUMERIC(18,5),
  yesterday_low NUMERIC(18,5),
  yesterday_close NUMERIC(18,5),
  pivot_point NUMERIC(18,5)
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    el.trade_date,
    el.yesterday_high,
    el.yesterday_low,
    el.yesterday_close,
    el.pivot_point
  FROM public.eod_levels el
  WHERE el.symbol_id = p_symbol_id
  ORDER BY el.trade_date DESC
  LIMIT 1;
END;
$$ LANGUAGE plpgsql;

-- Function to get current cached price for a symbol
CREATE OR REPLACE FUNCTION get_current_price(p_symbol_id UUID)
RETURNS TABLE (
  current_price NUMERIC(18,5),
  high_today NUMERIC(18,5),
  low_today NUMERIC(18,5),
  open_today NUMERIC(18,5),
  updated_at TIMESTAMPTZ
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    pc.current_price,
    pc.high_today,
    pc.low_today,
    pc.open_today,
    pc.updated_at
  FROM public.price_cache pc
  WHERE pc.symbol_id = p_symbol_id
  LIMIT 1;
END;
$$ LANGUAGE plpgsql;

-- =====================================================================
-- 7. COMMENTS (Documentation)
-- =====================================================================

COMMENT ON TABLE public.alerts IS 'Stores alert rules and their current status for liquidity level notifications';
COMMENT ON TABLE public.price_cache IS 'Caches latest realtime prices to reduce API calls (updated every 1 minute)';
COMMENT ON TABLE public.alert_subscriptions IS 'User preferences for which alert types to receive per symbol';
COMMENT ON TABLE public.user_push_subscriptions IS 'Browser push notification subscriptions (Web Push API)';

COMMENT ON COLUMN public.alerts.level_type IS 'Type of liquidity level: yesterday_high, yesterday_low, or pivot_point';
COMMENT ON COLUMN public.alerts.direction IS 'Price direction to trigger alert: above, below, or touch';
COMMENT ON COLUMN public.alerts.status IS 'Alert status: active, triggered, cancelled, or expired';

COMMENT ON COLUMN public.price_cache.data_source IS 'API source: finnhub (indices) or alpha_vantage (forex)';
COMMENT ON COLUMN public.price_cache.fetched_at IS 'Timestamp when price was fetched from API';

COMMENT ON COLUMN public.user_push_subscriptions.endpoint IS 'Push subscription endpoint URL (unique per device)';
COMMENT ON COLUMN public.user_push_subscriptions.p256dh IS 'Public key for Web Push encryption (p256dh)';
COMMENT ON COLUMN public.user_push_subscriptions.auth IS 'Auth secret for Web Push encryption';

COMMENT ON COLUMN public.eod_levels.pivot_point IS 'Pivot Point = (Yesterday High + Yesterday Low + Yesterday Close) / 3';

COMMENT ON FUNCTION expire_old_alerts() IS 'Marks alerts as expired if past their expiration date';
COMMENT ON FUNCTION get_latest_eod_levels(UUID) IS 'Returns the most recent EOD levels for a given symbol';
COMMENT ON FUNCTION get_current_price(UUID) IS 'Returns the current cached price for a given symbol';

-- =====================================================================
-- MIGRATION COMPLETE
-- =====================================================================

-- Summary:
-- ✅ Created alerts table with RLS policies
-- ✅ Created price_cache table with RLS policies
-- ✅ Created alert_subscriptions table with RLS policies
-- ✅ Created user_push_subscriptions table with RLS policies
-- ✅ Updated eod_levels table with pivot_point column
-- ✅ Created indexes for performance optimization
-- ✅ Created updated_at triggers for all tables
-- ✅ Created utility functions for alert management
-- ✅ Added comprehensive documentation comments
