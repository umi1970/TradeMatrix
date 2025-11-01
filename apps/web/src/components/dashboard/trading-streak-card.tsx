'use client'

import { useEffect, useState } from 'react'
import { createBrowserClient } from '@/lib/supabase/client'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Loader2, TrendingUp, TrendingDown } from 'lucide-react'

interface Trade {
  id: string
  pnl: number | null
  status: 'open' | 'closed' | 'cancelled'
  created_at: string
}

interface StreakData {
  type: 'win' | 'loss' | 'none'
  count: number
  emoji: string
}

export function TradingStreakCard() {
  const [streak, setStreak] = useState<StreakData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function calculateStreak() {
      try {
        const supabase = createBrowserClient()

        // Get current user
        const { data: { user }, error: userError } = await supabase.auth.getUser()
        if (userError || !user) {
          setError('Authentication required')
          setLoading(false)
          return
        }

        // Fetch closed trades ordered by date
        const { data: trades, error: tradesError } = await supabase
          .from('trades')
          .select('id, pnl, status, created_at')
          .eq('user_id', user.id)
          .eq('status', 'closed')
          .not('pnl', 'is', null)
          .order('created_at', { ascending: false })

        if (tradesError) {
          throw tradesError
        }

        if (!trades || trades.length === 0) {
          setStreak({
            type: 'none',
            count: 0,
            emoji: '📊'
          })
          setLoading(false)
          return
        }

        // Calculate current streak
        let currentStreak = 0
        let streakType: 'win' | 'loss' | 'none' = 'none'

        if (trades.length > 0) {
          const firstTrade = trades[0]
          streakType = (firstTrade.pnl ?? 0) > 0 ? 'win' : 'loss'
          currentStreak = 1

          // Count consecutive wins or losses
          for (let i = 1; i < trades.length; i++) {
            const currentType = (trades[i].pnl ?? 0) > 0 ? 'win' : 'loss'
            if (currentType === streakType) {
              currentStreak++
            } else {
              break
            }
          }
        }

        const emoji = streakType === 'win' ? '🔥' : streakType === 'loss' ? '📉' : '📊'

        setStreak({
          type: streakType,
          count: currentStreak,
          emoji
        })
      } catch (err) {
        console.error('Error calculating streak:', err)
        setError('Failed to calculate streak')
      } finally {
        setLoading(false)
      }
    }

    calculateStreak()
  }, [])

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Trading Streak</CardTitle>
        </CardHeader>
        <CardContent className="flex items-center justify-center py-8">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Trading Streak</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-destructive">{error}</p>
        </CardContent>
      </Card>
    )
  }

  if (streak?.type === 'none') {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Trading Streak</CardTitle>
          <CardDescription>Track your consecutive wins or losses</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <span className="text-6xl mb-4">📊</span>
            <p className="text-sm text-muted-foreground">
              No trading history yet
            </p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Trading Streak</CardTitle>
        <CardDescription>Your current consecutive streak</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex flex-col items-center justify-center py-6 space-y-4">
          {/* Emoji and Count */}
          <div className="flex items-center space-x-3">
            <span className="text-6xl">{streak!.emoji}</span>
            <div className="text-5xl font-bold">
              {streak!.count}
            </div>
          </div>

          {/* Streak Type */}
          <div className="flex items-center space-x-2">
            {streak!.type === 'win' ? (
              <>
                <TrendingUp className="h-5 w-5 text-green-500" />
                <span className="text-xl font-semibold text-green-500">
                  {streak!.count === 1 ? 'Win' : 'Wins'} in a row!
                </span>
              </>
            ) : (
              <>
                <TrendingDown className="h-5 w-5 text-red-500" />
                <span className="text-xl font-semibold text-red-500">
                  {streak!.count === 1 ? 'Loss' : 'Losses'} in a row
                </span>
              </>
            )}
          </div>

          {/* Encouragement Message */}
          <p className="text-sm text-muted-foreground text-center">
            {streak!.type === 'win'
              ? "Keep up the great work! Stay disciplined."
              : "Stay focused and stick to your strategy."}
          </p>
        </div>
      </CardContent>
    </Card>
  )
}
