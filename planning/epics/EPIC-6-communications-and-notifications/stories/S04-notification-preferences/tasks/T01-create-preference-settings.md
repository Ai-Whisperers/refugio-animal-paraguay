---
task: T01
story: S04
epic: EPIC-6
title: Create preference settings
status: ready
priority: medium
created: 2026-03-25T17:13:26.733418
---

# T01: Create preference settings

## Description

Build the user-facing notification preferences page where users can enable or disable specific notification channels (email, WhatsApp, in-app) for each event type. Preferences are stored per-user in Supabase and respected by the notification dispatch logic in T02.

Users should be able to control: which channels they receive notifications on, and for which events. All settings default to enabled. No third-party preferences service — Supabase only.

## Acceptance Criteria

- [ ] `notification_preferences` table created with RLS (users manage only their own rows)
- [ ] Default preferences row upserted automatically on first login (or on-demand)
- [ ] Preferences page at `/ajustes/notificaciones` renders current settings
- [ ] Each toggle persists via Server Action with optimistic UI
- [ ] Browser push notification permission toggle — requests permission via Web Notifications API
- [ ] Page is accessible: all toggles have labels, keyboard navigable, WCAG 2.1 AA
- [ ] Unit tests cover preference read/write service functions

## Implementation Notes

### Data model

**Migration**: `supabase/migrations/20260401000021_notification_preferences.sql`

```sql
-- Enum: notification channels
create type public.notification_channel as enum ('email', 'whatsapp', 'in_app');

-- Enum: event types that can trigger notifications
-- Add new values here as new features are introduced.
create type public.notification_event_type as enum (
  'adoption_submitted',       -- adopter submitted a request
  'adoption_approved',        -- staff approved an adoption
  'adoption_rejected',        -- staff rejected an adoption
  'donation_received',        -- donation payment confirmed
  'donation_receipt',         -- monthly/annual receipt ready
  'foster_assignment',        -- assigned as foster carer
  'shelter_alert',            -- urgent shelter-wide announcement
  'volunteer_reminder',       -- upcoming volunteer shift reminder
  'animal_update'             -- update on a specific animal the user follows
);

-- Per-user, per-channel, per-event preference row.
-- Composite primary key: one row per (user, channel, event).
create table public.notification_preferences (
  user_id       uuid not null references auth.users(id) on delete cascade,
  channel       public.notification_channel not null,
  event_type    public.notification_event_type not null,
  enabled       boolean not null default true,
  updated_at    timestamptz not null default now(),

  primary key (user_id, channel, event_type)
);

-- RLS: users can only read and write their own preferences.
alter table public.notification_preferences enable row level security;

create policy "Users can view own preferences"
  on public.notification_preferences for select
  using (auth.uid() = user_id);

create policy "Users can upsert own preferences"
  on public.notification_preferences for insert
  with check (auth.uid() = user_id);

create policy "Users can update own preferences"
  on public.notification_preferences for update
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

-- Browser push consent stored separately — not per-event, just a single boolean.
-- Stored as a profile-level field rather than a preference row.
alter table public.profiles
  add column if not exists browser_push_enabled boolean not null default false;
```

> **Why a normalized table instead of JSONB?** The rules engine in T02 queries preferences with
> `WHERE user_id = $1 AND channel = $2 AND event_type = $3` — a normalized table makes this a
> single indexed lookup. Adding new event types is a schema change (new enum value), which is
> explicit and auditable.

---

### Default preferences bootstrap

When a user first visits the preferences page (or when a notification is about to be sent to a
user who has no preference rows yet), all channel × event combinations default to `enabled = true`.

Rather than inserting all rows at signup, use an **on-demand upsert** pattern: the service
function reads preferences, and for any missing (channel, event) pair returns the default `true`.

**`src/lib/notifications/preferences.ts`**:

