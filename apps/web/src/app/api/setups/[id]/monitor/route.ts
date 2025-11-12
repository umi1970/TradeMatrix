import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
)

interface MonitorParams {
  params: {
    id: string
  }
}

export async function POST(request: NextRequest, { params }: MonitorParams) {
  try {
    const { id: setupId } = params

    // Get CSV file from FormData
    const formData = await request.formData()
    const csvFile = formData.get('csv') as File

    if (!csvFile) {
      return NextResponse.json(
        { error: 'CSV file is required' },
        { status: 400 }
      )
    }

    // Read CSV content
    const csvText = await csvFile.text()

    // Parse CSV to get last (most recent) candle
    const lines = csvText.trim().split('\n')
    if (lines.length < 2) {
      return NextResponse.json(
        { error: 'Invalid CSV: No data rows found' },
        { status: 400 }
      )
    }

    // Get last line (most recent candle)
    const lastLine = lines[lines.length - 1]
    const values = lastLine.split(',')

    // Expected CSV format: time,open,high,low,close,volume (or similar)
    // We need: close price (column 4, index 4 if 0-indexed with header)
    let currentPrice: number

    try {
      // Try to find close price
      // Typical format: time,open,high,low,close,volume
      const closePrice = parseFloat(values[4])
      if (isNaN(closePrice)) {
        throw new Error('Invalid close price')
      }
      currentPrice = closePrice
    } catch (err) {
      return NextResponse.json(
        { error: 'Failed to parse CSV: Could not extract close price. Expected format: time,open,high,low,close,volume' },
        { status: 400 }
      )
    }

    // Get setup from database
    const { data: setup, error: setupError } = await supabase
      .from('setups')
      .select('*')
      .eq('id', setupId)
      .single()

    if (setupError || !setup) {
      return NextResponse.json(
        { error: 'Setup not found' },
        { status: 404 }
      )
    }

    // Check if setup is in correct status
    if (setup.status !== 'entry_hit' && setup.status !== 'pending') {
      return NextResponse.json(
        { error: `Cannot monitor setup with status: ${setup.status}. Must be 'pending' or 'entry_hit'` },
        { status: 400 }
      )
    }

    const entryPrice = setup.entry_price
    const stopLoss = setup.stop_loss
    const takeProfit = setup.take_profit
    const side = setup.side // 'long' or 'short'

    // Tolerance for entry hit detection (0.01%)
    const entryTolerance = entryPrice * 0.0001

    let newStatus = setup.status
    let outcome = setup.outcome
    let slHitAt = setup.sl_hit_at
    let tpHitAt = setup.tp_hit_at
    let entryHit = setup.entry_hit
    let entryHitAt = setup.entry_hit_at
    let pnlPercent = setup.pnl_percent
    let closedAt = setup.closed_at

    // Check if entry was hit (for pending setups)
    if (setup.status === 'pending') {
      const entryHitCheck = Math.abs(currentPrice - entryPrice) <= entryTolerance
      if (entryHitCheck) {
        newStatus = 'entry_hit'
        entryHit = true
        entryHitAt = new Date().toISOString()
      }
    }

    // Check for SL/TP hit (for entry_hit setups or newly hit entries)
    if (newStatus === 'entry_hit') {
      if (side === 'long') {
        // Long: SL below entry, TP above entry
        if (currentPrice <= stopLoss) {
          newStatus = 'sl_hit'
          outcome = 'loss'
          slHitAt = new Date().toISOString()
          closedAt = new Date().toISOString()
          // Calculate P&L
          pnlPercent = ((currentPrice - entryPrice) / entryPrice) * 100
        } else if (currentPrice >= takeProfit) {
          newStatus = 'tp_hit'
          outcome = 'win'
          tpHitAt = new Date().toISOString()
          closedAt = new Date().toISOString()
          pnlPercent = ((currentPrice - entryPrice) / entryPrice) * 100
        }
      } else if (side === 'short') {
        // Short: SL above entry, TP below entry
        if (currentPrice >= stopLoss) {
          newStatus = 'sl_hit'
          outcome = 'loss'
          slHitAt = new Date().toISOString()
          closedAt = new Date().toISOString()
          pnlPercent = ((entryPrice - currentPrice) / entryPrice) * 100
        } else if (currentPrice <= takeProfit) {
          newStatus = 'tp_hit'
          outcome = 'win'
          tpHitAt = new Date().toISOString()
          closedAt = new Date().toISOString()
          pnlPercent = ((entryPrice - currentPrice) / entryPrice) * 100
        }
      }
    }

    // Update setup in database
    const { data: updatedSetup, error: updateError } = await supabase
      .from('setups')
      .update({
        status: newStatus,
        entry_hit: entryHit,
        entry_hit_at: entryHitAt,
        sl_hit_at: slHitAt,
        tp_hit_at: tpHitAt,
        outcome: outcome,
        pnl_percent: pnlPercent ? Math.round(pnlPercent * 100) / 100 : null,
        last_price: currentPrice,
        last_checked_at: new Date().toISOString(),
        closed_at: closedAt,
        updated_at: new Date().toISOString(),
      })
      .eq('id', setupId)
      .select()
      .single()

    if (updateError) {
      console.error('Failed to update setup:', updateError)
      return NextResponse.json(
        { error: 'Failed to update setup status' },
        { status: 500 }
      )
    }

    // Build response message
    let message = ''
    if (newStatus === 'entry_hit' && setup.status === 'pending') {
      message = '🎯 Entry Hit! Trade is now active and being monitored.'
    } else if (newStatus === 'sl_hit') {
      message = `❌ Stop Loss Hit! Trade closed with ${pnlPercent?.toFixed(2)}% loss.`
    } else if (newStatus === 'tp_hit') {
      message = `✅ Take Profit Hit! Trade closed with ${pnlPercent?.toFixed(2)}% profit.`
    } else {
      message = `📊 Trade monitored. Current price: ${currentPrice.toFixed(5)}`
    }

    console.log(`✅ Monitored setup ${setupId}: ${newStatus}`)

    return NextResponse.json({
      message,
      status: newStatus,
      current_price: currentPrice,
      entry_hit: entryHit,
      outcome: outcome,
      pnl_percent: pnlPercent,
      setup: updatedSetup,
    })

  } catch (error) {
    console.error('❌ Monitor setup error:', error)
    return NextResponse.json(
      { error: 'Failed to monitor setup' },
      { status: 500 }
    )
  }
}
