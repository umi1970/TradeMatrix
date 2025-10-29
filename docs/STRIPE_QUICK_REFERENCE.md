# Stripe Integration - Quick Reference

One-page reference for using the Stripe integration in TradeMatrix.ai.

---

## Import Statements

```typescript
// Feature gating
import { canAccessFeature, FEATURES, getTierLimits, hasReachedLimit } from '@/lib/subscription'

// Subscription hook
import { useSubscription } from '@/hooks/use-subscription'

// UI Components
import { SubscriptionPlans } from '@/components/billing/SubscriptionPlans'
import { BillingPortal } from '@/components/billing/BillingPortal'
import { UpgradePrompt, LimitReachedPrompt } from '@/components/billing/UpgradePrompt'
```

---

## Check Feature Access

```typescript
// In a component
const userTier = 'free' // or get from useSubscription()

if (canAccessFeature(userTier, FEATURES.BACKTESTING)) {
  // User has access - show feature
  return <BacktestingPanel />
} else {
  // User doesn't have access - show upgrade prompt
  return <UpgradePrompt feature={FEATURES.BACKTESTING} currentTier={userTier} />
}
```

---

## Check Resource Limits

```typescript
const userTier = 'free'
const currentCount = 15
const limits = getTierLimits(userTier)

if (hasReachedLimit(userTier, 'maxTrades', currentCount)) {
  return (
    <LimitReachedPrompt
      resourceName="trades"
      currentCount={currentCount}
      limit={limits.maxTrades}
      currentTier={userTier}
    />
  )
}

// Or check specific limit
if (currentCount >= limits.maxTrades && limits.maxTrades !== -1) {
  // Show upgrade prompt
}
```

---

## Get User Subscription

```typescript
function MyComponent() {
  const { subscription, loading, error, refetch } = useSubscription()

  if (loading) return <div>Loading...</div>
  if (error) return <div>Error loading subscription</div>
  if (!subscription) return <div>No subscription found</div>

  return (
    <div>
      <p>Tier: {subscription.tier}</p>
      <p>Status: {subscription.status}</p>
      {subscription.status === 'past_due' && (
        <Alert>Your payment failed. Please update your payment method.</Alert>
      )}
    </div>
  )
}
```

---

## Show Pricing Cards

```typescript
// In any page/component
<SubscriptionPlans currentTier="free" showCurrentBadge={true} />

// Or with subscription hook
function PricingSection() {
  const { subscription } = useSubscription()

  return (
    <SubscriptionPlans
      currentTier={subscription?.tier || 'free'}
      showCurrentBadge={true}
    />
  )
}
```

---

## Add Billing Portal Button

```typescript
// Default usage
<BillingPortal />

// Custom styling
<BillingPortal variant="default" size="lg" className="mt-4">
  Manage My Subscription
</BillingPortal>

// Only show for paid users
{subscription?.tier !== 'free' && <BillingPortal />}
```

---

## Show Upgrade Prompts

### Inline Prompt
```typescript
<UpgradePrompt
  feature={FEATURES.API_ACCESS}
  currentTier="free"
  variant="inline"
/>
```

### Banner Prompt
```typescript
<UpgradePrompt
  feature={FEATURES.BACKTESTING}
  currentTier="starter"
  variant="banner"
  message="Unlock powerful backtesting with Pro plan"
/>
```

### Dialog Prompt
```typescript
<Dialog>
  <DialogContent>
    <UpgradePrompt
      feature={FEATURES.CUSTOM_STRATEGIES}
      currentTier="pro"
      variant="dialog"
    />
  </DialogContent>
</Dialog>
```

---

## Available Features

```typescript
FEATURES.BASIC_MARKET_OVERVIEW      // Free
FEATURES.LIMITED_REPORTS            // Free
FEATURES.DAILY_REPORTS              // Starter+
FEATURES.EMAIL_ALERTS               // Starter+
FEATURES.BASIC_CHARTS               // Starter+
FEATURES.BACKTESTING                // Pro+
FEATURES.API_ACCESS                 // Pro+
FEATURES.ADVANCED_CHARTS            // Pro+
FEATURES.REAL_TIME_ALERTS           // Pro+
FEATURES.CUSTOM_INDICATORS          // Pro+
FEATURES.EXPORT_DATA                // Pro+
FEATURES.CUSTOM_STRATEGIES          // Expert
FEATURES.PRIORITY_SUPPORT           // Expert
FEATURES.WHATSAPP_ALERTS            // Expert
FEATURES.ADVANCED_AI_ANALYSIS       // Expert
FEATURES.UNLIMITED_BACKTESTS        // Expert
FEATURES.WHITE_LABEL                // Expert
```