```typescript
import { createServerClient } from '@supabase/ssr'
import { cookies } from 'next/headers'
import type { Database } from '@/lib/supabase/database.types'

export type NotificationChannel = 'email' | 'whatsapp' | 'in_app'
export type NotificationEventType =
  | 'adoption_submitted'
  | 'adoption_approved'
  | 'adoption_rejected'
  | 'donation_received'
  | 'donation_receipt'
  | 'foster_assignment'
  | 'shelter_alert'
  | 'volunteer_reminder'
  | 'animal_update'

export const ALL_CHANNELS: NotificationChannel[] = ['email', 'whatsapp', 'in_app']
export const ALL_EVENT_TYPES: NotificationEventType[] = [
  'adoption_submitted',
  'adoption_approved',
  'adoption_rejected',
  'donation_received',
  'donation_receipt',
  'foster_assignment',
  'shelter_alert',
  'volunteer_reminder',
  'animal_update',
]

export interface UserPreferences {
  // preferences[channel][eventType] = enabled
  preferences: Record<NotificationChannel, Record<NotificationEventType, boolean>>
  browserPushEnabled: boolean
}

/**
 * Load all notification preferences for a user.
 * Missing rows (never set) default to true — opt-out model, not opt-in.
 *
 * Uses SSR session client so RLS is enforced.
 */
export async function getUserPreferences(userId: string): Promise<UserPreferences> {
  const cookieStore = await cookies()
  const supabase = createServerClient<Database>(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    { cookies: { getAll: () => cookieStore.getAll() } }
  )

  const [{ data: rows }, { data: profile }] = await Promise.all([
    supabase
      .from('notification_preferences')
      .select('channel, event_type, enabled')
      .eq('user_id', userId),
    supabase
      .from('profiles')
      .select('browser_push_enabled')
      .eq('id', userId)
      .single(),
  ])

  // Build a complete matrix defaulting to true for missing rows.
  const prefs = {} as Record<NotificationChannel, Record<NotificationEventType, boolean>>

  for (const channel of ALL_CHANNELS) {
    prefs[channel] = {} as Record<NotificationEventType, boolean>
    for (const eventType of ALL_EVENT_TYPES) {
      prefs[channel][eventType] = true // default: enabled
    }
  }

  for (const row of rows ?? []) {
    const channel = row.channel as NotificationChannel
    const eventType = row.event_type as NotificationEventType
    prefs[channel][eventType] = row.enabled
  }

  return {
    preferences: prefs,
    browserPushEnabled: profile?.browser_push_enabled ?? false,
  }
}

/**
 * Check if a specific channel is enabled for a user and event type.
 * Used by the rules engine (T02) — lightweight single-row lookup.
 *
 * Returns true if no preference row exists (opt-out model).
 */
export async function isChannelEnabledForUser(
  userId: string,
  channel: NotificationChannel,
  eventType: NotificationEventType
): Promise<boolean> {
  const cookieStore = await cookies()
  const supabase = createServerClient<Database>(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    { cookies: { getAll: () => cookieStore.getAll() } }
  )

  const { data } = await supabase
    .from('notification_preferences')
    .select('enabled')
    .eq('user_id', userId)
    .eq('channel', channel)
    .eq('event_type', eventType)
    .maybeSingle()

  // No row = not yet explicitly set = use default (true).
  return data?.enabled ?? true
}
```

---

### Server Actions

**`src/app/actions/preferences.ts`**:

