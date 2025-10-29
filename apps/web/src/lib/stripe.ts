/**
 * Stripe utility library
 * Server-side Stripe initialization and helpers
 */

import Stripe from 'stripe'

/**
 * Lazily initialized Stripe instance
 */
let stripeInstance: Stripe | null = null

/**
 * Get Stripe client instance (lazy initialization)
 * This should only be used on the server side
 */
export function getStripe(): Stripe {
  if (!stripeInstance) {
    if (!process.env.STRIPE_SECRET_KEY) {
      throw new Error('STRIPE_SECRET_KEY is not set in environment variables')
    }

    stripeInstance = new Stripe(process.env.STRIPE_SECRET_KEY, {
      apiVersion: '2025-09-30.clover',
      typescript: true,
    })
  }

  return stripeInstance
}

/**
 * Create a checkout session for subscription
 */
export async function createCheckoutSession({
  userId,
  email,
  priceId,
  successUrl,
  cancelUrl,
}: {
  userId: string
  email: string
  priceId: string
  successUrl: string
  cancelUrl: string
}): Promise<Stripe.Checkout.Session> {
  try {
    const stripe = getStripe()
    const session = await stripe.checkout.sessions.create({
      mode: 'subscription',
      payment_method_types: ['card'],
      line_items: [
        {
          price: priceId,
          quantity: 1,
        },
      ],
      success_url: successUrl,
      cancel_url: cancelUrl,
      customer_email: email,
      client_reference_id: userId,
      metadata: {
        userId,
      },
      subscription_data: {
        metadata: {
          userId,
        },
      },
      allow_promotion_codes: true,
    })

    return session
  } catch (error) {
    console.error('Error creating checkout session:', error)
    throw error
  }
}

/**
 * Create a billing portal session for managing subscription
 */
export async function createBillingPortalSession({
  customerId,
  returnUrl,
}: {
  customerId: string
  returnUrl: string
}): Promise<Stripe.BillingPortal.Session> {
  try {
    const stripe = getStripe()
    const session = await stripe.billingPortal.sessions.create({
      customer: customerId,
      return_url: returnUrl,
    })

    return session
  } catch (error) {
    console.error('Error creating billing portal session:', error)
    throw error
  }
}

/**
 * Get subscription by ID
 */
export async function getSubscription(
  subscriptionId: string
): Promise<Stripe.Subscription | null> {
  try {
    const stripe = getStripe()
    const subscription = await stripe.subscriptions.retrieve(subscriptionId)
    return subscription
  } catch (error) {
    console.error('Error retrieving subscription:', error)
    return null
  }
}

/**
 * Cancel a subscription at period end
 */
export async function cancelSubscription(
  subscriptionId: string
): Promise<Stripe.Subscription> {
  try {
    const stripe = getStripe()
    const subscription = await stripe.subscriptions.update(subscriptionId, {
      cancel_at_period_end: true,
    })

    return subscription
  } catch (error) {
    console.error('Error canceling subscription:', error)
    throw error
  }
}

/**
 * Reactivate a canceled subscription
 */
export async function reactivateSubscription(
  subscriptionId: string
): Promise<Stripe.Subscription> {
  try {
    const stripe = getStripe()
    const subscription = await stripe.subscriptions.update(subscriptionId, {
      cancel_at_period_end: false,
    })

    return subscription
  } catch (error) {
    console.error('Error reactivating subscription:', error)
    throw error
  }
}

/**
 * Get customer by ID
 */
export async function getCustomer(
  customerId: string
): Promise<Stripe.Customer | null> {
  try {
    const stripe = getStripe()
    const customer = await stripe.customers.retrieve(customerId)

    if (customer.deleted) {
      return null
    }

    return customer as Stripe.Customer
  } catch (error) {
    console.error('Error retrieving customer:', error)
    return null
  }
}

/**
 * Create a customer
 */
export async function createCustomer({
  email,
  userId,
  name,
}: {
  email: string
  userId: string
  name?: string
}): Promise<Stripe.Customer> {
  try {
    const stripe = getStripe()
    const customer = await stripe.customers.create({
      email,
      name,
      metadata: {
        userId,
      },
    })

    return customer
  } catch (error) {
    console.error('Error creating customer:', error)
    throw error
  }
}

/**
 * Map Stripe price ID to subscription tier
 */
export function mapPriceIdToTier(priceId: string): 'starter' | 'pro' | 'expert' | null {
  const priceMap: Record<string, 'starter' | 'pro' | 'expert'> = {
    [process.env.NEXT_PUBLIC_STRIPE_PRICE_STARTER || '']: 'starter',
    [process.env.NEXT_PUBLIC_STRIPE_PRICE_PRO || '']: 'pro',
    [process.env.NEXT_PUBLIC_STRIPE_PRICE_EXPERT || '']: 'expert',
  }

  return priceMap[priceId] || null
}

/**
 * Verify webhook signature
 */
export function verifyWebhookSignature(
  payload: string | Buffer,
  signature: string
): Stripe.Event {
  const webhookSecret = process.env.STRIPE_WEBHOOK_SECRET

  if (!webhookSecret) {
    throw new Error('STRIPE_WEBHOOK_SECRET is not set')
  }

  try {
    const stripe = getStripe()
    const event = stripe.webhooks.constructEvent(payload, signature, webhookSecret)
    return event
  } catch (error) {
    console.error('Error verifying webhook signature:', error)
    throw error
  }
}
