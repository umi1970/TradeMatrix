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

    const kind = lastNotification.kind
    const context = lastNotification.context as Record<string, any>

    // Trade opened notification
    if (kind === 'trade_opened') {
      const symbol = context.symbol || 'Trade'
      const side = context.side?.toUpperCase() || 'TRADE'
      const price = context.entry_price?.toFixed(2) || '0.00'

      toast({
        title: `Trade Opened: ${side} ${symbol}`,
        description: `Entry at ${price}`,
        variant: 'default',
      })
      return
    }

    // Market alerts
    if (
      kind === 'range_break' ||
      kind === 'retest_touch' ||
      kind === 'asia_sweep' ||
      kind === 'pivot_touch' ||
      kind === 'r1_touch' ||
      kind === 's1_touch'
    ) {
      const symbol = context.symbol || 'Market'
      const alertTitle = {
        range_break: 'Range Break',
        retest_touch: 'Retest Touch',
        asia_sweep: 'Asia Sweep',
        pivot_touch: 'Pivot Touch',
        r1_touch: 'R1 Touch',
        s1_touch: 'S1 Touch',
      }[kind] || 'Alert'

      toast({
        title: `${alertTitle}: ${symbol}`,
        description: 'Check your chart for details',
        variant: 'default',
      })
      return
    }

    // Agent completion notifications
    if (kind.includes('agent_')) {
      const agentType = kind.replace('agent_', '').replace('_completed', '')
      const agentName = agentType.replace(/_/g, ' ').toUpperCase()
      const duration = context.duration_ms ? `${(context.duration_ms / 1000).toFixed(1)}s` : 'completed'

      toast({
        title: `${agentName} Completed`,
        description: `Execution time: ${duration}`,
        variant: 'default',
      })
      return
    }
  }, [notifications, toast])
}
