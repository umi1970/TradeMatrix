import { createServerClient } from '@/lib/supabase/server'
import { createBrowserClient } from '@/lib/supabase/client'
import type { User } from '@supabase/supabase-js'

/**
 * Get current user from server-side
 * Use this in Server Components, Server Actions, and Route Handlers
 */
export async function getCurrentUser(): Promise<User | null> {
  const supabase = await createServerClient()
  const {
    data: { user },
  } = await supabase.auth.getUser()
  return user
}

/**
 * Get user profile from database
 * Use this to get additional user information beyond auth data
 */
export async function getUserProfile(userId: string) {
  const supabase = await createServerClient()
  const { data, error } = await supabase
    .from('profiles')
    .select('*')
    .eq('id', userId)
    .single()

  if (error) {
    console.error('Error fetching user profile:', error)
    return null
  }

  return data
}

/**
 * Check if user has a specific subscription tier or higher
 */
export async function hasSubscriptionTier(
  userId: string,
  requiredTier: 'free' | 'starter' | 'pro' | 'expert'
): Promise<boolean> {
  const profile = await getUserProfile(userId)
  if (!profile) return false

  const tierHierarchy: Record<'free' | 'starter' | 'pro' | 'expert', number> = {
    free: 0,
    starter: 1,
    pro: 2,
    expert: 3,
  }

  const userTierLevel = tierHierarchy[profile.subscription_tier as 'free' | 'starter' | 'pro' | 'expert']
  const requiredTierLevel = tierHierarchy[requiredTier]

  return userTierLevel >= requiredTierLevel
}

/**
 * Sign in with email and password (client-side)
 */
export async function signInWithEmail(email: string, password: string) {
  const supabase = createBrowserClient()
  return await supabase.auth.signInWithPassword({
    email,
    password,
  })
}

/**
 * Sign up with email and password (client-side)
 */
export async function signUpWithEmail(email: string, password: string) {
  const supabase = createBrowserClient()
  return await supabase.auth.signUp({
    email,
    password,
    options: {
      emailRedirectTo: `${window.location.origin}/auth/callback`,
    },
  })
}

/**
 * Sign in with Google OAuth (client-side)
 */
export async function signInWithGoogle() {
  const supabase = createBrowserClient()
  return await supabase.auth.signInWithOAuth({
    provider: 'google',
    options: {
      redirectTo: `${window.location.origin}/auth/callback`,
      queryParams: {
        access_type: 'offline',
        prompt: 'consent',
      },
    },
  })
}

/**
 * Sign in with GitHub OAuth (client-side)
 */
export async function signInWithGitHub() {
  const supabase = createBrowserClient()
  return await supabase.auth.signInWithOAuth({
    provider: 'github',
    options: {
      redirectTo: `${window.location.origin}/auth/callback`,
    },
  })
}

/**
 * Sign out (client-side)
 */
export async function signOut() {
  const supabase = createBrowserClient()
  return await supabase.auth.signOut()
}

/**
 * Reset password (client-side)
 */
export async function resetPassword(email: string) {
  const supabase = createBrowserClient()
  return await supabase.auth.resetPasswordForEmail(email, {
    redirectTo: `${window.location.origin}/auth/reset-password`,
  })
}

/**
 * Update password (client-side)
 */
export async function updatePassword(newPassword: string) {
  const supabase = createBrowserClient()
  return await supabase.auth.updateUser({
    password: newPassword,
  })
}
