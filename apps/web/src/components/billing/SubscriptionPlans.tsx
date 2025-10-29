/**
 * SubscriptionPlans Component
 * Displays pricing cards for all subscription tiers with purchase buttons
 */

'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Check, Loader2, Zap } from 'lucide-react'
import { TIER_PRICING, type SubscriptionTier } from '@/lib/subscription'
import { useSubscription } from '@/hooks/use-subscription'

interface SubscriptionPlansProps {
  currentTier?: SubscriptionTier
  showCurrentBadge?: boolean
}

export function SubscriptionPlans({
  currentTier = 'free',
  showCurrentBadge = true,
}: SubscriptionPlansProps) {
  const router = useRouter()
  const { subscription } = useSubscription()
  const [loadingTier, setLoadingTier] = useState<SubscriptionTier | null>(null)

  const handleSubscribe = async (tier: SubscriptionTier) => {
    if (tier === 'free') return

    const pricing = TIER_PRICING[tier]
    if (!pricing.stripePriceId) {
      console.error('No Stripe price ID configured for tier:', tier)
      alert('This plan is not yet configured. Please contact support.')
      return
    }

    setLoadingTier(tier)

    try {
      // Create checkout session
      const response = await fetch('/api/stripe/checkout', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          priceId: pricing.stripePriceId,
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to create checkout session')
      }

      const { url } = await response.json()

      // Redirect to Stripe Checkout
      if (url) {
        window.location.href = url
      }
    } catch (error) {
      console.error('Error creating checkout session:', error)
      alert('Failed to start checkout. Please try again.')
    } finally {
      setLoadingTier(null)
    }
  }

  const tiers: SubscriptionTier[] = ['free', 'starter', 'pro', 'expert']

  const isCurrentTier = (tier: SubscriptionTier) => {
    return subscription ? subscription.tier === tier : currentTier === tier
  }

  const canUpgradeToTier = (tier: SubscriptionTier) => {
    const tierOrder: SubscriptionTier[] = ['free', 'starter', 'pro', 'expert']
    const current = subscription?.tier || currentTier
    const currentIndex = tierOrder.indexOf(current)
    const targetIndex = tierOrder.indexOf(tier)
    return targetIndex > currentIndex
  }

  return (
    <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
      {tiers.map((tier) => {
        const pricing = TIER_PRICING[tier]
        const isCurrent = isCurrentTier(tier)
        const canUpgrade = canUpgradeToTier(tier)
        const isLoading = loadingTier === tier

        return (
          <Card
            key={tier}
            className={`relative flex flex-col h-full ${
              tier === 'pro'
                ? 'border-purple-500 border-2 shadow-lg'
                : isCurrent
                ? 'border-blue-500 border-2'
                : ''
            }`}
          >
            {tier === 'pro' && (
              <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                <Badge className="bg-purple-600 text-white px-4 py-1">
                  <Zap className="h-3 w-3 mr-1 inline" />
                  Most Popular
                </Badge>
              </div>
            )}

            <CardHeader className="text-center pb-4">
              <div className="flex justify-center items-center gap-2 mb-2">
                <CardTitle className="text-2xl capitalize">{pricing.name}</CardTitle>
                {isCurrent && showCurrentBadge && (
                  <Badge variant="outline" className="ml-2">
                    Current
                  </Badge>
                )}
              </div>

              <div className="mt-4">
                <div className="flex items-baseline justify-center gap-2">
                  <span className="text-4xl font-bold">€{pricing.price}</span>
                  <span className="text-muted-foreground">/{pricing.interval}</span>
                </div>
              </div>

              <p className="text-sm text-muted-foreground mt-2">{pricing.description}</p>
            </CardHeader>

            <CardContent className="flex flex-col flex-grow space-y-4">
              {/* Features list */}
              <ul className="space-y-2 flex-grow">
                {pricing.features.map((feature, index) => (
                  <li key={index} className="flex items-start gap-2 text-sm">
                    <Check className="h-4 w-4 text-green-600 shrink-0 mt-0.5" />
                    <span>{feature}</span>
                  </li>
                ))}
              </ul>

              {/* CTA Button */}
              <div className="pt-4">
                {tier === 'free' ? (
                  <Button variant="outline" className="w-full" disabled>
                    Free Forever
                  </Button>
                ) : isCurrent ? (
                  <Button
                    variant="outline"
                    className="w-full"
                    onClick={() => router.push('/dashboard/profile')}
                  >
                    Manage Subscription
                  </Button>
                ) : canUpgrade ? (
                  <Button
                    className={`w-full ${
                      tier === 'pro'
                        ? 'bg-purple-600 hover:bg-purple-700'
                        : 'bg-blue-600 hover:bg-blue-700'
                    }`}
                    onClick={() => handleSubscribe(tier)}
                    disabled={isLoading}
                  >
                    {isLoading ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Processing...
                      </>
                    ) : (
                      'Upgrade Now'
                    )}
                  </Button>
                ) : (
                  <Button variant="outline" className="w-full" disabled>
                    Downgrade not available
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>
        )
      })}
    </div>
  )
}
