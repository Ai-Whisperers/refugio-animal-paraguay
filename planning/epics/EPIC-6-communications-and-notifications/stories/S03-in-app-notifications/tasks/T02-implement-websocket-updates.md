---
task: T02
story: S03
epic: EPIC-6
title: Implement WebSocket updates
status: ready
priority: medium
created: 2026-03-25T17:13:26.733223
---

# T02: Implement WebSocket updates

## Description

Add Supabase Realtime subscriptions to the in-app notification bell so new notifications appear instantly without page refresh. When a Server Action inserts a row into `notification_inbox`, the client receives a Postgres CDC event and updates the badge count and dropdown list in real time.

This task extends the `NotificationBell` component built in T01 to hold local state seeded from SSR props, then kept live via a `postgres_changes` subscription. No separate WebSocket server, no polling.

## Acceptance Criteria

- [ ] New `notification_inbox` INSERT events reach the client within 1–2 seconds
- [ ] Badge count increments immediately when a new notification arrives
- [ ] Dropdown list prepends the new notification without requiring a page reload
- [ ] Subscription is scoped to `user_id = current user` — users cannot receive each other's notifications
- [ ] Realtime channel is removed on component unmount (no memory leaks)
- [ ] SSR-fetched initial state (unread count + recent list) is preserved on first render
- [ ] Supabase Realtime publication includes `notification_inbox`
- [ ] Unit tests cover the state update logic triggered by a mock Realtime payload

## Implementation Notes

### Prerequisites

T01 must be complete. The `notification_inbox` table, RLS policies, and `NotificationBell` component must exist before adding Realtime.

---

### Step 1 — Enable Realtime publication for `notification_inbox`

Realtime CDC requires the table to be added to the `supabase_realtime` publication. Add this to the **same migration file** as T01 (`20260401000019_notification_inbox.sql`) or create a follow-on migration.

**Option A (amend T01 migration — preferred if not yet deployed):**

Append to `supabase/migrations/20260401000019_notification_inbox.sql`:

```sql
-- Enable Realtime for in-app notifications
-- Supabase Realtime uses logical replication via the supabase_realtime publication.
-- Without this, postgres_changes events are never emitted for this table.
alter publication supabase_realtime add table public.notification_inbox;
```

**Option B (new migration — if T01 is already deployed):**

`supabase/migrations/20260401000020_notification_inbox_realtime.sql`:

```sql
-- Enable Realtime CDC for notification_inbox
alter publication supabase_realtime add table public.notification_inbox;
```

> **Important**: Supabase Realtime only emits `postgres_changes` events for tables in the `supabase_realtime` publication. This step is required even though RLS is already set up.

---

### Step 2 — Browser Supabase client utility

Realtime subscriptions run in the browser. Use the `@supabase/ssr` browser client, not the server client.

`src/lib/supabase/browser.ts`:

```typescript
import { createBrowserClient } from '@supabase/ssr'
import type { Database } from '@/lib/supabase/database.types'

// Singleton pattern — calling createBrowserClient multiple times in the same
// browser context is safe (it returns cached client), but a module-level
// singleton avoids any ambiguity.
let browserClient: ReturnType<typeof createBrowserClient<Database>> | null = null

export function getSupabaseBrowserClient() {
  if (!browserClient) {
    browserClient = createBrowserClient<Database>(
      process.env.NEXT_PUBLIC_SUPABASE_URL!,
      process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
    )
  }
  return browserClient
}
```

Both env vars are public (safe to expose to browser). They are already required by Next.js Auth Helpers.

---

### Step 3 — Realtime payload type

`src/lib/notifications/realtime.ts`:

```typescript
import type { InboxNotification, NotificationType } from './inbox'

// Shape of the `new` record in a Supabase postgres_changes INSERT payload.
// Column names are snake_case (database), not camelCase (application interface).
export interface NotificationInboxInsertPayload {
  id: string
  user_id: string
  title: string
  message: string
  type: NotificationType
  link: string | null
  read_at: string | null
  created_at: string
}

/** Convert the raw Realtime INSERT payload to the application InboxNotification shape. */
export function mapPayloadToNotification(
  payload: NotificationInboxInsertPayload
): InboxNotification {
  return {
    id: payload.id,
    userId: payload.user_id,
    title: payload.title,
    message: payload.message,
    type: payload.type,
    link: payload.link,
    readAt: payload.read_at,
    createdAt: payload.created_at,
  }
}
```

