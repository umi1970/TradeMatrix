# Real-time Notifications - Testing Guide

## Overview

This guide explains how to test the real-time notifications system in TradeMatrix.ai.

## Prerequisites

1. ✅ Supabase project set up
2. ✅ Real-time enabled for alerts, trades, agent_logs tables
3. ✅ User authenticated in app
4. ✅ Browser dev tools open

## Test Scenarios

### Scenario 1: Display Notification Bell with Badge

**Test:** Bell icon appears with correct count

```
1. Navigate to dashboard
2. Look for bell icon in header (right side)
3. If notifications exist, see red badge with count
4. Hover over bell to see tooltip
```

**Expected Result:**
- Bell icon visible next to subscription badge
- Badge shows "9+" if 9+ unread notifications
- Badge has pulse animation

### Scenario 2: Open Notification Dropdown

**Test:** Click bell and see dropdown

```
1. Click bell icon
2. Wait for dropdown to open (animation ~300ms)
3. See notification list or empty state
4. Click outside to close
```

**Expected Result:**
- Dropdown opens smoothly
- Shows "Notifications" header with unread count badge
- Shows ScrollArea with max 400px height
- Empty state if no notifications

### Scenario 3: Create New Trading Alert

**Test:** Real-time alert appears in dropdown

```
1. Have dropdown open
2. Using Supabase console, insert test alert:
   INSERT INTO alerts (user_id, symbol_id, kind, context, sent)
   VALUES (
     'current-user-id',
     'symbol-uuid',
     'range_break',
     '{"symbol": "DAX"}'::jsonb,
     false
   );
3. Observe dropdown updates instantly
4. Badge counter increments
5. Toast notification appears (optional)
```

**Expected Result:**
- New notification appears at top of list
- Unread count increments
- Background color is blue (unread style)
- Icon color matches alert type (orange for range_break)
- Timestamp shows "a few seconds ago"
- Toast appears (if useNotificationToasts is active)

### Scenario 4: Mark Single Notification as Read

**Test:** Click check icon to mark read

```
1. Find unread notification (blue background)
2. Hover to show action buttons
3. Click check icon
4. Notification should change style
5. Unread count should decrease
6. Bell badge should update
```

**Expected Result:**
- Notification background changes from blue to gray
- Check icon disappears
- Unread count decrements
- Badge counter updates

### Scenario 5: Mark All as Read

**Test:** Bulk mark operation

```
1. Have 3+ unread notifications
2. Click "Mark all as read" button
3. Verify all change to gray background
4. Check unread count becomes 0
5. Bell badge disappears
```

**Expected Result:**
- All notifications marked read instantly
- Unread count: 0
- Badge counter hidden
- Button becomes disabled

### Scenario 6: Delete Single Notification

**Test:** Remove notification from list

```
1. Find notification in list
2. Hover to show delete button (trash icon)
3. Click delete button
4. Notification removed from list
5. Unread count adjusted if it was unread
```

**Expected Result:**
- Notification removed instantly
- Smooth removal animation
- List shifts up to fill gap
- Unread count decreases if notification was unread

### Scenario 7: Clear All Notifications

**Test:** Remove all notifications

```
1. Have 5+ notifications
2. Click "Clear all" button
3. All notifications removed
4. Empty state appears
5. Badge disappears
```

**Expected Result:**
- All notifications removed
- Empty state message: "No notifications yet"
- Bell icon with bell emoji appears
- "Clear all" button disabled
- "Mark all as read" button disabled

### Scenario 8: Trade Open Notification

**Test:** Notification for new trade

```
1. Create new trade in app
2. Check NotificationBell dropdown or toast
3. Should show trade details
```

**Expected Result:**
- Notification kind: "trade_opened"
- Title: "Trade Opened: [SIDE] [SYMBOL]"
- Description: "Entry at [PRICE]"
- Icon color: green

### Scenario 9: Agent Completion Notification

**Test:** Notification when agent finishes

```
1. Insert completed agent_log record:
   INSERT INTO agent_logs (..., status, agent_type, duration_ms)
   VALUES (..., 'completed', 'chart_watcher', 5234);
2. Check notification appears
```

**Expected Result:**
- Notification kind: "agent_chart_watcher_completed"
- Title: "Chart Watcher Completed"
- Description: "Execution time: 5.2s"
- Icon color: purple

### Scenario 10: Empty State

