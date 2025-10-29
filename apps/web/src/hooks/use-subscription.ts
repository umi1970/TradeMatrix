/**
 * useSubscription hook
 * Fetches and manages subscription status for the current user
 */

import { useEffect, useState } from 'react'
import { createBrowserClient } from '@/lib/supabase/client'
import type { SubscriptionTier } from '@/lib/subscription'

interface SubscriptionData {
  tier: SubscriptionTier
  status: 'active' | 'cancelled' | 'past_due' | 'trialing'
  stripeCustomerId: string | null
  stripeSubscriptionId: string | null
  stripePriceId: string | null
}

interface UseSubscriptionReturn {
  subscription: SubscriptionData | null
  loading: boolean
  error: Error | null
  refetch: () => Promise<void>
}

/**
 * Hook to get current user's subscription status
 */
export function useSubscription(): UseSubscriptionReturn {
  const [subscription, setSubscription] = useState<SubscriptionData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  const supabase = createBrowserClient()

  const fetchSubscription = async () => {
    try {
      setLoading(true)
      setError(null)

      // Get current user
      const {
        data: { user },
        error: authError,
      } = await supabase.auth.getUser()

      if (authError) throw authError

      if (!user) {
        throw new Error('No authenticated user')
      }

      // Fetch profile with subscription info
      const { data: profile, error: profileError } = await supabase
        .from('profiles')
        .select(
          'subscription_tier, subscription_status, stripe_customer_id, stripe_subscription_id, stripe_price_id'
        )
        .eq('id', user.id)
        .single()

      if (profileError) throw profileError

      if (!profile) {
        throw new Error('Profile not found')
      }

      setSubscription({
        tier: profile.subscription_tier as SubscriptionTier,
        status: profile.subscription_status as 'active' | 'cancelled' | 'past_due' | 'trialing',
        stripeCustomerId: profile.stripe_customer_id,
        stripeSubscriptionId: profile.stripe_subscription_id,
        stripePriceId: profile.stripe_price_id,
      })
    } catch (err) {
      console.error('Error fetching subscription:', err)
      setError(err instanceof Error ? err : new Error('Unknown error'))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchSubscription()
  }, [])

  return {
    subscription,
    loading,
    error,
    refetch: fetchSubscription,
  }
}
