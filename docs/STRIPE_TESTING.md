# Stripe Testing Guide

This guide covers how to test the Stripe integration for TradeMatrix.ai.

## Test Mode vs Live Mode

- **Test Mode**: Use test API keys and test cards. No real money is charged.
- **Live Mode**: Use live API keys and real cards. Real money is charged.

Always develop and test in **Test Mode**!

## Stripe Test Cards

Stripe provides test card numbers for different scenarios:

### Successful Payments

| Card Number | Brand | Description |
|------------|-------|-------------|
| `4242 4242 4242 4242` | Visa | Standard success |
| `5555 5555 5555 4444` | Mastercard | Standard success |
| `3782 822463 10005` | American Express | Standard success |

### Testing 3D Secure

| Card Number | Brand | 3D Secure Behavior |
|------------|-------|-------------------|
| `4000 0027 6000 3184` | Visa | 3D Secure required |
| `4000 0025 0000 3155` | Visa | 3D Secure supported |

### Payment Failures

| Card Number | Error Type |
|------------|------------|
| `4000 0000 0000 9995` | Insufficient funds |
| `4000 0000 0000 9987` | Lost card |
| `4000 0000 0000 9979` | Stolen card |
| `4000 0000 0000 0069` | Card declined (generic) |
| `4000 0000 0000 0127` | Incorrect CVC |
| `4000 0000 0000 0119` | Processing error |

### Subscription-Specific Testing

| Card Number | Behavior |
|------------|----------|
| `4000 0000 0000 0341` | Charge succeeds and funds added to account after 7 days |
| `4000 0000 0000 1976` | Charge succeeds and funds added to account after 1 minute (for testing) |

### Additional Test Details

For all test cards:
- **Expiration Date**: Any future date (e.g., 12/34)
- **CVC**: Any 3 digits (e.g., 123)
- **ZIP/Postal Code**: Any valid code (e.g., 12345)

## Testing Scenarios

### 1. Test Successful Subscription

1. Navigate to `/dashboard/profile`
2. Scroll to "Billing & Subscription" section
3. Click "Upgrade Now" on any tier
4. Use test card: `4242 4242 4242 4242`
5. Enter:
   - Expiration: `12/34`
   - CVC: `123`
   - ZIP: `12345`
6. Click "Subscribe"

**Expected Results:**
- Redirected to success page
- Subscription tier updated in profile
- Stripe customer ID saved
- Webhook event logged

### 2. Test Payment Failure

1. Start subscription flow
2. Use test card: `4000 0000 0000 9995` (insufficient funds)
3. Attempt payment

**Expected Results:**
- Payment fails
- Error message displayed
- No subscription created
- User remains on free tier

### 3. Test Subscription Cancellation

1. Have an active paid subscription
2. Go to `/dashboard/profile`
3. Click "Manage Subscription" button
4. Click "Cancel plan" in Stripe portal
5. Confirm cancellation

**Expected Results:**
- Subscription marked as `cancel_at_period_end: true`
- User can still access features until period ends
- Webhook event received
- Database updated

### 4. Test Payment Method Update

1. Have an active subscription
2. Click "Manage Subscription"
3. Click "Update payment method"
4. Enter new test card
5. Save changes

**Expected Results:**
- Payment method updated
- No new charge
- Confirmation shown

### 5. Test Failed Payment (Subscription Renewal)

You can simulate this using Stripe Dashboard:

1. Go to Stripe Dashboard → Customers
2. Find your test customer
3. Click on active subscription
4. Click "..." → "Update subscription"
5. Change card to failing card: `4000 0000 0000 0341`
6. Trigger invoice payment

**Expected Results:**
- Payment fails
- Subscription status: `past_due`
- Webhook event received
- User profile updated

## Local Webhook Testing

### Setup Stripe CLI

```bash
# Install (macOS)
brew install stripe/stripe-cli/stripe

# Install (Linux)
wget https://github.com/stripe/stripe-cli/releases/download/vX.X.X/stripe_X.X.X_linux_x86_64.tar.gz
tar -xvf stripe_X.X.X_linux_x86_64.tar.gz
sudo mv stripe /usr/local/bin

# Install (Windows)
# Download from https://github.com/stripe/stripe-cli/releases
```

### Forward Webhooks Locally

```bash
# Login to Stripe
stripe login

# Forward webhooks to local server
stripe listen --forward-to localhost:3000/api/stripe/webhook

# You'll see output like:
# > Ready! Your webhook signing secret is whsec_xxxxx
# Copy this secret to your .env.local as STRIPE_WEBHOOK_SECRET
```

Keep this terminal open while testing!

### Trigger Webhook Events Manually

```bash
# Trigger checkout.session.completed
stripe trigger checkout.session.completed

# Trigger subscription updated
stripe trigger customer.subscription.updated

# Trigger subscription deleted
stripe trigger customer.subscription.deleted

# Trigger payment succeeded
stripe trigger invoice.payment_succeeded

# Trigger payment failed
stripe trigger invoice.payment_failed
```

## Testing Checklist

### Initial Setup
- [ ] Stripe CLI installed
- [ ] Webhook forwarding active (`stripe listen`)
- [ ] All environment variables set
- [ ] Database migration applied

