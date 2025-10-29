/**
 * UpgradePrompt Component
 * Shows when user hits feature limits, prompting upgrade
 */

'use client'

import { useRouter } from 'next/navigation'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { ArrowUpCircle, Lock, Sparkles } from 'lucide-react'
import { FEATURES, getTierPricing, getMinimumTierForFeature, type Feature } from '@/lib/subscription'

interface UpgradePromptProps {
  feature: Feature
  currentTier?: 'free' | 'starter' | 'pro' | 'expert'
  message?: string
  variant?: 'inline' | 'banner' | 'dialog'
  className?: string
}

export function UpgradePrompt({
  feature,
  currentTier = 'free',
  message,
  variant = 'inline',
  className,
}: UpgradePromptProps) {
  const router = useRouter()

  const requiredTier = getMinimumTierForFeature(feature)
  const tierPricing = getTierPricing(requiredTier)

  const handleUpgrade = () => {
    // Navigate to pricing page or profile with pricing section
    router.push('/dashboard/profile#billing')
  }

  const defaultMessage = `Upgrade to ${tierPricing.name} to unlock this feature`

  if (variant === 'banner') {
    return (
      <div className={`bg-gradient-to-r from-purple-50 to-blue-50 dark:from-purple-950/20 dark:to-blue-950/20 border border-purple-200 dark:border-purple-800 rounded-lg p-6 ${className}`}>
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-start gap-3">
            <div className="rounded-full bg-purple-100 dark:bg-purple-900 p-2">
              <Sparkles className="h-5 w-5 text-purple-600 dark:text-purple-400" />
            </div>
            <div>
              <h3 className="font-semibold text-lg mb-1">Unlock Premium Features</h3>
              <p className="text-sm text-muted-foreground mb-3">
                {message || defaultMessage}
              </p>
              <div className="flex items-center gap-2 text-sm">
                <span className="font-medium">Starting at €{tierPricing.price}/month</span>
              </div>
            </div>
          </div>
          <Button onClick={handleUpgrade} className="shrink-0">
            <ArrowUpCircle className="h-4 w-4 mr-2" />
            Upgrade Now
          </Button>
        </div>
      </div>
    )
  }

  if (variant === 'dialog') {
    return (
      <div className={`text-center space-y-4 p-6 ${className}`}>
        <div className="flex justify-center">
          <div className="rounded-full bg-gradient-to-br from-purple-500 to-blue-600 p-4">
            <Lock className="h-8 w-8 text-white" />
          </div>
        </div>
        <div className="space-y-2">
          <h3 className="text-xl font-bold">Feature Locked</h3>
          <p className="text-muted-foreground">
            {message || defaultMessage}
          </p>
        </div>
        <div className="bg-muted rounded-lg p-4 space-y-2">
          <div className="flex justify-between items-center">
            <span className="font-medium">{tierPricing.name} Plan</span>
            <span className="text-2xl font-bold">€{tierPricing.price}</span>
          </div>
          <p className="text-xs text-muted-foreground">per month</p>
        </div>
        <Button onClick={handleUpgrade} className="w-full" size="lg">
          <ArrowUpCircle className="h-4 w-4 mr-2" />
          Upgrade to {tierPricing.name}
        </Button>
      </div>
    )
  }

  // Inline variant (default)
  return (
    <Alert className={`bg-blue-50 dark:bg-blue-950/20 border-blue-200 dark:border-blue-800 ${className}`}>
      <Lock className="h-4 w-4 text-blue-600 dark:text-blue-400" />
      <AlertDescription className="flex items-center justify-between gap-4">
        <span className="text-sm">
          {message || defaultMessage}
        </span>
        <Button onClick={handleUpgrade} size="sm" variant="default">
          Upgrade
        </Button>
      </AlertDescription>
    </Alert>
  )
}

/**
 * Limit Reached Prompt
 * Shows when user has reached a resource limit
 */
interface LimitReachedPromptProps {
  resourceName: string
  currentCount: number
  limit: number
  currentTier: 'free' | 'starter' | 'pro' | 'expert'
  className?: string
}

export function LimitReachedPrompt({
  resourceName,
  currentCount,
  limit,
  currentTier,
  className,
}: LimitReachedPromptProps) {
  const router = useRouter()

  const tierOrder: ('free' | 'starter' | 'pro' | 'expert')[] = ['free', 'starter', 'pro', 'expert']
  const currentIndex = tierOrder.indexOf(currentTier)
  const nextTier = tierOrder[currentIndex + 1]

  if (!nextTier) {
    return null // Already at highest tier
  }

  const nextTierPricing = getTierPricing(nextTier)

  const handleUpgrade = () => {
    router.push('/dashboard/profile#billing')
  }

  return (
    <Alert className={`bg-amber-50 dark:bg-amber-950/20 border-amber-200 dark:border-amber-800 ${className}`}>
      <AlertCircle className="h-4 w-4 text-amber-600 dark:text-amber-400" />
      <AlertDescription>
        <div className="space-y-2">
          <p className="text-sm font-medium">
            You've reached your limit
          </p>
          <p className="text-xs text-muted-foreground">
            {currentCount} / {limit} {resourceName} used
          </p>
          <Button onClick={handleUpgrade} size="sm" variant="default" className="mt-2">
            <ArrowUpCircle className="h-3 w-3 mr-1" />
            Upgrade to {nextTierPricing.name}
          </Button>
        </div>
      </AlertDescription>
    </Alert>
  )
}

// Fix missing import
import { AlertCircle } from 'lucide-react'
