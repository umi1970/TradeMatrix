import { createServerClient } from '@/lib/supabase/server'
import { redirect } from 'next/navigation'
import { Sidebar } from '@/components/dashboard/sidebar'
import { Header } from '@/components/dashboard/header'

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const supabase = await createServerClient()

  // Get the current user
  const {
    data: { user },
  } = await supabase.auth.getUser()

  // Redirect to login if not authenticated
  if (!user) {
    redirect('/login')
  }

  // Get user profile
  let profile: {
    full_name?: string | null
    subscription_tier?: string | null
    avatar_url?: string | null
  } | null = null
  try {
    const { data } = await supabase
      .from('profiles')
      .select('full_name, subscription_tier, avatar_url')
      .eq('id', user.id)
      .single()
    profile = data
  } catch (error) {
    console.log('Profile not found or table does not exist')
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
