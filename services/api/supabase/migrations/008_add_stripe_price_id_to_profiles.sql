-- Add stripe_price_id to profiles table
-- This tracks which Stripe price ID the user is subscribed to

ALTER TABLE public.profiles
ADD COLUMN IF NOT EXISTS stripe_price_id TEXT;

-- Add comment
COMMENT ON COLUMN public.profiles.stripe_price_id IS 'Stripe Price ID for the current subscription (e.g., price_1234...)';

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_profiles_stripe_customer_id ON public.profiles(stripe_customer_id);
CREATE INDEX IF NOT EXISTS idx_profiles_stripe_subscription_id ON public.profiles(stripe_subscription_id);
