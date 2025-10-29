'use client'

import { useState } from 'react'
import { Bell, Trash2, Check, CheckCheck } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from '@/components/ui/dropdown-menu'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Badge } from '@/components/ui/badge'
import { Notification, useNotifications } from '@/hooks/use-notifications'
import { formatDistanceToNow } from 'date-fns'

interface NotificationBellProps {
  userId: string
}

const getAlertColor = (kind: string): string => {
  if (kind.includes('_touch') || kind.includes('retest')) return 'text-blue-500'
  if (kind.includes('break') || kind.includes('sweep')) return 'text-orange-500'
  if (kind.includes('trade')) return 'text-green-500'
  if (kind.includes('agent')) return 'text-purple-500'
  return 'text-gray-500'
}

const getAlertIcon = (kind: string): string => {
  if (kind.includes('trade')) return 'Trade'
  if (kind.includes('agent')) return 'Agent'
  if (kind.includes('break')) return 'Break'
  if (kind.includes('retest')) return 'Retest'
  if (kind.includes('touch')) return 'Touch'
  return 'Alert'
}

const getAlertTitle = (notification: Notification): string => {
  switch (notification.kind) {
    case 'range_break':
      return 'Range Break'
    case 'retest_touch':
      return 'Retest Touch'
    case 'asia_sweep':
      return 'Asia Sweep'
    case 'pivot_touch':
      return 'Pivot Touch'
    case 'r1_touch':
      return 'R1 Touch'
    case 's1_touch':
      return 'S1 Touch'
    case 'trade_opened':
      return 'Trade Opened'
    default:
      if (notification.kind.includes('agent_')) {
        const agentType = notification.kind.replace('agent_', '').replace('_completed', '')
        return `${agentType.replace(/_/g, ' ')} Completed`
      }
      return notification.kind
  }
}

const getAlertDescription = (notification: Notification): string => {
  const context = notification.context as Record<string, any>

  switch (notification.kind) {
    case 'trade_opened':
      return `${context.side?.toUpperCase()} ${context.symbol} @ ${context.entry_price}`
    case 'range_break':
    case 'retest_touch':
    case 'asia_sweep':
      return context.symbol || 'Market Alert'
    default:
      return context.agent_type ? `Took ${context.duration_ms}ms` : 'New notification'
  }
}

export function NotificationBell({ userId }: NotificationBellProps) {
  const [open, setOpen] = useState(false)
  const { notifications, unreadCount, markAsRead, markAllAsRead, clearAll, deleteNotification } =
    useNotifications(userId)

  const unreadNotifications = notifications.filter((n) => !n.read)

  const handleNotificationClick = (notification: Notification) => {
    if (!notification.read) {
      markAsRead(notification.id)
    }
  }

  return (
    <DropdownMenu open={open} onOpenChange={setOpen}>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon" className="relative">
          <Bell className="h-5 w-5" />
          {unreadCount > 0 && (
            <span className="absolute -top-1 -right-1 h-5 w-5 rounded-full bg-red-500 text-white text-xs font-bold flex items-center justify-center animate-pulse">
              {unreadCount > 9 ? '9+' : unreadCount}
            </span>
          )}
          <span className="sr-only">Notifications</span>
        </Button>
      </DropdownMenuTrigger>

      <DropdownMenuContent className="w-80" align="end" forceMount>
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3">
          <h3 className="font-semibold">Notifications</h3>
          {unreadCount > 0 && (
            <Badge variant="destructive" className="animate-pulse">
              {unreadCount} new
            </Badge>
          )}
        </div>

        <DropdownMenuSeparator />

        {/* Notifications List */}
        {notifications.length === 0 ? (
          <div className="px-4 py-8 text-center text-sm text-muted-foreground">
            <Bell className="h-8 w-8 mx-auto mb-2 opacity-50" />
            <p>No notifications yet</p>
          </div>
        ) : (
          <ScrollArea className="h-[400px]">
            <div className="space-y-2 p-2">
              {notifications.map((notification) => (
                <div
                  key={notification.id}
                  className={`flex items-start gap-3 rounded-lg p-3 text-sm transition-colors ${
                    notification.read
                      ? 'bg-muted/30 hover:bg-muted/50'
                      : 'bg-blue-50 hover:bg-blue-100 dark:bg-blue-950/30'
                  }`}
                  onClick={() => handleNotificationClick(notification)}
                >
                  {/* Alert Icon */}
                  <div
                    className={`mt-1 flex-shrink-0 text-lg font-semibold ${getAlertColor(notification.kind)}`}
                  >
                    {getAlertIcon(notification.kind)}
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-2">
                      <p className="font-medium">{getAlertTitle(notification)}</p>
                      <span className="text-xs text-muted-foreground flex-shrink-0">
                        {formatDistanceToNow(new Date(notification.created_at), {
                          addSuffix: true,
                        })}
                      </span>
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">
                      {getAlertDescription(notification)}
                    </p>
                  </div>

                  {/* Actions */}
                  <div className="flex gap-1 flex-shrink-0">
                    {!notification.read && (
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-6 w-6 p-0"
                        onClick={(e) => {
                          e.stopPropagation()
                          markAsRead(notification.id)
                        }}
                        title="Mark as read"
                      >
                        <Check className="h-3 w-3" />
                      </Button>
                    )}
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-6 w-6 p-0 hover:text-red-500"
                      onClick={(e) => {
                        e.stopPropagation()
                        deleteNotification(notification.id)
                      }}
                      title="Delete notification"
                    >
                      <Trash2 className="h-3 w-3" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </ScrollArea>
        )}

        <DropdownMenuSeparator />

        {/* Footer Actions */}
        <div className="flex gap-2 px-4 py-3">
          <Button
            variant="outline"
            size="sm"
            className="flex-1"
            onClick={() => markAllAsRead()}
            disabled={unreadCount === 0}
          >
            <CheckCheck className="h-4 w-4 mr-2" />
            Mark all as read
          </Button>
          <Button
            variant="outline"
            size="sm"
            className="flex-1"
            onClick={() => clearAll()}
            disabled={notifications.length === 0}
          >
            <Trash2 className="h-4 w-4 mr-2" />
            Clear all
          </Button>
        </div>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