```typescript
'use server'

import { createServerClient } from '@supabase/ssr'
import { cookies } from 'next/headers'
import { revalidatePath } from 'next/cache'
import type { Database } from '@/lib/supabase/database.types'
import type { NotificationChannel, NotificationEventType } from '@/lib/notifications/preferences'

async function getSessionClient() {
  const cookieStore = await cookies()
  return createServerClient<Database>(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    { cookies: { getAll: () => cookieStore.getAll() } }
  )
}

/**
 * Toggle a single channel+event preference for the authenticated user.
 * Uses upsert — creates the row if it doesn't exist, updates if it does.
 */
export async function setNotificationPreference(
  channel: NotificationChannel,
  eventType: NotificationEventType,
  enabled: boolean
): Promise<{ error?: string }> {
  const supabase = await getSessionClient()
  const { data: { user } } = await supabase.auth.getUser()

  if (!user) return { error: 'No autenticado' }

  const { error } = await supabase
    .from('notification_preferences')
    .upsert({
      user_id: user.id,
      channel,
      event_type: eventType,
      enabled,
      updated_at: new Date().toISOString(),
    }, { onConflict: 'user_id,channel,event_type' })

  if (error) return { error: error.message }

  revalidatePath('/ajustes/notificaciones')
  return {}
}

/**
 * Enable or disable all channels for a given event type at once.
 * Used by the "silence all channels for this event" bulk toggle.
 */
export async function setAllChannelsForEvent(
  eventType: NotificationEventType,
  enabled: boolean
): Promise<{ error?: string }> {
  const supabase = await getSessionClient()
  const { data: { user } } = await supabase.auth.getUser()

  if (!user) return { error: 'No autenticado' }

  const rows = ['email', 'whatsapp', 'in_app'].map((channel) => ({
    user_id: user.id,
    channel: channel as NotificationChannel,
    event_type: eventType,
    enabled,
    updated_at: new Date().toISOString(),
  }))

  const { error } = await supabase
    .from('notification_preferences')
    .upsert(rows, { onConflict: 'user_id,channel,event_type' })

  if (error) return { error: error.message }

  revalidatePath('/ajustes/notificaciones')
  return {}
}

/** Update browser push consent flag on user profile. */
export async function setBrowserPushEnabled(enabled: boolean): Promise<{ error?: string }> {
  const supabase = await getSessionClient()
  const { data: { user } } = await supabase.auth.getUser()

  if (!user) return { error: 'No autenticado' }

  const { error } = await supabase
    .from('profiles')
    .update({ browser_push_enabled: enabled })
    .eq('id', user.id)

  if (error) return { error: error.message }

  revalidatePath('/ajustes/notificaciones')
  return {}
}
```

---

### Page: `/ajustes/notificaciones`

**`src/app/(protected)/ajustes/notificaciones/page.tsx`** (Server Component):

```typescript
import { redirect } from 'next/navigation'
import { createServerClient } from '@supabase/ssr'
import { cookies } from 'next/headers'
import { getUserPreferences } from '@/lib/notifications/preferences'
import { NotificationPreferencesForm } from '@/components/settings/NotificationPreferencesForm'
import type { Database } from '@/lib/supabase/database.types'

export const metadata = { title: 'Preferencias de notificaciones — Refugio Animal Paraguay' }

export default async function NotificationPreferencesPage() {
  const cookieStore = await cookies()
  const supabase = createServerClient<Database>(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    { cookies: { getAll: () => cookieStore.getAll() } }
  )

  const { data: { user } } = await supabase.auth.getUser()
  if (!user) redirect('/login')

  const userPreferences = await getUserPreferences(user.id)

  return (
    <div className="mx-auto max-w-2xl px-4 py-8">
      <h1 className="text-2xl font-semibold text-[var(--text-primary)] mb-2">
        Preferencias de notificaciones
      </h1>
      <p className="text-[var(--text-muted)] mb-8">
        Controlá cómo y cuándo recibís notificaciones de Refugio Animal Paraguay.
      </p>

      <NotificationPreferencesForm initialPreferences={userPreferences} />
    </div>
  )
}
```

---

### Preferences form component

**`src/components/settings/NotificationPreferencesForm.tsx`**:

