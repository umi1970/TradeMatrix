# Real-time Notifications Implementation Guide

## Overview

This document details the complete implementation of real-time notifications in TradeMatrix.ai using Supabase Realtime.

**Date:** 2025-10-29
**Status:** Complete
**Components:** 3 new files, 2 modified files

## Files Created/Modified

### New Files

1. **`apps/web/src/hooks/use-notifications.ts`** (165 lines)
   - Main hook for notification management
   - Subscribes to alerts, trades, and agent_logs tables
   - Provides mark as read, delete, and clear functionality

2. **`apps/web/src/components/dashboard/notification-bell.tsx`** (177 lines)
   - React component with bell icon and dropdown
   - Displays notification list with color-coded icons
   - Shows unread counter with animation
   - Includes bulk actions (mark all as read, clear all)

3. **`apps/web/src/hooks/use-notification-toasts.ts`** (68 lines)
   - Hook for browser-level toast notifications
   - Shows toasts for new trades, market alerts, and agent completions
   - Complements the dropdown notification list

### Modified Files

1. **`apps/web/src/lib/supabase/types.ts`**
   - Added alerts table type definition
   - Includes Row, Insert, and Update types
   - Added relationships to profiles and market_symbols tables

2. **`apps/web/src/components/dashboard/header.tsx`**
   - Imported NotificationBell component
   - Replaced dummy bell button with NotificationBell component
   - Removed unused Bell icon import

3. **`apps/web/src/components/dashboard/index.ts`**
   - Added export for NotificationBell component

## Implementation Details

### 1. Database Schema (Already in Migration 003)

The alerts table stores real-time notifications:

```sql
CREATE TABLE alerts (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  symbol_id UUID REFERENCES market_symbols(id) ON DELETE CASCADE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  kind TEXT NOT NULL,
  context JSONB,
  sent BOOLEAN DEFAULT false,
  sent_at TIMESTAMPTZ
);
```

**Supported alert kinds:**
- `range_break` - Price broke out of daily range
- `retest_touch` - Price touched yesterday's level
- `asia_sweep` - Asia session sweep pattern
- `pivot_touch` - Price touched pivot point
- `r1_touch` - Resistance 1 touched
- `s1_touch` - Support 1 touched

### 2. Supabase Realtime Subscriptions

The `useNotifications` hook subscribes to three Postgres change events:

**a) Alerts Table (New Trading Alerts)**
```typescript
supabase
  .channel(`alerts:${userId}`)
  .on('postgres_changes', {
    event: 'INSERT',
    schema: 'public',
    table: 'alerts',
    filter: `user_id=eq.${userId}`,
  }, handleNewAlert)
  .subscribe()
```

**b) Trades Table (New Trade Opens)**
```typescript
supabase
  .channel(`trades:${userId}`)
  .on('postgres_changes', {
    event: 'INSERT',
    schema: 'public',
    table: 'trades',
    filter: `user_id=eq.${userId}`,
  }, handleNewTrade)
  .subscribe()
```

**c) Agent Logs Table (Agent Completions)**
```typescript
supabase
  .channel(`agent_logs:${userId}`)
  .on('postgres_changes', {
    event: 'INSERT',
    schema: 'public',
    table: 'agent_logs',
    filter: `user_id=eq.${userId}`,
  }, handleAgentCompletion)
  .subscribe()
```

### 3. Component Structure

**NotificationBell Component:**

```
┌─ NotificationBell
│  ├─ Bell Icon Button
│  │  ├─ Badge Counter (animated pulse)
│  │  └─ Click to open dropdown
│  └─ Dropdown Menu
│     ├─ Header
│     │  ├─ "Notifications" Title
│     │  └─ Badge showing unread count
│     ├─ ScrollArea (400px height)
│     │  ├─ Empty State (if no notifications)
│     │  └─ Notification Items
│     │     ├─ Icon (color-coded by type)
│     │     ├─ Title + Timestamp
│     │     ├─ Description
│     │     └─ Actions (mark as read, delete)
│     └─ Footer Actions
│        ├─ Mark all as read
│        └─ Clear all
```

### 4. Notification Types

Three main notification sources:

