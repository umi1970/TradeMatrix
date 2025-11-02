'use client'

import { useEffect } from 'react'
import { useToast } from '@/hooks/use-toast'
import { useNotifications } from '@/hooks/use-notifications'
import { AlertCircle, CheckCircle, Info, TrendingUp } from 'lucide-react'

/**
 * Hook that shows toast notifications for important trading events
 * Complements the NotificationBell dropdown with browser-level toasts
 */
export function useNotificationToasts(userId: string) {
  const { toast } = useToast()
  const { notifications } = useNotifications(userId)

  useEffect(() => {
    // Get the last notification to check if it's new
    if (notifications.length === 0) return

    const lastNotification = notifications[0]

    // Only show toast for recent notifications (within last 5 seconds)
    const notificationAge = Date.now() - new Date(lastNotification.created_at).getTime()
    if (notificationAge > 5000) return

    const levelType = lastNotification.level_type
    const price = lastNotification.target_price.toFixed(2)

    // Liquidity level alerts
    if (levelType === 'yesterday_high') {
      toast({
        title: '🔴 Yesterday High Touched',
        description: `SHORT SETUP: Consider MR-01 reversal @ ${price}`,
        variant: 'default',
      })
      return
    }

    if (levelType === 'yesterday_low') {
      toast({
        title: '🟢 Yesterday Low Touched',
        description: `LONG SETUP: Consider MR-04 reversal @ ${price}`,
        variant: 'default',
      })
      return
    }

    if (levelType === 'pivot_point') {
      toast({
        title: '🟡 Pivot Point Touched',
        description: `Pivot level @ ${price} - Evaluate position management`,
        variant: 'default',
      })
      return
    }

    // Default fallback
    toast({
      title: 'Liquidity Alert',
      description: `Level touched @ ${price}`,
      variant: 'default',
    })
  }, [notifications, toast])
}
