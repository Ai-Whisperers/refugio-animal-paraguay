---
task: T01
story: S03
epic: EPIC-6
title: Build notification UI
status: ready
priority: medium
created: 2026-03-25T17:13:26.733166
---

# T01: Build notification UI

## Description

Build an in-app notification system with a bell icon component, unread badge, and dropdown
list showing recent notifications. In-app notifications are distinct from the outbound
`notification_queue` (email/WhatsApp): they appear inside the web application for logged-in
users (staff, volunteers, adopters) and persist until read.

**Architecture decision**: A separate `notification_inbox` table stores in-app notifications.
The `notification_queue` (EPIC-6/S01/T03) handles outbound sends — it does NOT feed the
in-app inbox directly. Instead, Server Actions that trigger events (adoption approved,
shift assigned, donation processed) insert rows into both tables as needed.

**Component model**:
- `NotificationBell` — `'use client'` wrapper that owns open/close state
- `NotificationDropdown` — dropdown panel rendered inside `NotificationBell`
- Badge count fetched server-side and passed as a prop (avoids client fetch on mount)
- Mark-as-read via Server Action (`markNotificationRead`, `markAllNotificationsRead`)

---

## Acceptance Criteria

- [ ] `notification_inbox` table migration (`000019`) created
- [ ] `src/lib/notifications/inbox.ts` with `getUnreadCount()`, `getRecentNotifications()`, `createInboxNotification()`
- [ ] `src/components/notifications/NotificationBell.tsx` — `'use client'` bell + badge
- [ ] `src/components/notifications/NotificationDropdown.tsx` — dropdown list
- [ ] `src/app/actions/notifications.ts` — `markNotificationRead()`, `markAllNotificationsRead()` Server Actions
- [ ] Bell integrates into admin layout header (example in implementation notes)
- [ ] 6 vitest unit tests for `inbox.ts` helpers

---

## Implementation Notes

### 1. Database migration — `supabase/migrations/20260401000019_notification_inbox.sql`

```sql
create type public.notification_type as enum (
  'info', 'success', 'warning', 'error'
);

create table public.notification_inbox (
  id          uuid                        primary key default gen_random_uuid(),
  user_id     uuid                        not null references auth.users(id) on delete cascade,
  title       text                        not null,
  message     text                        not null,
  type        public.notification_type    not null default 'info',
  link        text,                        -- optional href to navigate to when clicked
  read_at     timestamptz,                 -- null = unread
  created_at  timestamptz                 not null default now()
);

-- Index for fast unread count per user
create index notification_inbox_user_unread_idx
  on public.notification_inbox (user_id, created_at desc)
  where read_at is null;

-- RLS: users can only see their own notifications
alter table public.notification_inbox enable row level security;

create policy "Users can view own inbox"
  on public.notification_inbox for select
  using (auth.uid() = user_id);

create policy "Users can update own inbox (mark as read)"
  on public.notification_inbox for update
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

-- Service role can insert inbox notifications (from Server Actions using supabaseAdmin)
-- RLS insert is intentionally skipped for service role — INSERT is admin-only
```

### 2. Inbox library — `src/lib/notifications/inbox.ts`