**Test:** No notifications scenario

```
1. Clear all notifications
2. Close and reopen dropdown
3. Should show empty state
```

**Expected Result:**
- Bell icon (large, centered, faded)
- Text: "No notifications yet"
- "Clear all" button disabled
- "Mark all as read" button disabled

### Scenario 11: Toast Notifications

**Test:** Browser-level toasts appear

```
1. Ensure useNotificationToasts is active
2. Create new alert
3. Check for toast notification
4. Toast disappears after ~5 seconds
```

**Expected Result:**
- Toast appears in bottom-right (or top-right)
- Shows title and description
- Closes automatically
- Multiple toasts stack vertically

### Scenario 12: Real-time Unsubscribe

**Test:** Verify cleanup on unmount

```
1. Open dropdown with notifications
2. Navigate away from dashboard
3. Open browser DevTools Network tab
4. Go back to dashboard
5. Check WebSocket is reconnected
```

**Expected Result:**
- No memory leaks
- Subscriptions clean up properly
- New subscriptions on remount

### Scenario 13: Multiple Simultaneous Notifications

**Test:** Handle rapid alerts

```
1. Use Supabase console to insert 10 alerts rapidly
2. Observe they all appear
3. Scroll through notification list
4. Badge shows correct unread count
```

**Expected Result:**
- All notifications appear
- No duplicates
- Badge count accurate
- ScrollArea works smoothly
- No performance degradation

### Scenario 14: Timestamp Accuracy

**Test:** Verify relative timestamps

```
1. Create alert
2. Check timestamp shows "a few seconds ago"
3. Wait 1 minute
4. Timestamp should update to "a minute ago"
```

**Expected Result:**
- Timestamps use relative format (date-fns)
- Format: "X minutes ago", "X hours ago", etc.
- Updates as time passes

### Scenario 15: Color Coding

**Test:** Verify alert colors

```
Chart the notification kinds and expected colors:

kind                  | Expected Color | Icon
range_break          | Orange         | "Break"
asia_sweep           | Orange         | "Break"
retest_touch         | Blue           | "Retest"
r1_touch            | Blue           | "Touch"
s1_touch            | Blue           | "Touch"
pivot_touch         | Blue           | "Touch"
trade_opened        | Green          | "Trade"
agent_*_completed   | Purple         | "Agent"
```

**Test:**
1. Create different alert types
2. Verify colors match above table

## Automated Testing

### Unit Test Example

```typescript
import { renderHook, waitFor } from '@testing-library/react'
import { useNotifications } from '@/hooks/use-notifications'

describe('useNotifications', () => {
  it('should fetch initial notifications', async () => {
    const { result } = renderHook(() => useNotifications('user-123'))

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(result.current.notifications).toBeInstanceOf(Array)
  })

  it('should mark notification as read', () => {
    const { result } = renderHook(() => useNotifications('user-123'))

    const notification = result.current.notifications[0]
    result.current.markAsRead(notification.id)

    expect(notification.read).toBe(true)
    expect(result.current.unreadCount).toBe(
      result.current.notifications.filter(n => !n.read).length
    )
  })
})
```

### Component Test Example

```typescript
import { render, screen, fireEvent } from '@testing-library/react'
import { NotificationBell } from '@/components/dashboard/notification-bell'

describe('NotificationBell', () => {
  it('should render bell icon', () => {
    render(<NotificationBell userId="user-123" />)
    expect(screen.getByRole('button')).toBeInTheDocument()
  })

  it('should show unread badge', () => {
    render(<NotificationBell userId="user-123" />)
    const badge = screen.getByText(/\d+/)
    expect(badge).toBeInTheDocument()
  })

  it('should open dropdown on click', async () => {
    render(<NotificationBell userId="user-123" />)
    const button = screen.getByRole('button')
    fireEvent.click(button)

    const content = await screen.findByText('Notifications')
    expect(content).toBeInTheDocument()
  })
})
```

## Performance Testing

### Monitor WebSocket Usage

1. Open DevTools → Network tab
2. Filter by WebSocket
3. Create alert
4. Should see message in real-time
5. Check payload size (typically < 1KB per message)

### Memory Leak Detection

1. Open DevTools → Memory tab
2. Take heap snapshot
3. Create/delete notifications 100 times
4. Take another snapshot
5. Compare - should not grow significantly

### Load Testing

