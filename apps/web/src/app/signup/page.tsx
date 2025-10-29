'use client'

import Link from 'next/link'
import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import GoogleSignInButton from '@/components/auth/GoogleSignInButton'
import AuthForm from '@/components/auth/AuthForm'
import { createBrowserClient } from '@/lib/supabase/client'

export default function SignUpPage() {
  const router = useRouter()

  useEffect(() => {
    async function checkAuth() {
      try {
        const supabase = createBrowserClient()
        const { data: { session } } = await supabase.auth.getSession()

        // Redirect if already logged in
        if (session) {
          router.replace('/dashboard')
        }
      } catch (error) {
        // Ignore errors, just stay on signup page
        console.error('Auth check error:', error)
      }
    }

    checkAuth()
  }, [router])

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900">
            Create your account
          </h1>
          <p className="mt-2 text-sm text-gray-600">
            Start trading smarter with AI-powered analysis
          </p>
        </div>

        <div className="mt-8 bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
          <div className="space-y-6">
            {/* Google OAuth */}
            <GoogleSignInButton />

            {/* Divider */}
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-gray-300" />
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2 bg-white text-gray-500">
                  Or sign up with email
                </span>
              </div>
            </div>

            {/* Email/Password Form */}
            <AuthForm mode="signup" />

            {/* Login Link */}
            <div className="text-center text-sm">
              <span className="text-gray-600">Already have an account? </span>
              <Link
                href="/login"
                className="font-medium text-blue-600 hover:text-blue-500"
              >
                Sign in
              </Link>
            </div>
          </div>
        </div>

        {/* Footer */}
        <p className="mt-4 text-center text-xs text-gray-500">
          By signing up, you agree to our{' '}
          <Link href="/terms" className="underline hover:text-gray-700">
            Terms of Service
          </Link>{' '}
          and{' '}
          <Link href="/privacy" className="underline hover:text-gray-700">
            Privacy Policy
          </Link>
        </p>
      </div>
    </div>
  )
}