```typescript
import { createClient } from '@supabase/supabase-js';
import { createServerClient } from '@supabase/ssr';
import { cookies } from 'next/headers';

// Service role client for admin writes (Server Actions)
const supabaseAdmin = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
);

export type NotificationType = 'info' | 'success' | 'warning' | 'error';

export interface InboxNotification {
  id: string;
  userId: string;
  title: string;
  message: string;
  type: NotificationType;
  link: string | null;
  readAt: string | null;
  createdAt: string;
}

export interface CreateInboxNotificationOptions {
  userId: string;
  title: string;
  message: string;
  type?: NotificationType;
  link?: string;
}

/**
 * Insert a new in-app notification for a user.
 * Called from Server Actions using the service role client.
 */
export async function createInboxNotification(
  options: CreateInboxNotificationOptions
): Promise<{ id?: string; error?: string }> {
  const { data, error } = await supabaseAdmin
    .from('notification_inbox')
    .insert({
      user_id: options.userId,
      title: options.title,
      message: options.message,
      type: options.type ?? 'info',
      link: options.link ?? null,
    })
    .select('id')
    .single();

  if (error) return { error: error.message };
  return { id: data.id };
}

/**
 * Get the count of unread notifications for a user.
 * Uses the user's session client so RLS is enforced.
 */
export async function getUnreadCount(userId: string): Promise<number> {
  const cookieStore = cookies();
  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    { cookies: { getAll: () => cookieStore.getAll() } }
  );

  const { count, error } = await supabase
    .from('notification_inbox')
    .select('id', { count: 'exact', head: true })
    .eq('user_id', userId)
    .is('read_at', null);

  if (error) return 0;
  return count ?? 0;
}

/**
 * Fetch the most recent notifications for a user (read + unread).
 * Used to populate the dropdown list.
 */
export async function getRecentNotifications(
  userId: string,
  limit = 10
): Promise<InboxNotification[]> {
  const cookieStore = cookies();
  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    { cookies: { getAll: () => cookieStore.getAll() } }
  );

  const { data, error } = await supabase
    .from('notification_inbox')
    .select('id, user_id, title, message, type, link, read_at, created_at')
    .eq('user_id', userId)
    .order('created_at', { ascending: false })
    .limit(limit);

  if (error || !data) return [];

  return data.map((row) => ({
    id: row.id,
    userId: row.user_id,
    title: row.title,
    message: row.message,
    type: row.type as NotificationType,
    link: row.link,
    readAt: row.read_at,
    createdAt: row.created_at,
  }));
}
```

### 3. Server Actions — `src/app/actions/notifications.ts`

```typescript
'use server';

import { revalidatePath } from 'next/cache';
import { createClient } from '@supabase/supabase-js';
import { cookies } from 'next/headers';
import { createServerClient } from '@supabase/ssr';

/**
 * Mark a single notification as read.
 * Uses the user's session — only the owning user can mark their notifications.
 */
export async function markNotificationRead(notificationId: string): Promise<void> {
  const cookieStore = cookies();
  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll: () => cookieStore.getAll(),
        setAll: (cookiesToSet) => {
          cookiesToSet.forEach(({ name, value, options }) =>
            cookieStore.set(name, value, options)
          );
        },
      },
    }
  );

  await supabase
    .from('notification_inbox')
    .update({ read_at: new Date().toISOString() })
    .eq('id', notificationId)
    .is('read_at', null); // no-op if already read

  revalidatePath('/', 'layout'); // refresh header badge count
}

/**
 * Mark all unread notifications as read for the current user.
 */
export async function markAllNotificationsRead(userId: string): Promise<void> {
  const cookieStore = cookies();
  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll: () => cookieStore.getAll(),
        setAll: (cookiesToSet) => {
          cookiesToSet.forEach(({ name, value, options }) =>
            cookieStore.set(name, value, options)
          );
        },
      },
    }
  );

  await supabase
    .from('notification_inbox')
    .update({ read_at: new Date().toISOString() })
    .eq('user_id', userId)
    .is('read_at', null);

  revalidatePath('/', 'layout');
}
```

### 4. NotificationBell component — `src/components/notifications/NotificationBell.tsx`

```typescript
'use client';

import { useState, useRef, useEffect } from 'react';
import { BellIcon } from '@heroicons/react/24/outline';
import NotificationDropdown from './NotificationDropdown';
import type { InboxNotification } from '@/lib/notifications/inbox';

interface NotificationBellProps {
  /** Pre-fetched unread count (from Server Component parent) */
  unreadCount: number;
  /** Pre-fetched recent notifications (from Server Component parent) */
  notifications: InboxNotification[];
  userId: string;
}

export default function NotificationBell({
  unreadCount,
  notifications,
  userId,
}: NotificationBellProps) {
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        containerRef.current &&
        !containerRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div ref={containerRef} className="relative">
      <button
        type="button"
        aria-label={`Notificaciones${unreadCount > 0 ? ` (${unreadCount} sin leer)` : ''}`}
        aria-expanded={isOpen}
        aria-haspopup="true"
        onClick={() => setIsOpen((prev) => !prev)}
        className="relative rounded-full p-2 text-[var(--text-muted)] hover:bg-[var(--bg-hover)] hover:text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--ring-color)] transition-colors"
      >
        <BellIcon className="h-6 w-6" aria-hidden="true" />

        {unreadCount > 0 && (
          <span
            aria-hidden="true"
            className="absolute right-1 top-1 flex h-4 w-4 items-center justify-center rounded-full bg-[var(--color-danger)] text-[10px] font-bold text-white"
          >
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      {isOpen && (
        <NotificationDropdown
          notifications={notifications}
          userId={userId}
          onClose={() => setIsOpen(false)}
        />
      )}
    </div>
  );
}
```