```
Insert 1000 alerts via Supabase SQL:
INSERT INTO alerts (user_id, symbol_id, kind, context)
SELECT
  'user-123'::uuid,
  ms.id,
  CASE (random() * 5)::int
    WHEN 0 THEN 'range_break'
    WHEN 1 THEN 'retest_touch'
    WHEN 2 THEN 'asia_sweep'
    WHEN 3 THEN 'pivot_touch'
    ELSE 'r1_touch'
  END,
  jsonb_build_object('symbol', ms.symbol)
FROM market_symbols ms,
     generate_series(1, 1000)
ON CONFLICT DO NOTHING;
```

Then observe:
- Load time of notification list
- Scroll performance
- Badge update speed
- Memory usage

## Browser Compatibility

| Browser | Version | Status |
|---------|---------|--------|
| Chrome  | Latest  | ✅ Full support |
| Firefox | Latest  | ✅ Full support |
| Safari  | Latest  | ✅ Full support |
| Edge    | Latest  | ✅ Full support |
| Mobile Safari | Latest | ✅ Full support |
| Android Chrome | Latest | ✅ Full support |

## Debugging Checklist

- [ ] Check browser console for errors
- [ ] Verify Supabase keys in .env
- [ ] Enable DevTools Network tab to see WebSocket messages
- [ ] Check Supabase Function Logs
- [ ] Verify user ID is correct
- [ ] Confirm real-time enabled for tables
- [ ] Check RLS policies
- [ ] Verify data is in database

## Common Issues During Testing

### Issue: No notifications appear

**Checklist:**
1. Is real-time enabled in Supabase?
2. Is WebSocket open in Network tab?
3. Is the user ID correct?
4. Are there any RLS policy errors in Supabase logs?
5. Has data been inserted with correct user_id?

### Issue: Notifications appear but don't update in real-time

**Checklist:**
1. Is browser WebSocket connection active?
2. Are you subscribed to the correct user_id?
3. Check Network tab for WebSocket messages
4. Try refreshing the page

### Issue: Toast doesn't appear

**Checklist:**
1. Is useNotificationToasts called?
2. Is Toaster component in root layout?
3. Is notification timestamp recent (< 5 seconds)?
4. Check browser console for errors

### Issue: Dropdown doesn't open

**Checklist:**
1. Is NotificationBell in a client component?
2. Are DropdownMenu components imported?
3. Check z-index conflicts
4. Try refreshing the page

## Test Report Template

```
Date: ___________
Tester: _________
Build Version: __________

Test Results:
[ ] Scenario 1: Display Notification Bell
[ ] Scenario 2: Open Dropdown
[ ] Scenario 3: Create Alert (Real-time)
[ ] Scenario 4: Mark as Read
[ ] Scenario 5: Mark All as Read
[ ] Scenario 6: Delete Single
[ ] Scenario 7: Clear All
[ ] Scenario 8: Trade Notification
[ ] Scenario 9: Agent Notification
[ ] Scenario 10: Empty State
[ ] Scenario 11: Toast Notifications
[ ] Scenario 12: Unsubscribe on Unmount
[ ] Scenario 13: Multiple Simultaneous
[ ] Scenario 14: Timestamp Accuracy
[ ] Scenario 15: Color Coding

Issues Found:
1. _________________________
2. _________________________
3. _________________________

Performance Notes:
- Load time: ________ms
- Memory: _______MB
- CPU: ______%

Overall Status: [ ] Pass [ ] Fail [ ] Partial

Signature: ________________
```

## Deployment Testing

After deploying to production:

```
1. [ ] Test real-time in production Supabase
2. [ ] Monitor WebSocket connections
3. [ ] Check latency of alerts
4. [ ] Verify no regressions in other features
5. [ ] Monitor error logs
6. [ ] Load test with concurrent users
7. [ ] Test on multiple browsers
8. [ ] Test on mobile devices
9. [ ] Monitor server performance
10. [ ] Get user feedback
```

## Quick Test Command

```bash
# Navigate to Supabase console and run:
INSERT INTO alerts (user_id, kind, context, sent)
VALUES (
  'YOUR_USER_ID'::uuid,
  'range_break',
  '{"symbol": "DAX", "level": 18000}'::jsonb,
  false
);

# Should see notification appear in your app within 1-2 seconds
```

---

**Last Updated:** 2025-10-29
**Status:** Ready for testing