---

## Resource Limits

```typescript
// Get limits for a tier
const limits = getTierLimits('free')

limits.maxTrades        // 10 (free), 100 (starter), 1000 (pro), -1 (expert/unlimited)
limits.maxReports       // 5 (free), 50 (starter), 500 (pro), -1 (expert/unlimited)
limits.maxBacktests     // 0 (free), 0 (starter), 50 (pro), -1 (expert/unlimited)
limits.maxAlerts        // 0 (free), 10 (starter), 100 (pro), -1 (expert/unlimited)
limits.apiCallsPerDay   // 0 (free), 0 (starter), 1000 (pro), 10000 (expert)
```

---

## Environment Variables

```bash
# Required in .env.local
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
NEXT_PUBLIC_STRIPE_PRICE_STARTER=price_...
NEXT_PUBLIC_STRIPE_PRICE_PRO=price_...
NEXT_PUBLIC_STRIPE_PRICE_EXPERT=price_...
```

---

## Test Cards

```
Success: 4242 4242 4242 4242
Decline: 4000 0000 0000 9995
3D Secure: 4000 0027 6000 3184

Always use:
Expiry: 12/34
CVC: 123
ZIP: 12345
```

---

## Stripe CLI Commands

```bash
# Forward webhooks locally
stripe listen --forward-to localhost:3000/api/stripe/webhook

# Trigger test events
stripe trigger checkout.session.completed
stripe trigger customer.subscription.updated
stripe trigger customer.subscription.deleted
```

---

## Common Patterns

### Protected Feature Component
```typescript
function BacktestingFeature() {
  const { subscription } = useSubscription()

  if (!canAccessFeature(subscription?.tier || 'free', FEATURES.BACKTESTING)) {
    return <UpgradePrompt feature={FEATURES.BACKTESTING} variant="banner" />
  }

  return <BacktestingUI />
}
```

### Limit Check Before Action
```typescript
async function createTrade() {
  const { subscription } = useSubscription()
  const currentCount = await getTradeCount()
  const limits = getTierLimits(subscription?.tier || 'free')

  if (hasReachedLimit(subscription?.tier || 'free', 'maxTrades', currentCount)) {
    toast.error('Trade limit reached. Please upgrade.')
    return
  }

  // Create trade...
}
```

### Subscription Status Alert
```typescript
function SubscriptionAlert() {
  const { subscription } = useSubscription()

  if (subscription?.status === 'past_due') {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          Payment failed. <BillingPortal>Update payment method</BillingPortal>
        </AlertDescription>
      </Alert>
    )
  }

  if (subscription?.status === 'cancelled') {
    return (
      <Alert>
        <AlertDescription>
          Your subscription will end on {endDate}. <BillingPortal>Reactivate</BillingPortal>
        </AlertDescription>
      </Alert>
    )
  }

  return null
}
```

---

## API Endpoints

```typescript
// Create checkout session
POST /api/stripe/checkout
Body: { priceId: string }
Response: { sessionId: string, url: string }

// Create billing portal session
POST /api/stripe/portal
Response: { url: string }

// Webhook handler (Stripe only)
POST /api/stripe/webhook
Headers: { 'stripe-signature': string }
```

---

## Webhook Events

```typescript
// Handled events:
checkout.session.completed      → Create subscription
customer.subscription.updated   → Update subscription
customer.subscription.deleted   → Cancel subscription
invoice.payment_succeeded       → Set status to active
invoice.payment_failed          → Set status to past_due
```

---

## Troubleshooting Quick Fixes

### "No Stripe price ID configured"
→ Add price IDs to `.env.local` and restart dev server

### Webhook not received
→ Run `stripe listen --forward-to localhost:3000/api/stripe/webhook`

### Payment succeeds but tier not updated
→ Check webhook handler logs and database permissions

### "Invalid webhook signature"
→ Restart Stripe CLI listener and update `STRIPE_WEBHOOK_SECRET`

---

## Need More Details?

- Setup: [STRIPE_SETUP.md](./STRIPE_SETUP.md)
- Testing: [STRIPE_TESTING.md](./STRIPE_TESTING.md)
- Complete docs: [STRIPE_IMPLEMENTATION_SUMMARY.md](./STRIPE_IMPLEMENTATION_SUMMARY.md)