### 5. NotificationDropdown component — `src/components/notifications/NotificationDropdown.tsx`

```typescript
'use client';

import { useTransition } from 'react';
import Link from 'next/link';
import { formatDistanceToNow } from 'date-fns';
import { es } from 'date-fns/locale';
import type { InboxNotification } from '@/lib/notifications/inbox';
import {
  markNotificationRead,
  markAllNotificationsRead,
} from '@/app/actions/notifications';

// Type-to-color mapping using CSS vars for theme support
const TYPE_ACCENT: Record<string, string> = {
  info:    'bg-[var(--color-info)]',
  success: 'bg-[var(--color-success)]',
  warning: 'bg-[var(--color-warning)]',
  error:   'bg-[var(--color-danger)]',
};

interface NotificationDropdownProps {
  notifications: InboxNotification[];
  userId: string;
  onClose: () => void;
}

export default function NotificationDropdown({
  notifications,
  userId,
  onClose,
}: NotificationDropdownProps) {
  const [isPending, startTransition] = useTransition();

  function handleMarkRead(id: string) {
    startTransition(() => markNotificationRead(id));
  }

  function handleMarkAll() {
    startTransition(() => markAllNotificationsRead(userId));
    onClose();
  }

  const unreadNotifications = notifications.filter((n) => !n.readAt);

  return (
    <div
      role="dialog"
      aria-label="Panel de notificaciones"
      className="absolute right-0 z-50 mt-2 w-80 overflow-hidden rounded-xl border border-[var(--border-color)] bg-[var(--bg-card)] shadow-lg sm:w-96"
    >
      {/* Header */}
      <div className="flex items-center justify-between border-b border-[var(--border-color)] px-4 py-3">
        <h2 className="text-sm font-semibold text-[var(--text-primary)]">
          Notificaciones
        </h2>
        {unreadNotifications.length > 0 && (
          <button
            type="button"
            onClick={handleMarkAll}
            disabled={isPending}
            className="text-xs text-[var(--color-link)] hover:underline disabled:opacity-50"
          >
            Marcar todo como leído
          </button>
        )}
      </div>

      {/* Notification list */}
      <ul role="list" className="max-h-96 overflow-y-auto divide-y divide-[var(--border-color)]">
        {notifications.length === 0 ? (
          <li className="px-4 py-8 text-center text-sm text-[var(--text-muted)]">
            No tenés notificaciones.
          </li>
        ) : (
          notifications.map((notification) => (
            <NotificationItem
              key={notification.id}
              notification={notification}
              onMarkRead={handleMarkRead}
              onClose={onClose}
            />
          ))
        )}
      </ul>

      {/* Footer */}
      {notifications.length > 0 && (
        <div className="border-t border-[var(--border-color)] px-4 py-2 text-center">
          <Link
            href="/notificaciones"
            onClick={onClose}
            className="text-xs text-[var(--color-link)] hover:underline"
          >
            Ver todas las notificaciones
          </Link>
        </div>
      )}
    </div>
  );
}

interface NotificationItemProps {
  notification: InboxNotification;
  onMarkRead: (id: string) => void;
  onClose: () => void;
}

function NotificationItem({ notification, onMarkRead, onClose }: NotificationItemProps) {
  const isUnread = !notification.readAt;
  const accent = TYPE_ACCENT[notification.type] ?? TYPE_ACCENT.info;
  const timeAgo = formatDistanceToNow(new Date(notification.createdAt), {
    addSuffix: true,
    locale: es,
  });

  const content = (
    <div
      className={`flex gap-3 px-4 py-3 transition-colors hover:bg-[var(--bg-hover)] ${
        isUnread ? 'bg-[var(--bg-unread)]' : ''
      }`}
    >
      {/* Type accent dot */}
      <span
        aria-hidden="true"
        className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ${accent}`}
      />

      <div className="min-w-0 flex-1">
        <p className="text-sm font-medium text-[var(--text-primary)] truncate">
          {notification.title}
        </p>
        <p className="text-xs text-[var(--text-muted)] mt-0.5 line-clamp-2">
          {notification.message}
        </p>
        <p className="text-xs text-[var(--text-faint)] mt-1">{timeAgo}</p>
      </div>

      {isUnread && (
        <button
          type="button"
          aria-label="Marcar como leída"
          onClick={(e) => {
            e.preventDefault();
            e.stopPropagation();
            onMarkRead(notification.id);
          }}
          className="shrink-0 self-start mt-1 text-[var(--text-muted)] hover:text-[var(--text-primary)]"
        >
          <span
            aria-hidden="true"
            className="block h-2 w-2 rounded-full bg-[var(--color-info)]"
          />
        </button>
      )}
    </div>
  );

  if (notification.link) {
    return (
      <li>
        <Link href={notification.link} onClick={onClose}>
          {content}
        </Link>
      </li>
    );
  }

  return <li>{content}</li>;
}
```

### 6. Integration in admin layout header

The parent Server Component fetches counts and passes them as props — no client-side data fetch on mount:

```typescript
// src/app/(admin)/layout.tsx  (or equivalent header Server Component)
import { createServerClient } from '@supabase/ssr';
import { cookies } from 'next/headers';
import NotificationBell from '@/components/notifications/NotificationBell';
import {
  getUnreadCount,
  getRecentNotifications,
} from '@/lib/notifications/inbox';

