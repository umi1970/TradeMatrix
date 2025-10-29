/**
 * Stripe Checkout API Route
 * Creates a checkout session for subscription
 */

import { NextRequest, NextResponse } from 'next/server'
import { createServerClient } from '@/lib/supabase/server'
import { createCheckoutSession } from '@/lib/stripe'

export async function POST(request: NextRequest) {
  try {
    // Get user from session
    const supabase = await createServerClient()
    const {
      data: { user },
      error: authError,
    } = await supabase.auth.getUser()

    if (authError || !user) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      )
    }

    // Parse request body
    const body = await request.json()
    const { priceId } = body

    if (!priceId) {
      return NextResponse.json(
        { error: 'Missing priceId' },
        { status: 400 }
      )
    }

    // Get user profile for email
    const { data: profile } = await supabase
      .from('profiles')
      .select('email, stripe_customer_id')
      .eq('id', user.id)
      .single()

    if (!profile) {
      return NextResponse.json(
        { error: 'Profile not found' },
        { status: 404 }
      )
    }

    // Create checkout session
    const baseUrl = request.headers.get('origin') || 'http://localhost:3000'
    const session = await createCheckoutSession({
      userId: user.id,
      email: profile.email,
      priceId,
      successUrl: `${baseUrl}/dashboard/profile?success=true`,
      cancelUrl: `${baseUrl}/dashboard/profile?canceled=true`,
    })

    return NextResponse.json({ sessionId: session.id, url: session.url })
  } catch (error) {
    console.error('Error creating checkout session:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}
