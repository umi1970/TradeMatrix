/**
 * Stripe Billing Portal API Route
 * Creates a billing portal session for managing subscriptions
 */

import { NextRequest, NextResponse } from 'next/server'
import { createServerClient } from '@/lib/supabase/server'
import { createBillingPortalSession, createCustomer } from '@/lib/stripe'

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

    // Get user profile
    const { data: profile, error: profileError } = await supabase
      .from('profiles')
      .select('email, full_name, stripe_customer_id')
      .eq('id', user.id)
      .single()

    if (profileError || !profile) {
      return NextResponse.json(
        { error: 'Profile not found' },
        { status: 404 }
      )
    }

    let customerId = profile.stripe_customer_id

    // Create customer if doesn't exist
    if (!customerId) {
      const customer = await createCustomer({
        email: profile.email,
        userId: user.id,
        name: profile.full_name,
      })

      customerId = customer.id

      // Update profile with customer ID
      await supabase
        .from('profiles')
        .update({ stripe_customer_id: customerId })
        .eq('id', user.id)
    }

    // Create billing portal session
    const baseUrl = request.headers.get('origin') || 'http://localhost:3000'
    const session = await createBillingPortalSession({
      customerId,
      returnUrl: `${baseUrl}/dashboard/profile`,
    })

    return NextResponse.json({ url: session.url })
  } catch (error) {
    console.error('Error creating billing portal session:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}