---

### Step 4 — Custom hook: `useNotificationRealtime`

Extract the subscription logic into a dedicated hook so `NotificationBell` stays focused on rendering.

`src/hooks/useNotificationRealtime.ts`:

```typescript
'use client'

import { useEffect, useCallback } from 'react'
import type { RealtimeChannel } from '@supabase/supabase-js'
import { getSupabaseBrowserClient } from '@/lib/supabase/browser'
import {
  mapPayloadToNotification,
  type NotificationInboxInsertPayload,
} from '@/lib/notifications/realtime'
import type { InboxNotification } from '@/lib/notifications/inbox'

interface UseNotificationRealtimeOptions {
  userId: string
  onNewNotification: (notification: InboxNotification) => void
}

/**
 * Subscribe to Supabase Realtime INSERT events on `notification_inbox`
 * for the given user. Calls `onNewNotification` for each incoming row.
 *
 * The subscription is filtered server-side: `user_id=eq.{userId}`.
 * RLS on the table provides a second layer of security — the anon key
 * cannot read other users' rows even if the filter were bypassed.
 *
 * Cleans up the channel on unmount.
 */
export function useNotificationRealtime({
  userId,
  onNewNotification,
}: UseNotificationRealtimeOptions): void {
  const handlePayload = useCallback(
    (payload: { new: NotificationInboxInsertPayload }) => {
      const notification = mapPayloadToNotification(payload.new)
      onNewNotification(notification)
    },
    [onNewNotification]
  )

  useEffect(() => {
    const supabase = getSupabaseBrowserClient()

    const channel: RealtimeChannel = supabase
      .channel(`notification_inbox:${userId}`)
      .on(
        'postgres_changes',
        {
          event: 'INSERT',
          schema: 'public',
          table: 'notification_inbox',
          // Server-side filter — only events for this user are sent to the client.
          // Supabase Realtime supports eq filters on any column.
          filter: `user_id=eq.${userId}`,
        },
        handlePayload
      )
      .subscribe()

    return () => {
      // Remove channel on unmount to prevent memory leaks and duplicate subscriptions
      // when the component re-mounts (e.g. during Next.js hot reload in dev).
      supabase.removeChannel(channel)
    }
  }, [userId, handlePayload])
}
```

---

### Step 5 — Update `NotificationBell` to hold reactive state

T01's `NotificationBell` received props and rendered them statically. For Realtime, it must hold local state initialized from SSR props, then updated when the hook fires.

Replace `src/components/notifications/NotificationBell.tsx` (written in T01) with the updated version below. The rendering logic is identical — only state management changes.

