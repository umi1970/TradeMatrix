/**
 * Stripe Webhook Handler
 * Handles Stripe webhook events for subscription updates
 */

import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'
import { verifyWebhookSignature, mapPriceIdToTier } from '@/lib/stripe'
import Stripe from 'stripe'

// Supabase admin client (uses service role key for bypassing RLS)
const supabaseAdmin = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!,
  {
    auth: {
      autoRefreshToken: false,
      persistSession: false,
    },
  }
)

export async function POST(request: NextRequest) {
  const body = await request.text()
  const signature = request.headers.get('stripe-signature')

  if (!signature) {
    return NextResponse.json(
      { error: 'Missing stripe-signature header' },
      { status: 400 }
    )
  }

  let event: Stripe.Event

  try {
    // Verify webhook signature
    event = verifyWebhookSignature(body, signature)
  } catch (error) {
    console.error('Webhook signature verification failed:', error)
    return NextResponse.json(
      { error: 'Invalid signature' },
      { status: 400 }
    )
  }

  console.log(`Received webhook event: ${event.type}`)

  try {
    switch (event.type) {
      case 'checkout.session.completed': {
        const session = event.data.object as Stripe.Checkout.Session

        console.log('Checkout session completed:', session.id)

        // Get subscription details
        if (session.mode === 'subscription' && session.subscription) {
          const subscriptionId =
            typeof session.subscription === 'string'
              ? session.subscription
              : session.subscription.id

          const customerId =
            typeof session.customer === 'string'
              ? session.customer
              : session.customer?.id

          const userId = session.metadata?.userId || session.client_reference_id

          if (!userId) {
            console.error('No userId found in session metadata')
            break
          }

          // Get subscription to get price ID
          const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, {
            apiVersion: '2025-09-30.clover',
          })
          const subscription = await stripe.subscriptions.retrieve(subscriptionId)
          const priceId = subscription.items.data[0]?.price.id
          const tier = priceId ? mapPriceIdToTier(priceId) : null

          if (!tier) {
            console.error('Could not map price ID to tier:', priceId)
            break
          }

          // Update user profile with Stripe customer and subscription info
          const { error: profileError } = await supabaseAdmin
            .from('profiles')
            .update({
              stripe_customer_id: customerId,
              stripe_subscription_id: subscriptionId,
              stripe_price_id: priceId,
              subscription_tier: tier,
              subscription_status: 'active',
              updated_at: new Date().toISOString(),
            })
            .eq('id', userId)

          if (profileError) {
            console.error('Error updating profile:', profileError)
            break
          }

          // Create subscription record
          const { error: subscriptionError } = await supabaseAdmin
            .from('subscriptions')
            .insert({
              user_id: userId,
              stripe_subscription_id: subscriptionId,
              stripe_customer_id: customerId || '',
              stripe_price_id: priceId || '',
              tier,
              status: subscription.status,
              current_period_start: new Date(subscription.current_period_start * 1000).toISOString(),
              current_period_end: new Date(subscription.current_period_end * 1000).toISOString(),
              cancel_at_period_end: subscription.cancel_at_period_end,
            })

          if (subscriptionError) {
            console.error('Error creating subscription record:', subscriptionError)
          }

          console.log(`Subscription created for user ${userId}`)
        }
        break
      }

      case 'customer.subscription.updated': {
        const subscription = event.data.object as Stripe.Subscription

        console.log('Subscription updated:', subscription.id)

        const priceId = subscription.items.data[0]?.price.id
        const tier = priceId ? mapPriceIdToTier(priceId) : null

        // Find user by subscription ID
        const { data: profile } = await supabaseAdmin
          .from('profiles')
          .select('id')
          .eq('stripe_subscription_id', subscription.id)
          .single()

        if (!profile) {
          console.error('Profile not found for subscription:', subscription.id)
          break
        }

        // Update profile
        const { error: profileError } = await supabaseAdmin
          .from('profiles')
          .update({
            stripe_price_id: priceId,
            subscription_tier: tier || 'free',
            subscription_status: subscription.status,
            updated_at: new Date().toISOString(),
          })
          .eq('id', profile.id)

        if (profileError) {
          console.error('Error updating profile:', profileError)
          break
        }

        // Update subscription record
        const { error: subscriptionError } = await supabaseAdmin
          .from('subscriptions')
          .update({
            stripe_price_id: priceId || '',
            tier: tier || 'starter',
            status: subscription.status,
            current_period_start: new Date(subscription.current_period_start * 1000).toISOString(),
            current_period_end: new Date(subscription.current_period_end * 1000).toISOString(),
            cancel_at_period_end: subscription.cancel_at_period_end,
            cancelled_at: subscription.canceled_at
              ? new Date(subscription.canceled_at * 1000).toISOString()
              : null,
            updated_at: new Date().toISOString(),
          })
          .eq('stripe_subscription_id', subscription.id)

        if (subscriptionError) {
          console.error('Error updating subscription record:', subscriptionError)
        }

        console.log(`Subscription updated for user ${profile.id}`)
        break
      }

      case 'customer.subscription.deleted': {
        const subscription = event.data.object as Stripe.Subscription

        console.log('Subscription deleted:', subscription.id)

        // Find user by subscription ID
        const { data: profile } = await supabaseAdmin
          .from('profiles')
          .select('id')
          .eq('stripe_subscription_id', subscription.id)
          .single()

        if (!profile) {
          console.error('Profile not found for subscription:', subscription.id)
          break
        }

        // Downgrade user to free tier
        const { error: profileError } = await supabaseAdmin
          .from('profiles')
          .update({
            subscription_tier: 'free',
            subscription_status: 'cancelled',
            stripe_subscription_id: null,
            stripe_price_id: null,
            updated_at: new Date().toISOString(),
          })
          .eq('id', profile.id)

        if (profileError) {
          console.error('Error downgrading profile:', profileError)
          break
        }

        // Update subscription record
        const { error: subscriptionError } = await supabaseAdmin
          .from('subscriptions')
          .update({
            status: 'canceled',
            cancelled_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          })
          .eq('stripe_subscription_id', subscription.id)

        if (subscriptionError) {
          console.error('Error updating subscription record:', subscriptionError)
        }

        console.log(`Subscription cancelled for user ${profile.id}`)
        break
      }

      case 'invoice.payment_succeeded': {
        const invoice = event.data.object as Stripe.Invoice

        console.log('Invoice payment succeeded:', invoice.id)

        // Update subscription status to active
        if (invoice.subscription) {
          const subscriptionId =
            typeof invoice.subscription === 'string'
              ? invoice.subscription
              : invoice.subscription.id

          const { error } = await supabaseAdmin
            .from('profiles')
            .update({
              subscription_status: 'active',
              updated_at: new Date().toISOString(),
            })
            .eq('stripe_subscription_id', subscriptionId)

          if (error) {
            console.error('Error updating subscription status:', error)
          }
        }
        break
      }

      case 'invoice.payment_failed': {
        const invoice = event.data.object as Stripe.Invoice

        console.log('Invoice payment failed:', invoice.id)

        // Update subscription status to past_due
        if (invoice.subscription) {
          const subscriptionId =
            typeof invoice.subscription === 'string'
              ? invoice.subscription
              : invoice.subscription.id

          const { error } = await supabaseAdmin
            .from('profiles')
            .update({
              subscription_status: 'past_due',
              updated_at: new Date().toISOString(),
            })
            .eq('stripe_subscription_id', subscriptionId)

          if (error) {
            console.error('Error updating subscription status:', error)
          }
        }
        break
      }

      default:
        console.log(`Unhandled event type: ${event.type}`)
    }

    return NextResponse.json({ received: true })
  } catch (error) {
    console.error('Error processing webhook:', error)
    return NextResponse.json(
      { error: 'Webhook processing failed' },
      { status: 500 }
    )
  }
}
