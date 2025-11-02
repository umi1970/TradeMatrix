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

const getAlertColor = (levelType: string): string => {
  if (levelType === 'yesterday_high') return 'text-red-500'
  if (levelType === 'yesterday_low') return 'text-green-500'
  if (levelType === 'pivot_point') return 'text-yellow-500'
  return 'text-blue-500'
}

const getAlertIcon = (levelType: string): string => {
  if (levelType === 'yesterday_high') return '🔴'
  if (levelType === 'yesterday_low') return '🟢'
  if (levelType === 'pivot_point') return '🟡'
  return '🔔'
}

const getAlertTitle = (notification: Notification): string => {
  switch (notification.level_type) {
    case 'yesterday_high':
      return 'Yesterday High Touched'
    case 'yesterday_low':
      return 'Yesterday Low Touched'
    case 'pivot_point':
      return 'Pivot Point Touched'
    default:
      return 'Liquidity Alert'
  }
}

const getAlertDescription = (notification: Notification): string => {
  const price = notification.target_price.toFixed(2)
  switch (notification.level_type) {
    case 'yesterday_high':
      return `SHORT SETUP: Consider MR-01 reversal @ ${price}`
    case 'yesterday_low':
      return `LONG SETUP: Consider MR-04 reversal @ ${price}`
    case 'pivot_point':
      return `Pivot level @ ${price} - Evaluate position management`
    default:
      return `Level @ ${price}`
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
                    className={`mt-1 flex-shrink-0 text-lg font-semibold ${getAlertColor(notification.level_type)}`}
                  >
                    {getAlertIcon(notification.level_type)}
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
