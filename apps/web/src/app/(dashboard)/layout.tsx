'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { createBrowserClient } from '@/lib/supabase/client'
import { Sidebar } from '@/components/dashboard/sidebar'
import { Header } from '@/components/dashboard/header'
import type { User } from '@supabase/supabase-js'

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const router = useRouter()
  const [user, setUser] = useState<User | null>(null)
  const [profile, setProfile] = useState<{
    full_name?: string | null
    subscription_tier?: string | null
    avatar_url?: string | null
  } | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function loadUser() {
      try {
        const supabase = createBrowserClient()

        // Get the current user
        const { data: { user: currentUser }, error } = await supabase.auth.getUser()

        if (error || !currentUser) {
          // Redirect to login if not authenticated
          router.replace('/login')
          return
        }

        setUser(currentUser)

        // Get user profile
        try {
          const { data } = await supabase
            .from('profiles')
            .select('full_name, subscription_tier, avatar_url')
            .eq('id', currentUser.id)
            .single()

          setProfile(data)
        } catch (error) {
          console.log('Profile not found or table does not exist')
        }
      } catch (error) {
        console.error('Failed to load user:', error)
        router.replace('/login')
      } finally {
        setLoading(false)
      }
    }

    loadUser()
  }, [router])

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <p className="text-gray-600">Loading...</p>
      </div>
    )
  }

  if (!user) {
    return null
  }

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <Sidebar />

      {/* Main Content Area */}
      <div className="flex flex-col flex-1 overflow-hidden">
        {/* Header */}
        <Header
          user={user}
          profile={
            profile
              ? {
                  full_name: profile.full_name || undefined,
                  subscription_tier: profile.subscription_tier || undefined,
                  avatar_url: profile.avatar_url || undefined,
                }
              : null
          }
        />

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto bg-muted/40 p-4 md:p-6 lg:p-8">
          {children}
        </main>
      </div>
    </div>
  )
}
