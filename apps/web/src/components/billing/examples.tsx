/**
 * Example Usage of Stripe Integration Components
 * Copy these patterns into your own components
 */

import { useState } from 'react'
import { useSubscription } from '@/hooks/use-subscription'
import { canAccessFeature, FEATURES, getTierLimits, hasReachedLimit } from '@/lib/subscription'
import { SubscriptionPlans } from './SubscriptionPlans'
import { BillingPortal } from './BillingPortal'
import { UpgradePrompt, LimitReachedPrompt } from './UpgradePrompt'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { AlertCircle, Lock, TrendingUp } from 'lucide-react'

// ========================================
// Example 1: Protected Feature Component
// ========================================

export function BacktestingFeature() {
  const { subscription, loading } = useSubscription()

  if (loading) {
    return <div>Loading...</div>
  }

  const userTier = subscription?.tier || 'free'

  // Check if user has access to backtesting
  if (!canAccessFeature(userTier, FEATURES.BACKTESTING)) {
    return (
      <div className="space-y-4">
        <div className="text-center py-12">
          <Lock className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <h3 className="text-lg font-semibold mb-2">Backtesting is a Pro Feature</h3>
          <p className="text-muted-foreground mb-6">
            Upgrade to Pro to test your strategies against historical data
          </p>
        </div>

        <UpgradePrompt
          feature={FEATURES.BACKTESTING}
          currentTier={userTier}
          variant="banner"
        />
      </div>
    )
  }

  // User has access - show the feature
  return (
    <div>
      <h2>Backtesting Dashboard</h2>
      {/* Your backtesting UI here */}
    </div>
  )
}

// ========================================
// Example 2: Trade Creation with Limit Check
// ========================================

export function TradeCreationButton() {
  const { subscription } = useSubscription()
  const [tradeCount, setTradeCount] = useState(8) // Would come from database

  const userTier = subscription?.tier || 'free'
  const limits = getTierLimits(userTier)
  const isLimitReached = hasReachedLimit(userTier, 'maxTrades', tradeCount)

  const handleCreateTrade = () => {
    if (isLimitReached) {
      alert('Trade limit reached. Please upgrade.')
      return
    }

    // Create trade logic...
    setTradeCount(tradeCount + 1)
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="font-semibold">Create New Trade</h3>
          <p className="text-sm text-muted-foreground">
            {limits.maxTrades === -1
              ? 'Unlimited trades'
              : `${tradeCount} / ${limits.maxTrades} trades used`}
          </p>
        </div>
        <Button onClick={handleCreateTrade} disabled={isLimitReached}>
          Create Trade
        </Button>
      </div>

      {isLimitReached && (
        <LimitReachedPrompt
          resourceName="trades"
          currentCount={tradeCount}
          limit={limits.maxTrades}
          currentTier={userTier}
        />
      )}
    </div>
  )
}

// ========================================
// Example 3: Subscription Status Banner
// ========================================

export function SubscriptionStatusBanner() {
  const { subscription, loading } = useSubscription()

  if (loading || !subscription) return null

  // Show warning if payment failed
  if (subscription.status === 'past_due') {
    return (
      <Alert variant="destructive" className="mb-4">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription className="flex items-center justify-between">
          <span>Your payment failed. Please update your payment method to continue using premium features.</span>
          <BillingPortal variant="default" size="sm">
            Update Payment
          </BillingPortal>
        </AlertDescription>
      </Alert>
    )
  }

  // Show info if subscription is cancelled but still active
  if (subscription.status === 'cancelled') {
    return (
      <Alert className="mb-4">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription className="flex items-center justify-between">
          <span>Your subscription will end at the end of the billing period. Reactivate to keep your features.</span>
          <BillingPortal variant="default" size="sm">
            Reactivate
          </BillingPortal>
        </AlertDescription>
      </Alert>
    )
  }

  return null
}

// ========================================
// Example 4: Feature Badge with Upgrade
// ========================================

export function FeatureBadge({ feature }: { feature: string }) {
  const { subscription } = useSubscription()
  const userTier = subscription?.tier || 'free'

  // Determine if feature is available
  const hasFeature = canAccessFeature(userTier, feature as any)

  if (hasFeature) {
    return (
      <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
        Unlocked
      </Badge>
    )
  }

  return (
    <Badge variant="outline" className="bg-gray-50 text-gray-700 border-gray-200">
      <Lock className="h-3 w-3 mr-1" />
      Locked
    </Badge>
  )
}

// ========================================
// Example 5: Pricing Comparison Page
// ========================================

