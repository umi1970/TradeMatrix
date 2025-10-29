'use client'

import { useEffect, useState } from 'react'
import { createBrowserClient } from '@supabase/ssr'
import { Trade } from '@/lib/supabase/queries'

export function useTrades(userId: string) {
  const [trades, setTrades] = useState<Trade[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const supabase = createBrowserClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL!,
      process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
    )

    // Initial fetch
    async function fetchTrades() {
      const { data, error } = await supabase
        .from('trades')
        .select('*')
        .eq('user_id', userId)
        .order('created_at', { ascending: false })

      if (!error && data) {
        setTrades(data as Trade[])
      }
      setLoading(false)
    }

    fetchTrades()

    // Subscribe to real-time updates
    const channel = supabase
      .channel('trades-changes')
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'trades',
          filter: `user_id=eq.${userId}`,
        },
        (payload) => {
          if (payload.eventType === 'INSERT') {
            setTrades((current) => [payload.new as Trade, ...current])
          } else if (payload.eventType === 'UPDATE') {
            setTrades((current) =>
              current.map((trade) =>
                trade.id === payload.new.id ? (payload.new as Trade) : trade
              )
            )
          } else if (payload.eventType === 'DELETE') {
            setTrades((current) =>
              current.filter((trade) => trade.id !== payload.old.id)
            )
          }
        }
      )
      .subscribe()

    return () => {
      supabase.removeChannel(channel)
    }
  }, [userId])

  return { trades, loading }
}
