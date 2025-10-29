'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { createBrowserClient } from '@/lib/supabase/client'

export default function Home() {
  const router = useRouter()

  useEffect(() => {
    async function checkAuth() {
      try {
        const supabase = createBrowserClient()
        const { data: { session }, error } = await supabase.auth.getSession()

        if (error) {
          console.error('Auth error:', error)
          // On error, redirect to login
          router.replace('/login')
          return
        }

        if (session) {
          // User is logged in, redirect to dashboard
          router.replace('/dashboard')
        } else {
          // User is not logged in, redirect to login
          router.replace('/login')
        }
      } catch (error) {
        console.error('Failed to check auth:', error)
        // On any error, default to login page
        router.replace('/login')
      }
    }

    checkAuth()
  }, [router])

  // Minimal loading state
  return null
}
