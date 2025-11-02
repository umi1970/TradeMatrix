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

    // Initial fetch of triggered alerts
    async function fetchNotifications() {
      const { data, error } = await supabase
        .from('alerts')
        .select('*')
        .eq('user_id', userId)
        .eq('status', 'triggered')
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

    // TODO: Subscribe to trade updates for notifications (disabled for now)
    // const tradesChannel = supabase.channel(`trades:${userId}`)...

    // TODO: Subscribe to agent logs for notifications (disabled for now)
    // const agentLogsChannel = supabase.channel(`agent_logs:${userId}`)...

    return () => {
      supabase.removeChannel(alertsChannel)
      // supabase.removeChannel(tradesChannel)
      // supabase.removeChannel(agentLogsChannel)
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
