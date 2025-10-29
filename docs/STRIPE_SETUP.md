# Stripe Integration Setup Guide

This guide will walk you through setting up Stripe for TradeMatrix.ai subscription payments.

## Prerequisites

- A Stripe account (create at [stripe.com](https://stripe.com))
- Supabase project set up
- Next.js application running locally

## Step 1: Create Stripe Account

1. Sign up at [stripe.com](https://stripe.com)
2. Complete account verification
3. Switch to **Test Mode** for development (toggle in top-right corner)

## Step 2: Get Stripe API Keys

1. Go to **Developers** → **API keys** in Stripe Dashboard
2. Copy your keys:
   - **Publishable key** (starts with `pk_test_...`)
   - **Secret key** (starts with `sk_test_...`)

3. Add to your `.env.local` file:

```bash
# Stripe Configuration
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_your_key_here
STRIPE_SECRET_KEY=sk_test_your_secret_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here
```

## Step 3: Create Products and Prices

### Option A: Via Stripe Dashboard (Recommended)

1. Go to **Products** in Stripe Dashboard
2. Click **+ Add product**

Create the following products:

#### Starter Plan
- **Name**: TradeMatrix Starter
- **Description**: Daily reports and email alerts for active traders
- **Pricing**:
  - Amount: €29.00
  - Billing period: Monthly
  - Type: Recurring
- **Save the Price ID** (e.g., `price_1234...`)

#### Pro Plan
- **Name**: TradeMatrix Pro
- **Description**: Advanced features with backtesting and API access
- **Pricing**:
  - Amount: €79.00
  - Billing period: Monthly
  - Type: Recurring
- **Save the Price ID** (e.g., `price_5678...`)

#### Expert Plan
- **Name**: TradeMatrix Expert
- **Description**: Full suite for trading firms and experts
- **Pricing**:
  - Amount: €199.00
  - Billing period: Monthly
  - Type: Recurring
- **Save the Price ID** (e.g., `price_9012...`)

### Option B: Via Stripe CLI (Advanced)

```bash
# Install Stripe CLI
brew install stripe/stripe-cli/stripe

# Login
stripe login

# Create products
stripe products create \
  --name="TradeMatrix Starter" \
  --description="Daily reports and email alerts"

stripe prices create \
  --product=prod_XXX \
  --unit-amount=2900 \
  --currency=eur \
  --recurring[interval]=month

# Repeat for Pro and Expert tiers
```

## Step 4: Add Price IDs to Environment

Add the Price IDs to your `.env.local`:

```bash
# Stripe Price IDs
NEXT_PUBLIC_STRIPE_PRICE_STARTER=price_1234starter
NEXT_PUBLIC_STRIPE_PRICE_PRO=price_5678pro
NEXT_PUBLIC_STRIPE_PRICE_EXPERT=price_9012expert
```

## Step 5: Configure Stripe Webhooks

Webhooks allow Stripe to notify your app about subscription changes.

### Local Development (with Stripe CLI)

1. Install Stripe CLI (if not already):
```bash
brew install stripe/stripe-cli/stripe
```

2. Login to Stripe CLI:
```bash
stripe login
```

3. Forward webhooks to your local server:
```bash
stripe listen --forward-to localhost:3000/api/stripe/webhook
```

4. Copy the webhook signing secret (starts with `whsec_...`) and add to `.env.local`:
```bash
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here
```

5. Keep the CLI running while developing!

### Production Deployment

1. Go to **Developers** → **Webhooks** in Stripe Dashboard
2. Click **+ Add endpoint**
3. Enter your webhook URL:
   ```
   https://your-domain.com/api/stripe/webhook
   ```

4. Select events to listen to:
   - `checkout.session.completed`
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`

5. Click **Add endpoint**
6. Copy the **Signing secret** and add to production environment variables

## Step 6: Run Database Migration

The Stripe integration requires an additional field in the profiles table:

```sql
-- Run in Supabase SQL Editor
-- File: services/api/supabase/migrations/008_add_stripe_price_id_to_profiles.sql

ALTER TABLE public.profiles
ADD COLUMN IF NOT EXISTS stripe_price_id TEXT;

COMMENT ON COLUMN public.profiles.stripe_price_id IS 'Stripe Price ID for the current subscription (e.g., price_1234...)';

CREATE INDEX IF NOT EXISTS idx_profiles_stripe_customer_id ON public.profiles(stripe_customer_id);
CREATE INDEX IF NOT EXISTS idx_profiles_stripe_subscription_id ON public.profiles(stripe_subscription_id);
```

## Step 7: Test the Integration

1. Start your development server:
```bash
cd apps/web
npm run dev
```

2. Start Stripe webhook forwarding:
```bash
stripe listen --forward-to localhost:3000/api/stripe/webhook
```

3. Navigate to your app:
```
http://localhost:3000/dashboard/profile
```

4. Scroll to the "Billing & Subscription" section
5. Click "Upgrade Now" on any paid tier
6. Use Stripe test cards (see [STRIPE_TESTING.md](./STRIPE_TESTING.md))

## Step 8: Enable Billing Portal

The Customer Portal allows users to manage their subscriptions.

1. Go to **Settings** → **Billing** → **Customer Portal** in Stripe Dashboard
2. Click **Activate test link** or **Activate portal**
3. Configure portal settings:
   - Enable "Cancel subscriptions"
   - Enable "Update payment methods"
   - Enable "View invoice history"
4. Save settings

## Step 9: Production Checklist

Before going live:

- [ ] Switch Stripe from Test Mode to Live Mode
- [ ] Update all API keys in production environment
- [ ] Set up production webhook endpoint
- [ ] Test complete subscription flow with real card
- [ ] Verify webhook events are received
- [ ] Test subscription cancellation
- [ ] Test payment failure scenarios
- [ ] Enable Stripe Radar for fraud prevention
- [ ] Set up email receipts in Stripe Dashboard
- [ ] Configure tax settings (if applicable)

## Environment Variables Summary

Your final `.env.local` should include:

```bash
# Supabase
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Stripe
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Stripe Price IDs
NEXT_PUBLIC_STRIPE_PRICE_STARTER=price_...
NEXT_PUBLIC_STRIPE_PRICE_PRO=price_...
NEXT_PUBLIC_STRIPE_PRICE_EXPERT=price_...
```

## Troubleshooting

### "No Stripe price ID configured"
- Make sure you've added all three price IDs to `.env.local`
- Restart your dev server after adding environment variables

### Webhook not receiving events
- Check Stripe CLI is running: `stripe listen --forward-to localhost:3000/api/stripe/webhook`
- Verify webhook secret is correct in `.env.local`
- Check webhook logs in Stripe Dashboard

### "Failed to create checkout session"
- Verify STRIPE_SECRET_KEY is set correctly
- Check browser console for errors
- Verify user is logged in

### Subscription not updating in database
- Check webhook events in Stripe Dashboard → Developers → Webhooks
- Verify webhook signature is valid
- Check server logs for errors
- Ensure SUPABASE_SERVICE_ROLE_KEY is set (required for webhooks)

## Additional Resources

- [Stripe Documentation](https://stripe.com/docs)
- [Stripe Testing Guide](https://stripe.com/docs/testing)
- [Stripe Webhooks](https://stripe.com/docs/webhooks)
- [Stripe Customer Portal](https://stripe.com/docs/billing/subscriptions/customer-portal)

## Support

For issues specific to this integration:
1. Check [STRIPE_TESTING.md](./STRIPE_TESTING.md) for testing scenarios
2. Review server logs for errors
3. Check Stripe Dashboard for event logs
4. Verify all environment variables are set correctly