**Trading Alerts:**
```typescript
{
  kind: 'range_break' | 'retest_touch' | 'asia_sweep' | 'pivot_touch' | 'r1_touch' | 's1_touch'
  context: { symbol: string, ... }
}
```

**Trade Events:**
```typescript
{
  kind: 'trade_opened'
  context: {
    symbol: string
    side: 'long' | 'short'
    entry_price: number
    position_size: number
  }
}
```

**Agent Events:**
```typescript
{
  kind: 'agent_chart_watcher_completed' | 'agent_signal_bot_completed' | ...
  context: {
    agent_type: string
    duration_ms: number
  }
}
```

### 5. Real-time Update Flow

```
1. Backend creates new alert/trade/agent_log
   ↓
2. Supabase detects INSERT event
   ↓
3. Real-time message sent to subscribed clients
   ↓
4. useNotifications hook receives event
   ↓
5. Notification added to state (unreadCount++)
   ↓
6. NotificationBell updates badge counter
   ↓
7. useNotificationToasts shows toast (optional)
   ↓
8. User sees real-time notification
```

## Integration Checklist

- [x] Update types.ts with alerts table definition
- [x] Create use-notifications hook with subscriptions
- [x] Create NotificationBell component
- [x] Integrate NotificationBell into Header
- [x] Create use-notification-toasts hook
- [x] Add NotificationBell export to index
- [ ] **Enable Real-time in Supabase Console**
- [ ] Test with sample alerts
- [ ] Deploy and monitor

## Enabling Real-time in Supabase

**Important:** Before deploying, enable real-time for the alerts table:

1. Go to Supabase Console
2. Navigate to **Database** → **Replication**
3. Find the **alerts** table
4. Toggle **Enable** (if not already enabled)
5. Repeat for **trades** and **agent_logs** tables

Without this step, real-time updates will not work.

## Usage in Dashboard

**In your dashboard layout or page:**

```typescript
'use client'

import { Header } from '@/components/dashboard'
import { useNotificationToasts } from '@/hooks/use-notification-toasts'
import { useAuth } from '@/lib/auth'

export default function DashboardPage() {
  const { user } = useAuth()

  // Initialize toast notifications
  if (user) {
    useNotificationToasts(user.id)
  }

  return (
    <div>
      <Header user={user} profile={profile} />
      {/* Rest of dashboard */}
    </div>
  )
}
```

The NotificationBell is already integrated in the Header component.

## Styling & Customization

### Color Coding by Alert Type

```typescript
range_break / sweep    → Orange (🟠)
touch / retest        → Blue (🔵)
trade                 → Green (🟢)
agent                 → Purple (🟣)
default               → Gray (⚪)
```

Customize in `notification-bell.tsx`:
```typescript
const getAlertColor = (kind: string): string => {
  // Modify color mappings here
}
```

### Toast Message Format

Customize toast messages in `use-notification-toasts.ts`:
```typescript
if (kind === 'trade_opened') {
  toast({
    title: `Trade Opened: ${side} ${symbol}`,
    description: `Entry at ${price}`,
  })
}
```

## Performance Notes

- Initial fetch limited to 50 recent alerts
- Realtime subscriptions are lightweight (channel-based)
- Unread status tracked in memory (no DB writes)
- Badge counter updates instantly
- ScrollArea limits DOM size (only visible items rendered)

## Testing Checklist

```
[ ] Bell icon appears in header
[ ] Badge counter shows correct unread count
[ ] Dropdown opens/closes smoothly
[ ] New alerts appear in real-time
[ ] Mark as read works
[ ] Delete notification works
[ ] Clear all works
[ ] Mark all as read works
[ ] Toast notifications appear for new trades
[ ] Toast notifications appear for new alerts
[ ] Unread counter decreases when marked as read
[ ] Timestamps update (date-fns formatDistanceToNow)
[ ] Empty state shows when no notifications
[ ] Dropdown closes when clicking outside
[ ] Colors match alert types
```

## Common Issues & Solutions

### Notifications not appearing
1. Check RLS policies:
   ```sql
   -- Must allow user to read own alerts
   CREATE POLICY "Users can read own alerts"
     ON alerts FOR SELECT
     USING (auth.uid() = user_id);
   ```

