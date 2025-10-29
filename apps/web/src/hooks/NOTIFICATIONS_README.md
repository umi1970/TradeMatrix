# Real-time Notifications System

This directory contains hooks and components for real-time notifications in TradeMatrix.ai using Supabase Realtime.

## Overview

The notification system provides real-time updates for:
- Trading alerts (range breaks, retests, sweeps, level touches)
- Trade opens/closes
- Agent task completions
- System events

## Architecture

```
┌─────────────────────────────────────┐
│  Supabase Realtime Subscriptions    │
│  ├─ alerts table (INSERT)           │
│  ├─ trades table (INSERT/UPDATE)    │
│  └─ agent_logs table (INSERT)       │
└────────────┬────────────────────────┘
             │
             └─► useNotifications Hook
                 │
                 ├─► NotificationBell Component
                 │   ├─ Dropdown menu with list
                 │   ├─ Badge counter (animated)
                 │   ├─ Mark as read / Delete actions
                 │   └─ Clear all / Mark all as read
                 │
                 └─► useNotificationToasts Hook
                     └─► Toast notifications
```

## Components & Hooks

### `useNotifications(userId: string)`

Main hook for managing notifications with real-time Supabase subscriptions.

**Features:**
- Subscribes to 3 tables: `alerts`, `trades`, `agent_logs`
- Maintains local state with unread count
- Provides mark as read / delete / clear functionality
- Auto-unsubscribes on unmount

**Returns:**
```typescript
{
  notifications: Notification[]
  unreadCount: number
  loading: boolean
  markAsRead(notificationId: string): void
  markAllAsRead(): void
  clearAll(): void
  deleteNotification(notificationId: string): void
}
```

**Example:**
```typescript
function MyComponent({ userId }: { userId: string }) {
  const { notifications, unreadCount, markAsRead } = useNotifications(userId)

  return (
    <div>
      <p>You have {unreadCount} unread notifications</p>
      {notifications.map(notif => (
        <div key={notif.id} onClick={() => markAsRead(notif.id)}>
          {notif.kind}
        </div>
      ))}
    </div>
  )
}
```

### `NotificationBell({ userId: string })`

React component that renders a bell icon with dropdown menu.

**Features:**
- Bell icon with animated badge counter
- Dropdown menu showing notification list
- Real-time updates via useNotifications hook
- Color-coded alert icons
- Timestamps (e.g., "5 minutes ago")
- Individual mark as read / delete actions
- Bulk actions (Mark all as read, Clear all)
- Empty state message

**Example:**
```typescript
<NotificationBell userId={user.id} />
```

### `useNotificationToasts(userId: string)`

Hook that displays browser-level toast notifications for important events.

**Features:**
- Shows toast for new trade opens
- Shows toast for market alerts
- Shows toast for agent completions
- Only shows toasts for recent notifications
- Complements NotificationBell dropdown

**Example:**
```typescript
// In a page or layout component
export default function Dashboard({ userId }: { userId: string }) {
  useNotificationToasts(userId)
  return <NotificationBell userId={userId} />
}
```

## Notification Types

### Alert Notifications
From the `alerts` table:

```typescript
kind: 'range_break' | 'retest_touch' | 'asia_sweep' | 'pivot_touch' | 'r1_touch' | 's1_touch'
context: {
  symbol: string
  // Additional alert-specific data
}
```

### Trade Notifications
Generated from `trades` table INSERT events:

```typescript
kind: 'trade_opened'
context: {
  symbol: string
  side: 'long' | 'short'
  entry_price: number
  position_size: number
}
```

### Agent Notifications
Generated from `agent_logs` table completed events:

```typescript
kind: 'agent_chart_watcher_completed' | 'agent_signal_bot_completed' | 'agent_risk_manager_completed' | 'agent_journal_bot_completed'
context: {
  agent_type: string
  duration_ms: number
}
```

## Supabase Setup

### 1. Alerts Table (Migration 003)
```sql
CREATE TABLE alerts (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES auth.users(id),
  symbol_id UUID REFERENCES market_symbols(id),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  kind TEXT NOT NULL,
  context JSONB,
  sent BOOLEAN DEFAULT false,
  sent_at TIMESTAMPTZ
);

CREATE INDEX idx_alerts_user_id ON alerts(user_id);
CREATE INDEX idx_alerts_sent ON alerts(sent) WHERE sent = false;
CREATE INDEX idx_alerts_created_at ON alerts(created_at DESC);
```

### 2. Real-time Permissions
Ensure RLS policies allow the user to subscribe to their own alerts:

