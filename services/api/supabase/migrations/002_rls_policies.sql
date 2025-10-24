-- TradeMatrix.ai Row Level Security Policies
-- Ensures users can only access their own data

-- Enable RLS on all tables
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.trades ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.agent_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.subscriptions ENABLE ROW LEVEL SECURITY;

-- Profiles policies
CREATE POLICY "Users can view own profile"
    ON public.profiles FOR SELECT
    USING (auth.uid() = id);

CREATE POLICY "Users can update own profile"
    ON public.profiles FOR UPDATE
    USING (auth.uid() = id);

CREATE POLICY "Users can insert own profile"
    ON public.profiles FOR INSERT
    WITH CHECK (auth.uid() = id);

-- Trades policies
CREATE POLICY "Users can view own trades"
    ON public.trades FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own trades"
    ON public.trades FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own trades"
    ON public.trades FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own trades"
    ON public.trades FOR DELETE
    USING (auth.uid() = user_id);

-- Reports policies
CREATE POLICY "Users can view own reports"
    ON public.reports FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Published reports are public"
    ON public.reports FOR SELECT
    USING (status = 'published');

CREATE POLICY "Users can insert own reports"
    ON public.reports FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own reports"
    ON public.reports FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own reports"
    ON public.reports FOR DELETE
    USING (auth.uid() = user_id);

-- Agent logs policies
CREATE POLICY "Users can view own agent logs"
    ON public.agent_logs FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "System can insert agent logs"
    ON public.agent_logs FOR INSERT
    WITH CHECK (true);  -- Service role only via backend

-- Subscriptions policies
CREATE POLICY "Users can view own subscriptions"
    ON public.subscriptions FOR SELECT
    USING (auth.uid() = user_id);

-- Storage policies (for charts and PDFs)
-- Run these in Supabase Dashboard > Storage > Policies

-- Bucket: charts
-- Policy: Users can upload own charts
-- INSERT: bucket_id = 'charts' AND auth.uid()::text = (storage.foldername(name))[1]

-- Policy: Users can view own charts
-- SELECT: bucket_id = 'charts' AND auth.uid()::text = (storage.foldername(name))[1]

-- Policy: Published charts are public
-- SELECT: bucket_id = 'charts' AND (storage.foldername(name))[2] = 'public'

-- Bucket: reports
-- Policy: Users can upload own reports
-- INSERT: bucket_id = 'reports' AND auth.uid()::text = (storage.foldername(name))[1]

-- Policy: Users can view own reports
-- SELECT: bucket_id = 'reports' AND auth.uid()::text = (storage.foldername(name))[1]

-- Policy: Published reports are public
-- SELECT: bucket_id = 'reports' AND (storage.foldername(name))[2] = 'public'
