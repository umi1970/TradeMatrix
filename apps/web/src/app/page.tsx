'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { createBrowserClient } from '@/lib/supabase/client'

export default function Home() {
  const router = useRouter()

  useEffect(() => {
    async function checkAuth() {
      const supabase = createBrowserClient()
      const { data: { session } } = await supabase.auth.getSession()

      if (session) {
        // User is logged in, redirect to dashboard
        router.replace('/dashboard')
      } else {
        // User is not logged in, redirect to login
        router.replace('/login')
      }
    }

    checkAuth()
  }, [router])

  // Show loading state while checking auth
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <div className="text-center">
        <h1 className="text-4xl font-bold mb-4">
          TradeMatrix.ai
        </h1>
        <p className="text-xl text-gray-600">
          Loading...
        </p>
      </div>
    </main>
  )
}