```typescript
'use client'

import { useState, useCallback } from 'react'
import { BellIcon } from '@heroicons/react/24/outline'
import { BellAlertIcon } from '@heroicons/react/24/solid'
import { NotificationDropdown } from './NotificationDropdown'
import { useNotificationRealtime } from '@/hooks/useNotificationRealtime'
import type { InboxNotification } from '@/lib/notifications/inbox'

// Maximum recent notifications shown in dropdown.
const MAX_DROPDOWN_NOTIFICATIONS = 10

// Threshold above which badge displays "9+" instead of the actual count.
const BADGE_MAX_DISPLAY = 9

interface NotificationBellProps {
  /** Initial unread count from SSR — used to seed local state. */
  unreadCount: number
  /** Initial recent notifications from SSR — used to seed local state. */
  notifications: InboxNotification[]
  userId: string
}

export function NotificationBell({
  unreadCount,
  notifications,
  userId,
}: NotificationBellProps) {
  // Seed local state from SSR-fetched props.
  // After mount, Realtime events update these without a page refresh.
  const [localCount, setLocalCount] = useState(unreadCount)
  const [localNotifications, setLocalNotifications] = useState<InboxNotification[]>(notifications)
  const [isOpen, setIsOpen] = useState(false)

  const handleNewNotification = useCallback((notification: InboxNotification) => {
    setLocalCount((prev) => prev + 1)
    setLocalNotifications((prev) => {
      // Prepend new notification and trim to max dropdown size.
      const updated = [notification, ...prev]
      return updated.slice(0, MAX_DROPDOWN_NOTIFICATIONS)
    })
  }, [])

  // Subscribe to Realtime INSERT events for this user.
  useNotificationRealtime({ userId, onNewNotification: handleNewNotification })

  const badgeLabel =
    localCount > BADGE_MAX_DISPLAY ? `${BADGE_MAX_DISPLAY}+` : String(localCount)

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setIsOpen((prev) => !prev)}
        aria-label={
          localCount > 0
            ? `${localCount} notificaciones sin leer`
            : 'Sin notificaciones nuevas'
        }
        className="relative p-2 rounded-full text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)] focus:outline-none focus:ring-2 focus:ring-[var(--ring-color)] transition-colors"
      >
        {localCount > 0 ? (
          <BellAlertIcon className="h-6 w-6" aria-hidden="true" />
        ) : (
          <BellIcon className="h-6 w-6" aria-hidden="true" />
        )}

        {localCount > 0 && (
          <span
            aria-hidden="true"
            className="absolute top-1 right-1 flex h-4 w-4 items-center justify-center rounded-full bg-[var(--color-danger)] text-white text-[10px] font-bold leading-none"
          >
            {badgeLabel}
          </span>
        )}
      </button>

      {isOpen && (
        <NotificationDropdown
          notifications={localNotifications}
          userId={userId}
          onClose={() => setIsOpen(false)}
          onMarkRead={(id) => {
            // Remove from unread count and update readAt in local state.
            setLocalNotifications((prev) =>
              prev.map((n) =>
                n.id === id ? { ...n, readAt: new Date().toISOString() } : n
              )
            )
            setLocalCount((prev) => Math.max(0, prev - 1))
          }}
          onMarkAllRead={() => {
            setLocalNotifications((prev) =>
              prev.map((n) => ({ ...n, readAt: n.readAt ?? new Date().toISOString() }))
            )
            setLocalCount(0)
          }}
        />
      )}
    </div>
  )
}
```

> **Note on `NotificationDropdown` callback props**: The `onMarkRead` and `onMarkAllRead` callbacks allow `NotificationBell` to keep local state in sync when the user marks items read via the dropdown. `NotificationDropdown` calls these after its Server Action resolves. Add these props to `NotificationDropdown` if not already present from T01.

---

### Step 6 — `NotificationDropdown` callback wiring

Update `src/components/notifications/NotificationDropdown.tsx` to accept and call the new callbacks:

```typescript
// Add to the NotificationDropdownProps interface:
interface NotificationDropdownProps {
  notifications: InboxNotification[]
  userId: string
  onClose: () => void
  onMarkRead: (id: string) => void      // called after successful mark-as-read
  onMarkAllRead: () => void              // called after successful mark-all-read
}
```

In the existing `markRead` handler inside the component, after the Server Action resolves:

```typescript
// After: await markNotificationRead(notification.id)
onMarkRead(notification.id)

// After: await markAllNotificationsRead(userId)
onMarkAllRead()
```

This keeps the badge count in the parent `NotificationBell` accurate without waiting for a `revalidatePath` re-render cycle. Both mechanisms run: Realtime keeps the list live for inserts, and the callbacks keep the count accurate for mark-as-read operations.

---

### Step 7 — Optional browser notification (tab-focused)

If the user has granted notification permission and the tab is in the background, show a native browser notification. This is optional — implement only if the product requirements call for it.

```typescript
// Inside useNotificationRealtime handlePayload, after calling onNewNotification:

if (
  typeof window !== 'undefined' &&
  'Notification' in window &&
  Notification.permission === 'granted' &&
  document.visibilityState === 'hidden'
) {
  new Notification(payload.new.title, {
    body: payload.new.message,
    icon: '/icons/notification-icon.png',
  })
}
```

Do **not** request notification permission automatically — only after explicit user consent via a settings toggle (EPIC-6/S04/T01).

---

### Step 8 — Environment variables

No new variables needed. Realtime uses the existing public Supabase URL and anon key:

```
NEXT_PUBLIC_SUPABASE_URL=https://xxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...
```

Both are already required for `@supabase/ssr` browser client.

---

### Step 9 — Unit tests

`src/hooks/__tests__/useNotificationRealtime.test.ts`:

