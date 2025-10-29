import type { User } from '@supabase/supabase-js'

/**
 * Auth-related TypeScript types
 */

export type SubscriptionTier = 'free' | 'starter' | 'pro' | 'expert'

export interface UserProfile {
  id: string
  email: string
  full_name: string | null
  avatar_url: string | null
  subscription_tier: SubscriptionTier
  stripe_customer_id: string | null
  stripe_subscription_id: string | null
  created_at: string
  updated_at: string
}

export interface AuthContextType {
  user: User | null
  profile: UserProfile | null
  isLoading: boolean
  signOut: () => Promise<void>
}

export interface SignInCredentials {
  email: string
  password: string
}

export interface SignUpCredentials {
  email: string
  password: string
  full_name?: string
}

export interface AuthError {
  message: string
  status?: number
}
