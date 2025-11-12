import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
)

export async function GET(request: NextRequest) {
  try {
    // Optional: Add auth check for cron job
    const authHeader = request.headers.get('authorization')
    const cronSecret = process.env.CRON_SECRET

    if (cronSecret && authHeader !== `Bearer ${cronSecret}`) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      )
    }

    console.log('⏰ Running auto-expire cron job...')

    // Call the expire_old_setups() PostgreSQL function
    const { data, error } = await supabase.rpc('expire_old_setups')

    if (error) {
      console.error('❌ Failed to expire setups:', error)
      return NextResponse.json(
        { error: 'Failed to expire setups', details: error.message },
        { status: 500 }
      )
    }

    const expiredCount = data || 0

    console.log(`✅ Auto-expired ${expiredCount} setups`)

    return NextResponse.json({
      success: true,
      expired_count: expiredCount,
      message: `Expired ${expiredCount} old setups`,
      timestamp: new Date().toISOString(),
    })

  } catch (error) {
    console.error('❌ Cron error:', error)
    return NextResponse.json(
      { error: 'Cron job failed' },
      { status: 500 }
    )
  }
}

// Also support POST for manual triggers
export async function POST(request: NextRequest) {
  return GET(request)
}