export function PricingPage() {
  const { subscription } = useSubscription()

  return (
    <div className="container mx-auto py-12 space-y-8">
      {/* Header */}
      <div className="text-center space-y-4">
        <h1 className="text-4xl font-bold">Choose Your Plan</h1>
        <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
          Unlock powerful AI-driven trading analysis and automation
        </p>
      </div>

      {/* Current subscription info */}
      {subscription && subscription.tier !== 'free' && (
        <div className="max-w-2xl mx-auto">
          <Card>
            <CardContent className="flex items-center justify-between p-6">
              <div>
                <p className="text-sm text-muted-foreground">Current Plan</p>
                <p className="text-lg font-semibold capitalize">{subscription.tier}</p>
              </div>
              <BillingPortal />
            </CardContent>
          </Card>
        </div>
      )}

      {/* Pricing cards */}
      <SubscriptionPlans
        currentTier={subscription?.tier || 'free'}
        showCurrentBadge={true}
      />

      {/* FAQ or additional info */}
      <div className="max-w-3xl mx-auto pt-12">
        <h2 className="text-2xl font-bold mb-6 text-center">Frequently Asked Questions</h2>
        {/* FAQ content... */}
      </div>
    </div>
  )
}

// ========================================
// Example 6: API Access Dashboard
// ========================================

export function APIAccessDashboard() {
  const { subscription } = useSubscription()
  const userTier = subscription?.tier || 'free'
  const limits = getTierLimits(userTier)
  const hasAPIAccess = canAccessFeature(userTier, FEATURES.API_ACCESS)

  const [apiCallsToday] = useState(450) // Would come from database

  if (!hasAPIAccess) {
    return (
      <div className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Lock className="h-5 w-5" />
              API Access
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-muted-foreground mb-4">
              API access is available on Pro and Expert plans
            </p>
            <UpgradePrompt
              feature={FEATURES.API_ACCESS}
              currentTier={userTier}
              variant="inline"
            />
          </CardContent>
        </Card>
      </div>
    )
  }

  const isNearLimit = limits.apiCallsPerDay > 0 && apiCallsToday >= limits.apiCallsPerDay * 0.8

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>API Usage</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium">Daily API Calls</span>
              <span className="text-sm text-muted-foreground">
                {apiCallsToday.toLocaleString()} / {limits.apiCallsPerDay.toLocaleString()}
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className={`h-2 rounded-full ${isNearLimit ? 'bg-amber-500' : 'bg-blue-600'}`}
                style={{ width: `${(apiCallsToday / limits.apiCallsPerDay) * 100}%` }}
              />
            </div>
          </div>

          {isNearLimit && userTier !== 'expert' && (
            <Alert className="bg-amber-50 border-amber-200">
              <TrendingUp className="h-4 w-4 text-amber-600" />
              <AlertDescription>
                You're approaching your daily limit. Upgrade to Expert for 10x more API calls.
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

// ========================================
// Example 7: Feature List with Access Indicators
// ========================================

export function FeatureList() {
  const { subscription } = useSubscription()
  const userTier = subscription?.tier || 'free'

  const features = [
    { name: 'Daily AI Reports', feature: FEATURES.DAILY_REPORTS },
    { name: 'Email Alerts', feature: FEATURES.EMAIL_ALERTS },
    { name: 'Backtesting', feature: FEATURES.BACKTESTING },
    { name: 'API Access', feature: FEATURES.API_ACCESS },
    { name: 'Custom Strategies', feature: FEATURES.CUSTOM_STRATEGIES },
    { name: 'WhatsApp Alerts', feature: FEATURES.WHATSAPP_ALERTS },
  ]

  return (
    <Card>
      <CardHeader>
        <CardTitle>Your Features</CardTitle>
      </CardHeader>
      <CardContent>
        <ul className="space-y-3">
          {features.map(({ name, feature }) => {
            const hasAccess = canAccessFeature(userTier, feature)
            return (
              <li key={feature} className="flex items-center justify-between py-2 border-b last:border-0">
                <span className={hasAccess ? '' : 'text-muted-foreground'}>{name}</span>
                <FeatureBadge feature={feature} />
              </li>
            )
          })}
        </ul>

        {userTier === 'free' && (
          <div className="mt-6">
            <UpgradePrompt
              feature={FEATURES.DAILY_REPORTS}
              currentTier={userTier}
              variant="inline"
            />
          </div>
        )}
      </CardContent>
    </Card>
  )
}

// ========================================
// Example 8: Upgrade Modal/Dialog
// ========================================

export function UpgradeDialog({ isOpen, onClose, feature }: any) {
  const { subscription } = useSubscription()

  return (
    <div className={`${isOpen ? 'block' : 'hidden'}`}>
      {/* Dialog wrapper */}
      <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center">
        <div className="bg-white rounded-lg p-8 max-w-md w-full">
          <UpgradePrompt
            feature={feature}
            currentTier={subscription?.tier || 'free'}
            variant="dialog"
          />
          <Button variant="outline" onClick={onClose} className="w-full mt-4">
            Maybe Later
          </Button>
        </div>
      </div>
    </div>
  )
}
