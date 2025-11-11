import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
)

/**
 * TradingView Monitoring Webhook
 *
 * Receives alerts from Pine Script when Entry/SL/TP levels are hit.
 * Updates setup status, calculates outcome and P&L, sends push notifications.
 *
 * Expected payload from Pine Script:
 * {
 *   "setup_id": "uuid",
 *   "event": "entry_hit" | "sl_hit" | "tp_hit",
 *   "price": 19500.25,
 *   "symbol": "DAX"
 * }
 */

interface MonitoringWebhookPayload {
  setup_id: string
  event: 'entry_hit' | 'sl_hit' | 'tp_hit'
  price: number
  symbol: string
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.text()
    console.log('📥 TradingView Monitor Webhook received:', body.substring(0, 200))

    let payload: MonitoringWebhookPayload

    try {
      payload = JSON.parse(body)
    } catch (e) {
      console.error('❌ Invalid JSON:', e)
      return NextResponse.json(
        { error: 'Invalid JSON payload' },
        { status: 400 }
      )
    }

    const { setup_id, event, price, symbol } = payload

    if (!setup_id || !event || !price || !symbol) {
      console.error('❌ Missing required fields:', { setup_id, event, price, symbol })
      return NextResponse.json(
        { error: 'Missing required fields: setup_id, event, price, symbol' },
        { status: 400 }
      )
    }

    console.log(`🎯 Processing ${event} for setup ${setup_id} at ${price}`)

    // Step 1: Fetch setup from database
    const { data: setup, error: fetchError } = await supabase
      .from('setups')
      .select('id, side, entry_price, stop_loss, take_profit, status, entry_hit, user_id')
      .eq('id', setup_id)
      .single()

    if (fetchError || !setup) {
      console.error(`❌ Setup ${setup_id} not found:`, fetchError)
      return NextResponse.json(
        { error: `Setup ${setup_id} not found` },
        { status: 404 }
      )
    }

    console.log(`✅ Setup found: ${setup.side} @ ${setup.entry_price} (status: ${setup.status})`)

    // Step 2: Determine outcome and P&L based on event
    const now = new Date().toISOString()
    let updateData: any = {
      last_price: price,
      last_checked_at: now,
      updated_at: now,
    }

    switch (event) {
      case 'entry_hit':
        // Entry level hit
        updateData.entry_hit = true
        updateData.entry_hit_at = now
        updateData.status = 'entry_hit'
        console.log(`✅ Entry hit at ${price}`)
        break

      case 'sl_hit':
        // Stop Loss hit
        updateData.sl_hit_at = now
        updateData.status = 'sl_hit'

        // Determine outcome: loss (if entry hit first) or invalidated (if SL before entry)
        if (setup.entry_hit) {
          updateData.outcome = 'loss'
          // Calculate P&L (negative)
          const pnl = calculatePnL(setup.entry_price, price, setup.side)
          updateData.pnl_percent = pnl
          console.log(`❌ LOSS: Entry hit, then SL hit. P&L: ${pnl}%`)
        } else {
          updateData.outcome = 'invalidated'
          updateData.pnl_percent = 0
          console.log(`⚠️ INVALIDATED: SL hit before entry`)
        }
        break

      case 'tp_hit':
        // Take Profit hit
        updateData.tp_hit_at = now
        updateData.status = 'tp_hit'

        // Determine outcome: win (if entry hit first) or missed (if TP before entry)
        if (setup.entry_hit) {
          updateData.outcome = 'win'
          // Calculate P&L (positive)
          const pnl = calculatePnL(setup.entry_price, price, setup.side)
          updateData.pnl_percent = pnl
          console.log(`✅ WIN: Entry hit, then TP hit. P&L: ${pnl}%`)
        } else {
          updateData.outcome = 'missed'
          updateData.pnl_percent = 0
          console.log(`⚠️ MISSED: TP hit before entry`)
        }
        break

      default:
        console.error('❌ Unknown event:', event)
        return NextResponse.json(
          { error: `Unknown event: ${event}` },
          { status: 400 }
        )
    }

    // Step 3: Update setup in database
    const { data: updatedSetup, error: updateError } = await supabase
      .from('setups')
      .update(updateData)
      .eq('id', setup_id)
      .select()
      .single()

    if (updateError) {
      console.error('❌ Failed to update setup:', updateError)
      return NextResponse.json(
        { error: 'Failed to update setup', details: updateError },
        { status: 500 }
      )
    }