export default async function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const cookieStore = cookies();
  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    { cookies: { getAll: () => cookieStore.getAll() } }
  );

  const { data: { user } } = await supabase.auth.getUser();

  // Fetch in parallel — both depend only on user.id
  const [unreadCount, notifications] = user
    ? await Promise.all([
        getUnreadCount(user.id),
        getRecentNotifications(user.id, 10),
      ])
    : [0, []];

  return (
    <div>
      <header className="flex items-center justify-between px-6 py-4 border-b border-[var(--border-color)] bg-[var(--bg-surface)]">
        {/* ... other header content ... */}
        {user && (
          <NotificationBell
            unreadCount={unreadCount}
            notifications={notifications}
            userId={user.id}
          />
        )}
      </header>
      <main>{children}</main>
    </div>
  );
}
```

### 7. Creating inbox notifications from Server Actions

When an adoption is approved, insert an inbox notification alongside any outbound sends:

```typescript
// Example: src/app/actions/adoptions.ts
import { createInboxNotification } from '@/lib/notifications/inbox';
import { enqueueWhatsAppNotification } from '@/lib/notifications/queue';
import { buildAdoptionApprovedWA } from '@/lib/whatsapp/templates';
import { formatParaguayanWhatsApp } from '@/lib/whatsapp/send-whatsapp';

export async function approveAdoptionRequest(
  requestId: string,
  adopterId: string,
  adopterUserId: string,  // auth.users id for inbox
  adopterPhone: string,
  animalName: string,
  pickupDate: string
) {
  // ... database update ...

  // In-app notification (immediate, no queue)
  await createInboxNotification({
    userId: adopterUserId,
    title: '¡Tu solicitud fue aprobada!',
    message: `Podés retirar a ${animalName} el ${pickupDate}.`,
    type: 'success',
    link: `/adopciones/${requestId}`,
  });

  // Outbound WhatsApp via queue
  const waPhone = formatParaguayanWhatsApp(adopterPhone);
  if (waPhone) {
    const body = buildAdoptionApprovedWA({
      adopterName: 'Adoptante',
      animalName,
      pickupDate,
      contactPhone: process.env.SHELTER_CONTACT_PHONE ?? '',
    });
    await enqueueWhatsAppNotification({ recipient: waPhone, body });
  }
}
```

### 8. Required CSS variables

Add to your global CSS / Tailwind theme if not already present:

```css
/* globals.css */
:root {
  --bg-unread: hsl(210 50% 98%);   /* Light blue tint for unread rows */
  --bg-hover:  hsl(210 30% 96%);   /* Hover state for list items */
  --bg-card:   hsl(0 0% 100%);     /* Card/dropdown background */
  --bg-surface: hsl(0 0% 98%);     /* Page surface */
  --text-primary: hsl(222 47% 11%);
  --text-muted:   hsl(215 16% 47%);
  --text-faint:   hsl(215 20% 65%);
  --border-color: hsl(214 32% 91%);
  --ring-color:   hsl(215 70% 60%);
  --color-link:   hsl(215 70% 45%);
  --color-info:    hsl(207 90% 54%);
  --color-success: hsl(142 71% 45%);
  --color-warning: hsl(38 92% 50%);
  --color-danger:  hsl(0 72% 51%);
}