2. Enable real-time in Supabase Console
3. Verify userId is correct

### Toast notifications not showing
1. Ensure `useNotificationToasts` is called
2. Check `Toaster` component in root layout:
   ```typescript
   import { Toaster } from '@/components/ui/toaster'

   export default function RootLayout() {
     return (
       <html>
         <body>
           {children}
           <Toaster />
         </body>
       </html>
     )
   }
   ```

3. Check notification timestamp (must be recent, < 5 seconds)

### Dropdown not opening
1. Check NotificationBell is a client component
2. Verify DropdownMenu dependency is installed
3. Check z-index in CSS

## Future Enhancements

1. **Notification Preferences**
   - Users can toggle specific alert types
   - Filter by symbol

2. **Sound Alerts**
   - Optional sound for critical alerts
   - Separate sounds per alert type

3. **Push Notifications**
   - Web push for desktop alerts
   - Mobile app notifications

4. **Email Digests**
   - Daily/weekly summary emails
   - Customizable digest frequency

5. **External Integration**
   - Slack notifications
   - Discord webhooks
   - Telegram bot

6. **Analytics**
   - Track which notifications users interact with
   - Most clicked alert types
   - Time to response metrics

## Files Summary

| File | Lines | Purpose |
|------|-------|---------|
| use-notifications.ts | 165 | Main hook with Realtime subscriptions |
| notification-bell.tsx | 177 | Dropdown component with UI |
| use-notification-toasts.ts | 68 | Toast notifications hook |
| types.ts | +45 | Added alerts table type |
| header.tsx | ~10 | Integrated NotificationBell |
| dashboard/index.ts | +1 | Exported NotificationBell |

**Total new code: ~416 lines**
**Modified code: ~56 lines**

## Architecture Decision Notes

**Why Real-time over Polling?**
- Supabase Realtime is event-driven (more efficient)
- Instant user feedback
- Scales better with many concurrent users
- Lower bandwidth usage

**Why Multiple Subscriptions?**
- Separate channels for different event types
- Easier to filter and handle different notification kinds
- Better debugging and monitoring

**Why In-Memory Read Status?**
- Avoids database writes for UI state
- Fast mark-as-read UX
- No RLS policy issues
- Lighter performance footprint

**Why Toast + Dropdown?**
- Toast for immediate attention (critical events)
- Dropdown for history/review (non-disruptive)
- Better UX for power users

## Monitoring & Debugging

Monitor real-time subscriptions:
```typescript
// In useNotifications hook
const channel = supabase.channel(`alerts:${userId}`)
  .on('subscribe', () => console.log('Subscribed to alerts'))
  .on('postgres_changes', ..., (payload) => {
    console.log('Alert received:', payload)
  })
  .subscribe()
```

View logs in Supabase Console:
1. Go to **Logs** → **Function Logs** (for Realtime)
2. Filter by table name
3. Check for errors in subscriptions

## Deployment Notes

1. **Supabase Configuration**
   - Enable real-time replication for alerts, trades, agent_logs

2. **Environment Variables**
   - NEXT_PUBLIC_SUPABASE_URL (already set)
   - NEXT_PUBLIC_SUPABASE_ANON_KEY (already set)

3. **RLS Policies** (ensure these exist)
   ```sql
   CREATE POLICY "Users can read own alerts"
     ON alerts FOR SELECT USING (auth.uid() = user_id);

   CREATE POLICY "Service role can insert alerts"
     ON alerts FOR INSERT WITH CHECK (true);
   ```

4. **Test in Production**
   - Send test alert
   - Verify real-time delivery
   - Check browser console for errors

## Support & Documentation

- **Supabase Realtime Docs:** https://supabase.com/docs/guides/realtime
- **shadcn/ui Components:** https://ui.shadcn.com/
- **date-fns Documentation:** https://date-fns.org/
- **Project Docs:** See /apps/web/src/hooks/NOTIFICATIONS_README.md

---

**Implementation completed by:** Claude Code
**Date:** 2025-10-29
**Status:** Ready for testing