```typescript
import { renderHook, act } from '@testing-library/react'
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest'

// Mock the browser Supabase client
vi.mock('@/lib/supabase/browser', () => ({
  getSupabaseBrowserClient: vi.fn(),
}))

import { getSupabaseBrowserClient } from '@/lib/supabase/browser'
import { useNotificationRealtime } from '../useNotificationRealtime'

// Mock Supabase channel fluent API
const mockSubscribe = vi.fn().mockReturnThis()
const mockOn = vi.fn().mockReturnThis()
const mockRemoveChannel = vi.fn()
const mockChannel = vi.fn().mockReturnValue({ on: mockOn, subscribe: mockSubscribe })

let capturedHandler: ((payload: { new: object }) => void) | null = null

beforeEach(() => {
  vi.clearAllMocks()
  capturedHandler = null

  mockOn.mockImplementation((_event, _filter, handler) => {
    capturedHandler = handler
    return { subscribe: mockSubscribe }
  })

  vi.mocked(getSupabaseBrowserClient).mockReturnValue({
    channel: mockChannel,
    removeChannel: mockRemoveChannel,
  } as unknown as ReturnType<typeof getSupabaseBrowserClient>)
})

const samplePayload = {
  new: {
    id: 'notif-uuid',
    user_id: 'user-uuid',
    title: 'Solicitud aprobada',
    message: 'Tu solicitud fue aprobada.',
    type: 'success' as const,
    link: '/adopciones/123',
    read_at: null,
    created_at: '2026-04-01T10:00:00Z',
  },
}

describe('useNotificationRealtime', () => {
  it('subscribes to postgres_changes INSERT on notification_inbox for the user', () => {
    renderHook(() =>
      useNotificationRealtime({ userId: 'user-uuid', onNewNotification: vi.fn() })
    )

    expect(mockChannel).toHaveBeenCalledWith('notification_inbox:user-uuid')
    expect(mockOn).toHaveBeenCalledWith(
      'postgres_changes',
      expect.objectContaining({
        event: 'INSERT',
        table: 'notification_inbox',
        filter: 'user_id=eq.user-uuid',
      }),
      expect.any(Function)
    )
    expect(mockSubscribe).toHaveBeenCalled()
  })

  it('calls onNewNotification with mapped InboxNotification on INSERT event', () => {
    const onNewNotification = vi.fn()

    renderHook(() =>
      useNotificationRealtime({ userId: 'user-uuid', onNewNotification })
    )

    act(() => {
      capturedHandler!(samplePayload)
    })

    expect(onNewNotification).toHaveBeenCalledWith({
      id: 'notif-uuid',
      userId: 'user-uuid',
      title: 'Solicitud aprobada',
      message: 'Tu solicitud fue aprobada.',
      type: 'success',
      link: '/adopciones/123',
      readAt: null,
      createdAt: '2026-04-01T10:00:00Z',
    })
  })

  it('removes the channel on unmount', () => {
    const { unmount } = renderHook(() =>
      useNotificationRealtime({ userId: 'user-uuid', onNewNotification: vi.fn() })
    )

    unmount()

    expect(mockRemoveChannel).toHaveBeenCalled()
  })

  it('maps null link and null read_at from payload', () => {
    const onNewNotification = vi.fn()

    renderHook(() =>
      useNotificationRealtime({ userId: 'user-uuid', onNewNotification })
    )

    act(() => {
      capturedHandler!({
        new: { ...samplePayload.new, link: null, read_at: null },
      })
    })

    expect(onNewNotification).toHaveBeenCalledWith(
      expect.objectContaining({ link: null, readAt: null })
    )
  })

  it('creates a channel scoped per userId', () => {
    renderHook(() =>
      useNotificationRealtime({ userId: 'alice-uuid', onNewNotification: vi.fn() })
    )
    renderHook(() =>
      useNotificationRealtime({ userId: 'bob-uuid', onNewNotification: vi.fn() })
    )

    expect(mockChannel).toHaveBeenCalledWith('notification_inbox:alice-uuid')
    expect(mockChannel).toHaveBeenCalledWith('notification_inbox:bob-uuid')
  })
})
```

`src/components/notifications/__tests__/NotificationBell.realtime.test.tsx`:

```typescript
import { render, screen, act } from '@testing-library/react'
import { vi, describe, it, expect, beforeEach } from 'vitest'
import type { InboxNotification } from '@/lib/notifications/inbox'

// Mock the realtime hook — isolate component rendering from subscription side effects
const mockUseNotificationRealtime = vi.fn()
vi.mock('@/hooks/useNotificationRealtime', () => ({
  useNotificationRealtime: (opts: { onNewNotification: (n: InboxNotification) => void }) => {
    mockUseNotificationRealtime(opts)
  },
}))

// Mock NotificationDropdown to avoid deep rendering
vi.mock('../NotificationDropdown', () => ({
  NotificationDropdown: () => <div data-testid="dropdown" />,
}))

import { NotificationBell } from '../NotificationBell'

const baseNotification: InboxNotification = {
  id: 'n1',
  userId: 'u1',
  title: 'Adopción aprobada',
  message: 'Tu mascota te espera.',
  type: 'success',
  link: null,
  readAt: null,
  createdAt: '2026-04-01T10:00:00Z',
}

describe('NotificationBell realtime integration', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders initial unread count from SSR props', () => {
    render(
      <NotificationBell unreadCount={3} notifications={[baseNotification]} userId="u1" />
    )

    expect(screen.getByText('3')).toBeInTheDocument()
  })

  it('increments badge when realtime delivers a new notification', () => {
    render(
      <NotificationBell unreadCount={2} notifications={[]} userId="u1" />
    )

    // Grab the callback registered with the hook
    const { onNewNotification } = mockUseNotificationRealtime.mock.calls[0][0]

    act(() => {
      onNewNotification(baseNotification)
    })

    // Count should be 2 + 1 = 3
    expect(screen.getByText('3')).toBeInTheDocument()
  })

  it('displays 9+ when count exceeds 9', () => {
    render(
      <NotificationBell unreadCount={9} notifications={[]} userId="u1" />
    )

    const { onNewNotification } = mockUseNotificationRealtime.mock.calls[0][0]

    act(() => {
      onNewNotification(baseNotification)
    })

    expect(screen.getByText('9+')).toBeInTheDocument()
  })
})
```

---

### CSS variables required

No new CSS variables beyond T01. Realtime updates use the same `--bg-unread`, `--color-danger`, and `--ring-color` tokens already defined.

---

### Files changed

| File | Action | Description |
|------|--------|-------------|
| `supabase/migrations/20260401000019_notification_inbox.sql` | Amend (or new `000020`) | Add `alter publication supabase_realtime add table` |
| `src/lib/supabase/browser.ts` | Create | Singleton browser Supabase client |
| `src/lib/notifications/realtime.ts` | Create | Payload type + snake_case → camelCase mapper |
| `src/hooks/useNotificationRealtime.ts` | Create | Realtime subscription hook |
| `src/components/notifications/NotificationBell.tsx` | Update | Add `useState` seeded from SSR props + hook call |
| `src/components/notifications/NotificationDropdown.tsx` | Update | Add `onMarkRead` / `onMarkAllRead` callback props |
| `src/hooks/__tests__/useNotificationRealtime.test.ts` | Create | 5 unit tests for hook |
| `src/components/notifications/__tests__/NotificationBell.realtime.test.tsx` | Create | 3 unit tests for badge state |

---

### Integration with T01

`NotificationBell` in T01 renders static props. This task converts it to use local state. The layout Server Component in T01 (which calls `getUnreadCount()` and `getRecentNotifications()`) is unchanged — it continues to provide the initial SSR-rendered state. After hydration, Realtime takes over for new events.

**Flow summary:**

```
Page load
  └── Server Component fetches unreadCount + notifications (SSR)
  └── NotificationBell renders with SSR data (no flicker)
  └── After hydration: useNotificationRealtime subscribes via WebSocket
         └── New INSERT on notification_inbox triggers handlePayload
         └── badge count increments, dropdown prepends new item
         └── No page reload required
```

---

### Supabase Realtime limitations to be aware of

- Realtime requires the Supabase project to be on a plan that supports it (free tier includes it)
- `postgres_changes` filters (like `user_id=eq.X`) require the table to have RLS enabled — it does
- The channel name must be unique per subscription; using `notification_inbox:${userId}` achieves this even if the user has multiple tabs open (each creates a separate channel, which is fine)
- If the browser goes offline and reconnects, Supabase Realtime automatically re-subscribes; events during the offline window are **not** replayed — the badge count will be out of date until the next page load or manual refresh. This is acceptable behavior for this use case.

## Related Issues

- EPIC-6
- S03
- T01 (prerequisite — `notification_inbox` table and `NotificationBell` base component)