.dark {
  --bg-unread: hsl(215 30% 12%);
  --bg-hover:  hsl(215 25% 16%);
  --bg-card:   hsl(222 47% 11%);
  --bg-surface: hsl(222 47% 9%);
  --text-primary: hsl(210 40% 96%);
  --text-muted:   hsl(215 16% 65%);
  --text-faint:   hsl(215 20% 45%);
  --border-color: hsl(215 25% 22%);
  --ring-color:   hsl(215 70% 60%);
  --color-link:   hsl(215 70% 65%);
}
```

### 9. Unit tests — `src/lib/notifications/__tests__/inbox.test.ts`

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest';

// Mock Supabase clients
vi.mock('@supabase/supabase-js', () => ({
  createClient: vi.fn(() => ({
    from: vi.fn(() => ({
      insert: vi.fn(() => ({
        select: vi.fn(() => ({
          single: vi.fn(),
        })),
      })),
    })),
  })),
}));

vi.mock('@supabase/ssr', () => ({
  createServerClient: vi.fn(() => ({
    from: vi.fn(() => ({
      select: vi.fn(() => ({
        eq: vi.fn(() => ({
          is: vi.fn(() => ({
            count: 3,
            error: null,
            // for getRecentNotifications chain:
            order: vi.fn(() => ({
              limit: vi.fn(() => Promise.resolve({ data: [], error: null })),
            })),
          })),
          order: vi.fn(() => ({
            limit: vi.fn(() => Promise.resolve({ data: [], error: null })),
          })),
        })),
      })),
    })),
  })),
}));

vi.mock('next/headers', () => ({
  cookies: vi.fn(() => ({ getAll: vi.fn(() => []) })),
}));

import { createInboxNotification, getRecentNotifications } from '../inbox';
import * as supabaseJs from '@supabase/supabase-js';

function getInsertSingleMock() {
  const mockClient = vi.mocked(supabaseJs.createClient).mock.results[0].value;
  return mockClient.from().insert().select().single;
}

describe('createInboxNotification', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    process.env.NEXT_PUBLIC_SUPABASE_URL = 'https://test.supabase.co';
    process.env.SUPABASE_SERVICE_ROLE_KEY = 'test-service-key';
  });

  it('returns id on successful insert', async () => {
    getInsertSingleMock().mockResolvedValueOnce({
      data: { id: 'notif-uuid-1' },
      error: null,
    });

    const result = await createInboxNotification({
      userId: 'user-uuid',
      title: 'Tu solicitud fue aprobada',
      message: 'Podés retirar a Pelusa el miércoles.',
      type: 'success',
      link: '/adopciones/123',
    });

    expect(result.id).toBe('notif-uuid-1');
    expect(result.error).toBeUndefined();
  });

  it('returns error when insert fails', async () => {
    getInsertSingleMock().mockResolvedValueOnce({
      data: null,
      error: { message: 'foreign key violation' },
    });

    const result = await createInboxNotification({
      userId: 'nonexistent-user',
      title: 'Test',
      message: 'Test message',
    });

    expect(result.error).toContain('foreign key');
    expect(result.id).toBeUndefined();
  });

  it('defaults type to "info" when not specified', async () => {
    const mockFrom = vi.mocked(supabaseJs.createClient).mock.results[0].value.from;
    const mockInsert = vi.fn().mockReturnValue({
      select: () => ({ single: () => Promise.resolve({ data: { id: 'n1' }, error: null }) }),
    });
    mockFrom.mockReturnValue({ insert: mockInsert });

    await createInboxNotification({
      userId: 'user-uuid',
      title: 'Info note',
      message: 'Something happened.',
    });

    expect(mockInsert).toHaveBeenCalledWith(
      expect.objectContaining({ type: 'info' })
    );
  });

  it('sets link to null when not provided', async () => {
    const mockFrom = vi.mocked(supabaseJs.createClient).mock.results[0].value.from;
    const mockInsert = vi.fn().mockReturnValue({
      select: () => ({ single: () => Promise.resolve({ data: { id: 'n2' }, error: null }) }),
    });
    mockFrom.mockReturnValue({ insert: mockInsert });

    await createInboxNotification({
      userId: 'user-uuid',
      title: 'No link',
      message: 'No navigation needed.',
    });

    expect(mockInsert).toHaveBeenCalledWith(
      expect.objectContaining({ link: null })
    );
  });
});

describe('getRecentNotifications', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('returns empty array when Supabase returns error', async () => {
    const { createServerClient } = await import('@supabase/ssr');
    vi.mocked(createServerClient).mockReturnValueOnce({
      from: () => ({
        select: () => ({
          eq: () => ({
            order: () => ({
              limit: () => Promise.resolve({ data: null, error: { message: 'DB error' } }),
            }),
          }),
        }),
      }),
    } as any);

    const result = await getRecentNotifications('user-uuid');

    expect(result).toEqual([]);
  });

  it('maps snake_case DB columns to camelCase interface', async () => {
    const { createServerClient } = await import('@supabase/ssr');
    vi.mocked(createServerClient).mockReturnValueOnce({
      from: () => ({
        select: () => ({
          eq: () => ({
            order: () => ({
              limit: () =>
                Promise.resolve({
                  data: [
                    {
                      id: 'n1',
                      user_id: 'u1',
                      title: 'Hola',
                      message: 'Mensaje de prueba',
                      type: 'success',
                      link: '/adopciones/1',
                      read_at: null,
                      created_at: '2026-04-01T10:00:00Z',
                    },
                  ],
                  error: null,
                }),
            }),
          }),
        }),
      }),
    } as any);

    const result = await getRecentNotifications('u1');

    expect(result).toHaveLength(1);
    expect(result[0].userId).toBe('u1');
    expect(result[0].readAt).toBeNull();
    expect(result[0].createdAt).toBe('2026-04-01T10:00:00Z');
  });
});
```

