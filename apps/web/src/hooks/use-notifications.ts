'use client'

import { useEffect, useState } from 'react'
import { createBrowserClient } from '@supabase/ssr'
import { Database } from '@/lib/supabase/types'

export type Notification = Database['public']['Tables']['alerts']['Row'] & {
  read: boolean
}

export function useNotifications(userId: string) {
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [unreadCount, setUnreadCount] = useState(0)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const supabase = createBrowserClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL!,
      process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
    )

    // Initial fetch of unsent alerts
    async function fetchNotifications() {
      const { data, error } = await supabase
        .from('alerts')
        .select('*')
        .eq('user_id', userId)
        .eq('sent', false)
        .order('created_at', { ascending: false })
        .limit(50)

      if (!error && data) {
        const notificationsWithRead = (data as Notification[]).map((alert) => ({
          ...alert,
          read: false,
        }))
        setNotifications(notificationsWithRead)
        setUnreadCount(notificationsWithRead.length)
      }
      setLoading(false)
    }

    fetchNotifications()

    // Subscribe to new alerts in real-time
    const alertsChannel = supabase
      .channel(`alerts:${userId}`)
      .on(
        'postgres_changes',
        {
          event: 'INSERT',
          schema: 'public',
          table: 'alerts',
          filter: `user_id=eq.${userId}`,
        },
        (payload) => {
          const newAlert = payload.new as Notification
          newAlert.read = false
          setNotifications((current) => [newAlert, ...current])
          setUnreadCount((current) => current + 1)
        }
      )
      .subscribe()

    // Subscribe to trade updates for notifications
    const tradesChannel = supabase
      .channel(`trades:${userId}`)
      .on(
        'postgres_changes',
        {
          event: 'INSERT',
          schema: 'public',
          table: 'trades',
          filter: `user_id=eq.${userId}`,
        },
        (payload) => {
          const trade = payload.new as any
          const tradeNotification: Notification = {
            id: trade.id,
            user_id: userId,
            symbol_id: null,
            kind: 'trade_opened',
            context: {
              symbol: trade.symbol,
              side: trade.side,
              entry_price: trade.entry_price,
              position_size: trade.position_size,
            },
            sent: false,
            sent_at: null,
            created_at: new Date().toISOString(),
            read: false,
          }
          setNotifications((current) => [tradeNotification, ...current])
          setUnreadCount((current) => current + 1)
        }
      )
      .subscribe()

    // Subscribe to agent logs for notifications
    const agentLogsChannel = supabase
      .channel(`agent_logs:${userId}`)
      .on(
        'postgres_changes',
        {
          event: 'INSERT',
          schema: 'public',
          table: 'agent_logs',
          filter: `user_id=eq.${userId}`,
        },
        (payload) => {
          const agentLog = payload.new as any
          // Only notify for completed agent tasks
          if (agentLog.status === 'completed') {
            const agentNotification: Notification = {
              id: agentLog.id,
              user_id: userId,
              symbol_id: null,
              kind: `agent_${agentLog.agent_type}_completed`,
              context: {
                agent_type: agentLog.agent_type,
                duration_ms: agentLog.duration_ms,
              },
              sent: false,
              sent_at: null,
              created_at: new Date().toISOString(),
              read: false,
            }
            setNotifications((current) => [agentNotification, ...current])
            setUnreadCount((current) => current + 1)
          }
        }
      )
      .subscribe()

    return () => {
      supabase.removeChannel(alertsChannel)
      supabase.removeChannel(tradesChannel)
      supabase.removeChannel(agentLogsChannel)
    }
  }, [userId])

  const markAsRead = (notificationId: string) => {
    setNotifications((current) =>
      current.map((notif) =>
        notif.id === notificationId ? { ...notif, read: true } : notif
      )
    )
    setUnreadCount((current) => Math.max(0, current - 1))
  }

  const markAllAsRead = () => {
    setNotifications((current) =>
      current.map((notif) => ({ ...notif, read: true }))
    )
    setUnreadCount(0)
  }

  const clearAll = () => {
    setNotifications([])
    setUnreadCount(0)
  }

  const deleteNotification = (notificationId: string) => {
    setNotifications((current) =>
      current.filter((notif) => notif.id !== notificationId)
    )
    // Decrement unread count if the notification was unread
    const notification = notifications.find((n) => n.id === notificationId)
    if (notification && !notification.read) {
      setUnreadCount((current) => Math.max(0, current - 1))
    }
  }

  return {
    notifications,
    unreadCount,
    loading,
    markAsRead,
    markAllAsRead,
    clearAll,
    deleteNotification,
  }
}
