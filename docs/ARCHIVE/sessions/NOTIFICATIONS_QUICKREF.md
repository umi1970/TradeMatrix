# Real-time Notifications - Quick Reference

## Installation Status
✅ Complete - Ready to use

## Key Files
```
apps/web/src/
├── hooks/
│   ├── use-notifications.ts          ← Main notification hook
│   ├── use-notification-toasts.ts    ← Toast notifications
│   └── NOTIFICATIONS_README.md       ← Detailed docs
├── components/dashboard/
│   ├── notification-bell.tsx         ← Dropdown component
│   └── header.tsx                    ← (Updated - integrated bell)
└── lib/supabase/
    └── types.ts                      ← (Updated - alerts table type)
```

## Quick Start

### 1. Verify Real-time is Enabled
Go to Supabase Console:
- Database → Replication
- Enable for: `alerts`, `trades`, `agent_logs` tables

### 2. Use in Your Dashboard
```typescript
'use client'

import { Header } from '@/components/dashboard'
import { useNotificationToasts } from '@/hooks/use-notification-toasts'

export default function DashboardPage({ userId }: { userId: string }) {
  // Show toast notifications
  useNotificationToasts(userId)

  return (
    <>
      {/* Header already has NotificationBell integrated */}
      <Header user={user} profile={profile} />
      {/* Rest of dashboard */}
    </>
  )
}
```

## Usage Examples

### Display Notifications List
```typescript
import { useNotifications } from '@/hooks/use-notifications'

function NotificationsList({ userId }: { userId: string }) {
  const { notifications, unreadCount, markAsRead } = useNotifications(userId)

  return (
    <div>
      <h2>Notifications ({unreadCount})</h2>
      {notifications.map(notif => (
        <div key={notif.id} onClick={() => markAsRead(notif.id)}>
          {notif.kind}: {notif.context?.symbol}
        </div>
      ))}
    </div>
  )
}
```

### Filter by Type
```typescript
const { notifications } = useNotifications(userId)

// Only trade alerts
const trades = notifications.filter(n => n.kind === 'trade_opened')

// Only market alerts
const marketAlerts = notifications.filter(n =>
  ['range_break', 'retest_touch', 'asia_sweep'].includes(n.kind)
)
```

### Mark as Read
```typescript
const { markAsRead, markAllAsRead } = useNotifications(userId)

// Mark single notification
markAsRead(notificationId)

// Mark all as read
markAllAsRead()
```

## Notification Kinds

```
Trading Alerts:
- range_break      → Price broke daily range
- retest_touch     → Price retested level
- asia_sweep       → Asia session sweep
- pivot_touch      → Pivot point touched
- r1_touch         → Resistance 1 touched
- s1_touch         → Support 1 touched

Trade Events:
- trade_opened     → New trade created

Agent Events:
- agent_*_completed → Agent task finished
```

## Real-time Subscription Structure

```typescript
// Alerts from alerts table
alerts:{userId}
├─ INSERT event
└─ kind: string
   └─ context: JSONB

// Trade opens from trades table
trades:{userId}
├─ INSERT event
└─ symbol, side, entry_price, position_size

// Agent completions from agent_logs table
agent_logs:{userId}
├─ INSERT event (status=completed)
└─ agent_type, duration_ms
```

## Component Props

### NotificationBell
```typescript
<NotificationBell userId={user.id} />
```

| Prop | Type | Required |
|------|------|----------|
| userId | string | Yes |

### useNotifications
```typescript
const {
  notifications,      // Notification[]
  unreadCount,        // number
  loading,            // boolean
  markAsRead,         // (id: string) => void
  markAllAsRead,      // () => void
  clearAll,           // () => void
  deleteNotification, // (id: string) => void
} = useNotifications(userId)
```

### useNotificationToasts
```typescript
useNotificationToasts(userId)
// No return value - automatically shows toasts
```

## Customization

### Change Toast Format
File: `apps/web/src/hooks/use-notification-toasts.ts`

```typescript
if (kind === 'trade_opened') {
  toast({
    title: `Custom: ${symbol}`,
    description: `Custom message`,
    variant: 'default', // or 'destructive'
  })
}
```

### Change Icon Colors
File: `apps/web/src/components/dashboard/notification-bell.tsx`

```typescript
const getAlertColor = (kind: string): string => {
  if (kind.includes('trade')) return 'text-custom-color'
  // ...
}
```

### Change Dropdown Width
File: `apps/web/src/components/dashboard/notification-bell.tsx`

```typescript
<DropdownMenuContent className="w-96" align="end"> {/* Change w-80 to w-96 */}
```

## Debugging

### Check Subscriptions
```typescript
const { notifications } = useNotifications(userId)
useEffect(() => {
  console.log('Notifications:', notifications)
  console.log('Unread:', unreadCount)
}, [notifications, unreadCount])
```

### Monitor Toast Events
```typescript
const { toast } = useToast()
useEffect(() => {
  toast({
    title: 'Debug',
    description: 'Notifications loaded',
  })
}, [])
```

### Supabase Console
1. Go to **Logs** → **Function Logs**
2. Filter by table/event
3. Check for real-time messages

## Performance Tips

- ✅ Subscriptions auto-unsubscribe on unmount
- ✅ Limited to 50 notifications (configurable)
- ✅ Unread status in memory only (no DB writes)
- ✅ Badge counter updates instantly
- ✅ ScrollArea prevents DOM bloat

## Known Issues & Solutions

| Issue | Solution |
|-------|----------|
| No notifications | Enable real-time in Supabase Console |
| Toast not showing | Call `useNotificationToasts(userId)` in layout |
| Dropdown won't open | Check NotificationBell is in client component |
| Wrong userId | Verify `user.id` is passed correctly |
| Stale notifications | Refresh page (hook fetches on mount) |

## Next Steps

1. ✅ Code complete
2. ⬜ Enable real-time in Supabase
3. ⬜ Test with sample alerts
4. ⬜ Monitor in production
5. ⬜ Gather user feedback
6. ⬜ Add notification preferences (optional)

## Documentation

- **Full Guide:** `/apps/web/src/hooks/NOTIFICATIONS_README.md`
- **Implementation:** `/NOTIFICATIONS_IMPLEMENTATION.md`
- **This File:** `/NOTIFICATIONS_QUICKREF.md`

## Support

- Check the full README for detailed API
- See NOTIFICATIONS_IMPLEMENTATION.md for architecture
- Review code comments in source files
- Check Supabase docs: https://supabase.com/docs/guides/realtime

---

**Status:** ✅ Ready to use
**Last Updated:** 2025-10-29