### Required dependencies

```bash
# date-fns for relative time display ("hace 5 minutos")
npm install date-fns

# @heroicons/react for BellIcon (likely already installed)
npm install @heroicons/react
```

---

## Files to Create / Modify

| Path | Action | Notes |
|------|--------|-------|
| `supabase/migrations/20260401000019_notification_inbox.sql` | Create | Table, index, RLS policies |
| `src/lib/notifications/inbox.ts` | Create | `createInboxNotification`, `getUnreadCount`, `getRecentNotifications` |
| `src/app/actions/notifications.ts` | Create | `markNotificationRead`, `markAllNotificationsRead` Server Actions |
| `src/components/notifications/NotificationBell.tsx` | Create | `'use client'` bell + badge |
| `src/components/notifications/NotificationDropdown.tsx` | Create | Dropdown list |
| `src/lib/notifications/__tests__/inbox.test.ts` | Create | 6 unit tests |
| `src/app/(admin)/layout.tsx` | Modify | Integrate `NotificationBell` in header |

---

## Definition of Done

- [ ] Migration `000019` creates `notification_inbox` with RLS enabled (users see only their own rows)
- [ ] `createInboxNotification()` uses service role to insert (bypasses RLS)
- [ ] `getUnreadCount()` and `getRecentNotifications()` use user session client (RLS enforced)
- [ ] `NotificationBell` renders badge when `unreadCount > 0`, truncates to "9+" above 9
- [ ] `NotificationDropdown` closes on outside click
- [ ] Mark-as-read via Server Action triggers `revalidatePath` so badge count refreshes
- [ ] All text in Spanish (UI labels: "Notificaciones", "Marcar todo como leído", "Ver todas")
- [ ] No hardcoded colors — all Tailwind uses CSS vars (`bg-[var(--...)]`)
- [ ] All 6 unit tests pass
- [ ] `date-fns` with `es` locale used for relative timestamps