### Subscription Flow
- [ ] Create subscription (Starter tier)
- [ ] Verify redirect to success page
- [ ] Check profile shows correct tier
- [ ] Verify webhook received
- [ ] Check Stripe customer created

### Feature Access
- [ ] Verify free tier restrictions work
- [ ] Upgrade to Starter and verify access
- [ ] Try accessing Pro features (should be blocked)
- [ ] Upgrade to Pro and verify access

### Billing Portal
- [ ] Open billing portal
- [ ] View invoice history
- [ ] Update payment method
- [ ] Cancel subscription
- [ ] Reactivate subscription

### Webhooks
- [ ] `checkout.session.completed` - Creates subscription
- [ ] `customer.subscription.updated` - Updates subscription
- [ ] `customer.subscription.deleted` - Cancels subscription
- [ ] `invoice.payment_succeeded` - Sets status to active
- [ ] `invoice.payment_failed` - Sets status to past_due

### Edge Cases
- [ ] Multiple tab checkout (concurrent sessions)
- [ ] Expired card during renewal
- [ ] Downgrade request (should show not available)
- [ ] Already subscribed to same tier
- [ ] Webhook signature verification failure

## Monitoring Webhooks

### Stripe Dashboard

1. Go to **Developers** → **Webhooks**
2. Click on your endpoint
3. View recent webhook events
4. Check delivery status
5. Inspect request/response

### Application Logs

Check your server logs for webhook processing:

```bash
# Watch logs during testing
npm run dev

# Look for:
# "Received webhook event: checkout.session.completed"
# "Subscription created for user abc123"
```

### Database Verification

After each webhook event, verify database state:

```sql
-- Check profile
SELECT
  id,
  email,
  subscription_tier,
  subscription_status,
  stripe_customer_id,
  stripe_subscription_id,
  stripe_price_id
FROM profiles
WHERE email = 'test@example.com';

-- Check subscription record
SELECT *
FROM subscriptions
WHERE user_id = 'user-id-here'
ORDER BY created_at DESC;
```

## Common Issues & Solutions

### Issue: "Invalid webhook signature"

**Solution:**
- Restart webhook listener: `stripe listen --forward-to localhost:3000/api/stripe/webhook`
- Copy new webhook secret to `.env.local`
- Restart dev server

### Issue: Webhook not received

**Solution:**
- Check Stripe CLI is running
- Verify endpoint URL is correct
- Check firewall/network settings
- Review Stripe Dashboard webhook logs

### Issue: Payment succeeds but subscription not created

**Solution:**
- Check webhook handler logs
- Verify SUPABASE_SERVICE_ROLE_KEY is set
- Check database permissions
- Review webhook event data

### Issue: "No Stripe price ID configured"

**Solution:**
- Add price IDs to `.env.local`
- Restart dev server
- Verify price IDs match those in Stripe Dashboard

## Test Data Cleanup

After testing, you may want to clean up test data:

### Stripe Dashboard

1. Go to **Customers**
2. Delete test customers
3. Go to **Subscriptions**
4. Cancel test subscriptions

### Database

```sql
-- WARNING: Only run in development!

-- Delete test subscriptions
DELETE FROM subscriptions
WHERE stripe_subscription_id LIKE 'sub_test%';

-- Reset test user to free tier
UPDATE profiles
SET
  subscription_tier = 'free',
  subscription_status = 'active',
  stripe_customer_id = NULL,
  stripe_subscription_id = NULL,
  stripe_price_id = NULL
WHERE email = 'test@example.com';
```

## Production Testing

Before going live:

1. **Test with live mode in sandbox**
   - Switch to live API keys
   - Use real card (with small amount)
   - Test complete flow
   - Cancel immediately after testing

2. **Verify webhook endpoint**
   - Ensure production webhook URL is accessible
   - Test webhook signature verification
   - Monitor webhook delivery

3. **Test error handling**
   - Simulate payment failures
   - Test network issues
   - Verify error messages to users

4. **Load testing**
   - Test concurrent checkouts
   - Verify webhook queue handling
   - Check database performance

## Useful Stripe CLI Commands

```bash
# List recent events
stripe events list

# Get event details
stripe events retrieve evt_xxxxx

# List customers
stripe customers list

# Get customer details
stripe customers retrieve cus_xxxxx

# List subscriptions
stripe subscriptions list

# Cancel subscription
stripe subscriptions cancel sub_xxxxx

# Test webhook locally
stripe trigger customer.subscription.updated
```

## Additional Resources

- [Stripe Testing Documentation](https://stripe.com/docs/testing)
- [Test Card Numbers](https://stripe.com/docs/testing#cards)
- [Stripe CLI Documentation](https://stripe.com/docs/stripe-cli)
- [Webhook Testing](https://stripe.com/docs/webhooks/test)

## Support

If you encounter issues during testing:
1. Check Stripe Dashboard logs
2. Review application server logs
3. Verify database state
4. Test with Stripe CLI triggers
5. Consult [STRIPE_SETUP.md](./STRIPE_SETUP.md) for configuration