```typescript
'use client'

import { useState, useTransition, useOptimistic } from 'react'
import {
  setNotificationPreference,
  setAllChannelsForEvent,
  setBrowserPushEnabled,
} from '@/app/actions/preferences'
import type { UserPreferences, NotificationChannel, NotificationEventType } from '@/lib/notifications/preferences'
import { ALL_CHANNELS, ALL_EVENT_TYPES } from '@/lib/notifications/preferences'

// Spanish labels for display in UI
const CHANNEL_LABELS: Record<NotificationChannel, string> = {
  email: 'Email',
  whatsapp: 'WhatsApp',
  in_app: 'En la app',
}

const EVENT_LABELS: Record<NotificationEventType, { title: string; description: string }> = {
  adoption_submitted:  { title: 'Solicitud de adopción enviada',   description: 'Cuando un adoptante envía una solicitud' },
  adoption_approved:   { title: 'Adopción aprobada',               description: 'Cuando tu solicitud es aprobada' },
  adoption_rejected:   { title: 'Adopción rechazada',              description: 'Cuando tu solicitud no es aprobada' },
  donation_received:   { title: 'Donación confirmada',             description: 'Confirmación de pago recibida' },
  donation_receipt:    { title: 'Recibo de donación',              description: 'Recibos periódicos de donaciones' },
  foster_assignment:   { title: 'Asignación de hogar de tránsito', description: 'Cuando se te asigna un animal para cuidar' },
  shelter_alert:       { title: 'Alerta del refugio',              description: 'Anuncios urgentes del refugio' },
  volunteer_reminder:  { title: 'Recordatorio de voluntariado',    description: 'Recordatorios de turnos próximos' },
  animal_update:       { title: 'Actualización de animal',         description: 'Novedades de animales que seguís' },
}

interface NotificationPreferencesFormProps {
  initialPreferences: UserPreferences
}

export function NotificationPreferencesForm({ initialPreferences }: NotificationPreferencesFormProps) {
  const [prefs, setPrefs] = useState(initialPreferences.preferences)
  const [browserPush, setBrowserPush] = useState(initialPreferences.browserPushEnabled)
  const [isPending, startTransition] = useTransition()
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  const handleToggle = (
    channel: NotificationChannel,
    eventType: NotificationEventType,
    enabled: boolean
  ) => {
    // Optimistic update
    setPrefs((prev) => ({
      ...prev,
      [channel]: { ...prev[channel], [eventType]: enabled },
    }))

    startTransition(async () => {
      const { error } = await setNotificationPreference(channel, eventType, enabled)
      if (error) {
        // Roll back optimistic update on error
        setPrefs((prev) => ({
          ...prev,
          [channel]: { ...prev[channel], [eventType]: !enabled },
        }))
        setErrorMessage(error)
      }
    })
  }

  const handleBrowserPushToggle = async (enabled: boolean) => {
    if (enabled && Notification.permission === 'default') {
      const permission = await Notification.requestPermission()
      if (permission !== 'granted') return
    }

    setBrowserPush(enabled)
    startTransition(async () => {
      const { error } = await setBrowserPushEnabled(enabled)
      if (error) {
        setBrowserPush(!enabled)
        setErrorMessage(error)
      }
    })
  }

  return (
    <div className="space-y-8">
      {errorMessage && (
        <div
          role="alert"
          className="rounded-md bg-[var(--color-danger)]/10 border border-[var(--color-danger)]/30 px-4 py-3 text-sm text-[var(--color-danger)]"
        >
          {errorMessage}
        </div>
      )}

      {/* Per-event channel matrix */}
      <section>
        <h2 className="text-lg font-medium text-[var(--text-primary)] mb-4">
          Notificaciones por evento
        </h2>

        {/* Channel header row */}
        <div className="rounded-lg border border-[var(--border-color)] overflow-hidden">
          <div className="grid grid-cols-[1fr_repeat(3,_80px)] gap-0 bg-[var(--bg-surface)] px-4 py-3 border-b border-[var(--border-color)]">
            <span className="text-xs font-medium text-[var(--text-muted)] uppercase tracking-wide">
              Evento
            </span>
            {ALL_CHANNELS.map((channel) => (
              <span
                key={channel}
                className="text-xs font-medium text-[var(--text-muted)] uppercase tracking-wide text-center"
              >
                {CHANNEL_LABELS[channel]}
              </span>
            ))}
          </div>

          {ALL_EVENT_TYPES.map((eventType, idx) => (
            <div
              key={eventType}
              className={`grid grid-cols-[1fr_repeat(3,_80px)] gap-0 px-4 py-4 items-center ${
                idx < ALL_EVENT_TYPES.length - 1 ? 'border-b border-[var(--border-color)]' : ''
              } hover:bg-[var(--bg-hover)] transition-colors`}
            >
              <div>
                <p className="text-sm font-medium text-[var(--text-primary)]">
                  {EVENT_LABELS[eventType].title}
                </p>
                <p className="text-xs text-[var(--text-muted)] mt-0.5">
                  {EVENT_LABELS[eventType].description}
                </p>
              </div>

              {ALL_CHANNELS.map((channel) => (
                <div key={channel} className="flex justify-center">
                  <label className="sr-only">
                    {CHANNEL_LABELS[channel]} para {EVENT_LABELS[eventType].title}
                  </label>
                  <Toggle
                    checked={prefs[channel][eventType]}
                    onChange={(enabled) => handleToggle(channel, eventType, enabled)}
                    disabled={isPending}
                  />
                </div>
              ))}
            </div>
          ))}
        </div>
      </section>

      {/* Browser push */}
      <section className="rounded-lg border border-[var(--border-color)] p-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-[var(--text-primary)]">
              Notificaciones del navegador
            </p>
            <p className="text-xs text-[var(--text-muted)] mt-0.5">
              Recibí alertas incluso cuando no estés en la pestaña
            </p>
          </div>
          <Toggle
            checked={browserPush}
            onChange={handleBrowserPushToggle}
            disabled={isPending}
          />
        </div>
      </section>
    </div>
  )
}

// Accessible toggle switch
interface ToggleProps {
  checked: boolean
  onChange: (value: boolean) => void
  disabled?: boolean
}

function Toggle({ checked, onChange, disabled = false }: ToggleProps) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      onClick={() => onChange(!checked)}
      disabled={disabled}
      className={`
        relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full border-2 border-transparent
        transition-colors duration-200 ease-in-out
        focus:outline-none focus:ring-2 focus:ring-[var(--ring-color)] focus:ring-offset-2
        disabled:opacity-50 disabled:cursor-not-allowed
        ${checked ? 'bg-[var(--color-info)]' : 'bg-[var(--text-faint)]'}
      `}
    >
      <span
        aria-hidden="true"
        className={`
          pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow ring-0
          transition duration-200 ease-in-out
          ${checked ? 'translate-x-4' : 'translate-x-0'}
        `}
      />
    </button>
  )
}
```