    console.log(`✅ Setup updated: ${updatedSetup.status} (outcome: ${updatedSetup.outcome})`)

    // Step 4: Send push notification to user (if user exists)
    if (setup.user_id) {
      try {
        await sendPushNotification(setup.user_id, {
          title: `${symbol} Setup Update`,
          body: getNotificationMessage(event, updatedSetup.outcome, price),
          data: {
            setup_id: setup_id,
            event: event,
            outcome: updatedSetup.outcome,
          },
        })
        console.log(`✅ Push notification sent to user ${setup.user_id}`)
      } catch (notifError) {
        console.warn('⚠️ Failed to send push notification:', notifError)
        // Don't fail the webhook if notification fails
      }
    }

    // Step 5: Return success response
    return NextResponse.json({
      success: true,
      setup_id: setup_id,
      event: event,
      status: updatedSetup.status,
      outcome: updatedSetup.outcome,
      pnl_percent: updatedSetup.pnl_percent,
      price: price,
    })

  } catch (error) {
    console.error('❌ Webhook processing error:', error)
    return NextResponse.json(
      { error: 'Internal server error', details: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    )
  }
}

// =====================================================================
// HELPER FUNCTIONS
// =====================================================================

/**
 * Calculate P&L percentage
 *
 * For long: P&L = ((exit - entry) / entry) * 100
 * For short: P&L = ((entry - exit) / entry) * 100
 */
function calculatePnL(entry: number, exit: number, side: string): number {
  if (side === 'long') {
    return parseFloat((((exit - entry) / entry) * 100).toFixed(2))
  } else {
    // short
    return parseFloat((((entry - exit) / entry) * 100).toFixed(2))
  }
}

/**
 * Generate notification message based on event and outcome
 */
function getNotificationMessage(
  event: string,
  outcome: string | null,
  price: number
): string {
  switch (event) {
    case 'entry_hit':
      return `Entry level hit at ${price}. Trade is now active.`
    case 'sl_hit':
      if (outcome === 'loss') {
        return `Stop Loss hit at ${price}. Trade closed with a loss.`
      } else if (outcome === 'invalidated') {
        return `Stop Loss hit at ${price} before entry. Setup invalidated.`
      }
      return `Stop Loss hit at ${price}.`
    case 'tp_hit':
      if (outcome === 'win') {
        return `Take Profit hit at ${price}. Trade closed with a win! 🎉`
      } else if (outcome === 'missed') {
        return `Take Profit hit at ${price} before entry. Setup missed.`
      }
      return `Take Profit hit at ${price}.`
    default:
      return `Price update: ${price}`
  }
}

/**
 * Send push notification to user
 *
 * Fetches user's push subscriptions and sends notification via Web Push API
 */
async function sendPushNotification(
  userId: string,
  notification: {
    title: string
    body: string
    data?: any
  }
) {
  // Fetch user's push subscriptions from alert_subscriptions table
  const { data: subscriptions, error } = await supabase
    .from('alert_subscriptions')
    .select('id, endpoint, p256dh_key, auth_key')
    .eq('user_id', userId)
    .eq('active', true)

  if (error || !subscriptions || subscriptions.length === 0) {
    console.log(`No active push subscriptions for user ${userId}`)
    return
  }

  console.log(`Sending push to ${subscriptions.length} subscription(s)`)

  // Send push notification via Edge Function (reuse existing liquidity alert push function)
  // Or implement Web Push API directly here

  // For now, log that we would send push (actual implementation depends on existing push setup)
  console.log(`📨 Would send push notification:`, {
    userId,
    title: notification.title,
    body: notification.body,
    subscriptionCount: subscriptions.length,
  })

  // TODO: Implement actual push sending via:
  // Option 1: Call existing Edge Function (/api/send-push)
  // Option 2: Use web-push library directly here
  // Option 3: Queue job in Celery for push sending
}

// Allow GET for testing/documentation
export async function GET() {
  return NextResponse.json({
    message: 'TradingView Monitoring Webhook',
    url: `${process.env.NEXT_PUBLIC_APP_URL}/api/webhooks/tradingview-monitor`,
    method: 'POST',
    expected_payload: {
      setup_id: 'uuid',
      event: 'entry_hit | sl_hit | tp_hit',
      price: 19500.25,
      symbol: 'DAX',
    },
    response: {
      success: true,
      setup_id: 'uuid',
      event: 'entry_hit',
      status: 'entry_hit',
      outcome: null,
      pnl_percent: null,
      price: 19500.25,
    },
  })
}