```sql
-- Allow users to read their own alerts
CREATE POLICY "Users can read own alerts"
  ON alerts FOR SELECT
  USING (auth.uid() = user_id);

-- Allow service role to insert alerts
CREATE POLICY "Service role can insert alerts"
  ON alerts FOR INSERT
  WITH CHECK (true);
```

### 3. Enable Real-time
In Supabase Dashboard:
1. Go to Database -> Replication
2. Enable replication for `alerts`, `trades`, `agent_logs` tables

## Usage Examples

### Basic Integration in Dashboard Layout

```typescript
// app/(dashboard)/layout.tsx
'use client'

import { Header, NotificationBell } from '@/components/dashboard'
import { useNotificationToasts } from '@/hooks/use-notification-toasts'
import { useToast } from '@/hooks/use-toast'
import { useAuth } from '@/hooks/use-auth'

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const { user } = useAuth()
  const { toast } = useToast()

  // Show toasts for important events
  if (user) {
    useNotificationToasts(user.id)
  }

  return (
    <div>
      <Header user={user} profile={profile} />
      {children}
    </div>
  )
}
```

### Custom Notification Listener

```typescript
function TradeAlert({ userId }: { userId: string }) {
  const { notifications } = useNotifications(userId)

  // Filter only trade notifications
  const tradeNotifs = notifications.filter(n => n.kind === 'trade_opened')

  return (
    <div>
      {tradeNotifs.map(notif => {
        const ctx = notif.context as any
        return (
          <div key={notif.id}>
            {ctx.side} {ctx.symbol} @ {ctx.entry_price}
          </div>
        )
      })}
    </div>
  )
}
```

### Listening for Specific Alert Types

```typescript
function MarketAlerts({ userId }: { userId: string }) {
  const { notifications } = useNotifications(userId)

  const marketAlerts = notifications.filter(n => {
    return ['range_break', 'retest_touch', 'asia_sweep'].includes(n.kind)
  })

  return (
    <AlertsList>
      {marketAlerts.map(alert => (
        <AlertItem key={alert.id} alert={alert} />
      ))}
    </AlertsList>
  )
}
```

## Styling & Customization

### Color-Coded Alerts
The NotificationBell component uses color coding based on alert type:

```typescript
const getAlertColor = (kind: string): string => {
  if (kind.includes('_touch') || kind.includes('retest')) return 'text-blue-500'
  if (kind.includes('break') || kind.includes('sweep')) return 'text-orange-500'
  if (kind.includes('trade')) return 'text-green-500'
  if (kind.includes('agent')) return 'text-purple-500'
  return 'text-gray-500'
}
```

Customize colors in `notification-bell.tsx`.

### Toast Styling
Toast notifications use the default shadcn/ui toast component. Customize in:
- `src/components/ui/toast.tsx` - Toast UI
- `src/hooks/use-notification-toasts.ts` - Toast messages

## Best Practices

1. **Always pass userId**: All hooks require userId for filtering
2. **Use in layout**: Initialize `useNotificationToasts` in page/layout for app-wide toasts
3. **Handle loading state**: Check `notifications.loading` before rendering
4. **Limit history**: Only fetch last 50 notifications by default
5. **Clean up subscriptions**: useNotifications automatically unsubscribes on unmount
6. **Batch operations**: Use `markAllAsRead()` instead of individual calls

## Performance Considerations

- Notifications are limited to 50 items (configurable in hook)
- Realtime subscriptions are channel-based and efficient
- Unread count is tracked separately for quick badge updates
- Unread notifications have `.read = false` status in memory only
- No database writes for read status (only in memory UI)

## Troubleshooting

### No notifications appearing
1. Check RLS policies allow user to read their own alerts
2. Verify real-time is enabled for alerts/trades/agent_logs tables
3. Check browser console for Supabase errors
4. Verify userId is correct

### Toast notifications not showing
1. Ensure `useNotificationToasts` is called in layout
2. Check `Toaster` component is in root layout
3. Verify notification timestamp is recent (within 5 seconds)

### Dropdown menu not opening
1. Check NotificationBell is wrapped in client component
2. Verify DropdownMenu from shadcn/ui is installed
3. Check z-index conflicts with other modals

## Future Enhancements

- [ ] Notification preferences (per type)
- [ ] Sound notifications for critical alerts
- [ ] Email digest summaries
- [ ] Slack/Discord integration
- [ ] Push notifications (PWA)
- [ ] Notification history export
- [ ] Analytics on notification interactions