---

### Navigation: add preferences link to settings sidebar

In the settings layout sidebar (or wherever `/ajustes` navigation lives), add:

```typescript
// In the settings nav items array:
{
  href: '/ajustes/notificaciones',
  label: 'Notificaciones',
  icon: BellIcon,
}
```

---

### CSS variables required (additional to EPIC-6/S03)

No new CSS variables needed beyond what S03/T01 defined. Reuses `--bg-surface`, `--bg-hover`, `--border-color`, `--text-primary`, `--text-muted`, `--text-faint`, `--ring-color`, `--color-info`, `--color-danger`.

---

### Unit tests

**`src/lib/notifications/__tests__/preferences.test.ts`**:

```typescript
import { vi, describe, it, expect, beforeEach } from 'vitest'

vi.mock('next/headers', () => ({ cookies: vi.fn().mockResolvedValue({ getAll: () => [] }) }))
vi.mock('@supabase/ssr', () => ({
  createServerClient: vi.fn(),
}))

import { createServerClient } from '@supabase/ssr'
import { getUserPreferences, isChannelEnabledForUser } from '../preferences'

const mockSelect = vi.fn()
const mockEq = vi.fn().mockReturnThis()
const mockMaybeSingle = vi.fn()
const mockSingle = vi.fn()

const mockFrom = vi.fn().mockReturnValue({
  select: mockSelect.mockReturnValue({
    eq: mockEq,
    maybeSingle: mockMaybeSingle,
    single: mockSingle,
  }),
})

beforeEach(() => {
  vi.clearAllMocks()
  vi.mocked(createServerClient).mockReturnValue({
    from: mockFrom,
  } as unknown as ReturnType<typeof createServerClient>)
})

describe('isChannelEnabledForUser', () => {
  it('returns true when no preference row exists (default opt-out model)', async () => {
    mockMaybeSingle.mockResolvedValue({ data: null, error: null })

    const result = await isChannelEnabledForUser('user-1', 'email', 'adoption_approved')

    expect(result).toBe(true)
  })

  it('returns stored enabled value when preference row exists', async () => {
    mockMaybeSingle.mockResolvedValue({ data: { enabled: false }, error: null })

    const result = await isChannelEnabledForUser('user-1', 'whatsapp', 'donation_received')

    expect(result).toBe(false)
  })

  it('returns true when enabled = true in stored row', async () => {
    mockMaybeSingle.mockResolvedValue({ data: { enabled: true }, error: null })

    const result = await isChannelEnabledForUser('user-1', 'in_app', 'shelter_alert')

    expect(result).toBe(true)
  })
})

describe('getUserPreferences', () => {
  it('defaults all channel+event combinations to true when no rows exist', async () => {
    mockFrom.mockReturnValueOnce({
      select: vi.fn().mockReturnValue({ eq: vi.fn().mockResolvedValue({ data: [], error: null }) }),
    })
    mockFrom.mockReturnValueOnce({
      select: vi.fn().mockReturnValue({
        eq: vi.fn().mockReturnValue({ single: vi.fn().mockResolvedValue({ data: { browser_push_enabled: false } }) }),
      }),
    })

    const { preferences } = await getUserPreferences('user-1')

    expect(preferences.email.adoption_approved).toBe(true)
    expect(preferences.whatsapp.shelter_alert).toBe(true)
    expect(preferences.in_app.donation_received).toBe(true)
  })

  it('applies stored disabled rows on top of defaults', async () => {
    mockFrom.mockReturnValueOnce({
      select: vi.fn().mockReturnValue({
        eq: vi.fn().mockResolvedValue({
          data: [{ channel: 'email', event_type: 'donation_receipt', enabled: false }],
          error: null,
        }),
      }),
    })
    mockFrom.mockReturnValueOnce({
      select: vi.fn().mockReturnValue({
        eq: vi.fn().mockReturnValue({ single: vi.fn().mockResolvedValue({ data: { browser_push_enabled: false } }) }),
      }),
    })

    const { preferences } = await getUserPreferences('user-1')

    // The stored row overrides the default
    expect(preferences.email.donation_receipt).toBe(false)
    // Everything else remains true
    expect(preferences.email.adoption_approved).toBe(true)
  })
})
```

---

### Files changed

| File | Action | Description |
|------|--------|-------------|
| `supabase/migrations/20260401000021_notification_preferences.sql` | Create | `notification_preferences` table, RLS, enums; `browser_push_enabled` on profiles |
| `src/lib/notifications/preferences.ts` | Create | `getUserPreferences()`, `isChannelEnabledForUser()`, channel/event constants and types |
| `src/app/actions/preferences.ts` | Create | Server Actions: `setNotificationPreference()`, `setAllChannelsForEvent()`, `setBrowserPushEnabled()` |
| `src/app/(protected)/ajustes/notificaciones/page.tsx` | Create | Server Component: fetch preferences, render form |
| `src/components/settings/NotificationPreferencesForm.tsx` | Create | Client Component: toggle matrix, optimistic updates, browser push |
| `src/lib/notifications/__tests__/preferences.test.ts` | Create | Unit tests for preference service functions |

## Related Issues

- EPIC-6
- S04
- S04/T02 (rules engine reads preferences written by this task)
