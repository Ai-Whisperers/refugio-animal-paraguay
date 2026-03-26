---
task: T02
story: S04
epic: EPIC-6
title: Implement rules engine
status: ready
priority: medium
created: 2026-03-25T17:13:26.733486
---

# T02: Implement rules engine

## Description

Implement the notification routing rules engine that decides which channels to dispatch for each notification event, based on: user preferences (S04/T01), system-level event routing configuration, and channel availability (does the user have an email or WhatsApp number on record?). The rules engine is a pure server-side function called from Server Actions before inserting into `notification_queue` (outbound) or `notification_inbox` (in-app).

No queue worker, no event bus, no Redis. The rules engine runs synchronously inside Server Actions and returns a dispatch plan.

## Acceptance Criteria

- [ ] `resolveNotificationDispatch()` returns which channels to use for a given user + event
- [ ] User preference is checked per channel — disabled channels are excluded
- [ ] Channel availability is checked — no email dispatch if user has no email; no WhatsApp if no phone
- [ ] In-app notifications are always attempted unless explicitly disabled in user preferences
- [ ] System-level event routing config (which channels are allowed per event) is respected
- [ ] Rules engine is pure (no DB writes) — callers are responsible for executing the dispatch
- [ ] Server Actions in adoption/donation flows updated to call the rules engine
- [ ] Unit tests cover all exclusion logic (preference off, no contact info, system config)

## Implementation Notes

### Conceptual model

The rules engine answers one question:

> For user X, event Y — which channels should receive a notification?

It evaluates three layers in order:

```
Layer 1: System config   — Is this channel allowed for this event type at all?
             ↓ (excluded channels filtered out)
Layer 2: User preference — Has the user disabled this channel for this event?
             ↓ (opt-out channels filtered out)
Layer 3: Availability    — Does the user have the contact info needed for this channel?
             ↓ (channels without contact info filtered out)

Result: Set of channels to dispatch to
```

---

### Step 1 — System-level event routing configuration

Define which channels are allowed per event type. This is a code-level constant, not a database table — changing it requires a code deployment, which is intentional (it's a product decision, not user configuration).

**`src/lib/notifications/routing-config.ts`**:

```typescript
import type { NotificationChannel, NotificationEventType } from './preferences'

/**
 * System-level channel allowlist per event type.
 *
 * Defines the maximum set of channels that MAY be used for each event.
 * User preferences and contact availability further narrow this set.
 *
 * Adding a new event type requires adding an entry here.
 * Removing a channel from an event here immediately prevents dispatch
 * regardless of user preferences.
 */
export const EVENT_CHANNEL_CONFIG: Record<NotificationEventType, NotificationChannel[]> = {
  // Transactional — all channels available
  adoption_submitted:  ['email', 'whatsapp', 'in_app'],
  adoption_approved:   ['email', 'whatsapp', 'in_app'],
  adoption_rejected:   ['email', 'in_app'],          // no WhatsApp for rejections (too jarring)
  donation_received:   ['email', 'in_app'],           // receipts are formal — email only + in-app
  donation_receipt:    ['email', 'in_app'],
  foster_assignment:   ['email', 'whatsapp', 'in_app'],
  shelter_alert:       ['email', 'whatsapp', 'in_app'],
  volunteer_reminder:  ['whatsapp', 'in_app'],        // reminder = short, WhatsApp is better
  animal_update:       ['in_app'],                    // non-urgent, in-app only
}
```

---

### Step 2 — User contact availability check

**`src/lib/notifications/contact-availability.ts`**:

```typescript
import { createServerClient } from '@supabase/ssr'
import { cookies } from 'next/headers'
import type { Database } from '@/lib/supabase/database.types'
import type { NotificationChannel } from './preferences'

export interface UserContactInfo {
  email: string | null
  whatsappPhone: string | null
  hasEmail: boolean
  hasWhatsapp: boolean
}

/**
 * Look up which contact channels are available for a user.
 * A channel is available only if the user has a verified contact method for it.
 *
 * Uses service role client — this is called server-side to look up other users'
 * contact info (e.g., staff triggering notifications for an adopter).
 */
export async function getUserContactInfo(userId: string): Promise<UserContactInfo> {
  const cookieStore = await cookies()
  const supabase = createServerClient<Database>(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!,
    { cookies: { getAll: () => cookieStore.getAll() } }
  )

  const { data } = await supabase
    .from('profiles')
    .select('email, whatsapp_phone')
    .eq('id', userId)
    .single()

  return {
    email: data?.email ?? null,
    whatsappPhone: data?.whatsapp_phone ?? null,
    hasEmail: !!data?.email,
    hasWhatsapp: !!data?.whatsapp_phone,
  }
}

/**
 * Return whether a channel is available for a user based on contact info.
 * in_app is always available — it doesn't require contact info.
 */
export function isChannelAvailable(
  channel: NotificationChannel,
  contactInfo: UserContactInfo
): boolean {
  switch (channel) {
    case 'email':     return contactInfo.hasEmail
    case 'whatsapp':  return contactInfo.hasWhatsapp
    case 'in_app':    return true  // in-app never requires contact info
  }
}
```

---

### Step 3 — Rules engine

**`src/lib/notifications/rules-engine.ts`**:

```typescript
import { isChannelEnabledForUser } from './preferences'
import { getUserContactInfo, isChannelAvailable } from './contact-availability'
import { EVENT_CHANNEL_CONFIG } from './routing-config'
import type { NotificationChannel, NotificationEventType } from './preferences'

export interface DispatchPlan {
  /** Channels that should receive this notification */
  channels: NotificationChannel[]
  /** Channels excluded and why — useful for debug logging */
  excluded: { channel: NotificationChannel; reason: ExclusionReason }[]
}

export type ExclusionReason =
  | 'not_in_system_config'   // channel not allowed for this event type at system level
  | 'user_preference_off'    // user has disabled this channel for this event
  | 'no_contact_info'        // user has no email/phone for this channel

/**
 * Determine which notification channels to dispatch for a given user + event.
 *
 * Pure function in terms of side effects — does DB reads but no writes.
 * Callers are responsible for executing the actual dispatch (insert to
 * notification_queue for outbound, notification_inbox for in-app).
 *
 * @param userId   - Target user's auth.users id
 * @param eventType - The notification event being triggered
 * @returns DispatchPlan listing channels to use and excluded channels with reasons
 */
export async function resolveNotificationDispatch(
  userId: string,
  eventType: NotificationEventType
): Promise<DispatchPlan> {
  const systemAllowedChannels = EVENT_CHANNEL_CONFIG[eventType]

  const allChannels: NotificationChannel[] = ['email', 'whatsapp', 'in_app']
  const included: NotificationChannel[] = []
  const excluded: DispatchPlan['excluded'] = []

  // Layer 1: filter to system-allowed channels
  const systemFiltered = allChannels.filter((channel) => {
    if (!systemAllowedChannels.includes(channel)) {
      excluded.push({ channel, reason: 'not_in_system_config' })
      return false
    }
    return true
  })

  // Layer 2 + 3: preference and availability checks run in parallel per remaining channel
  const [contactInfo, ...prefResults] = await Promise.all([
    getUserContactInfo(userId),
    ...systemFiltered.map((channel) =>
      isChannelEnabledForUser(userId, channel, eventType)
    ),
  ])

  for (let i = 0; i < systemFiltered.length; i++) {
    const channel = systemFiltered[i]
    const prefEnabled = prefResults[i]

    if (!prefEnabled) {
      excluded.push({ channel, reason: 'user_preference_off' })
      continue
    }

    if (!isChannelAvailable(channel, contactInfo)) {
      excluded.push({ channel, reason: 'no_contact_info' })
      continue
    }

    included.push(channel)
  }

  return { channels: included, excluded }
}
```

---

### Step 4 — Unified dispatch helper

Callers should not need to wire up queue inserts + inbox inserts manually. Provide a single function that takes the dispatch plan and executes it.

**`src/lib/notifications/dispatch.ts`**:

```typescript
import { enqueueNotification } from './queue'         // from EPIC-6/S01/T03
import { createInboxNotification } from './inbox'     // from EPIC-6/S03/T01
import type { NotificationChannel } from './preferences'

export interface NotificationPayload {
  userId: string
  eventType: string
  title: string
  message: string
  link?: string | null
  // Channel-specific content overrides (e.g., WhatsApp uses shorter message)
  emailSubject?: string
  whatsappMessage?: string
}

/**
 * Execute a dispatch plan: for each channel in the plan, insert the appropriate record.
 *
 * - email / whatsapp → notification_queue (outbound, processed by queue worker or edge function)
 * - in_app → notification_inbox (immediate, surfaced in UI via Realtime)
 *
 * Errors are logged per channel — one channel failing does not block others.
 */
export async function executeDispatch(
  channels: NotificationChannel[],
  payload: NotificationPayload
): Promise<void> {
  const tasks = channels.map(async (channel) => {
    if (channel === 'in_app') {
      const { error } = await createInboxNotification({
        userId: payload.userId,
        title: payload.title,
        message: payload.message,
        type: resolveInboxType(payload.eventType),
        link: payload.link ?? null,
      })
      if (error) {
        console.error('[dispatch] in_app insert failed', { userId: payload.userId, error })
      }
      return
    }

    const { error } = await enqueueNotification({
      userId: payload.userId,
      channel,
      eventType: payload.eventType,
      subject: channel === 'email' ? (payload.emailSubject ?? payload.title) : undefined,
      message: channel === 'whatsapp' ? (payload.whatsappMessage ?? payload.message) : payload.message,
      link: payload.link ?? null,
    })
    if (error) {
      console.error(`[dispatch] ${channel} queue insert failed`, { userId: payload.userId, error })
    }
  })

  await Promise.all(tasks)
}

// Map event type string to notification_inbox type enum
function resolveInboxType(eventType: string): 'info' | 'success' | 'warning' | 'error' {
  if (eventType.includes('approved') || eventType.includes('received')) return 'success'
  if (eventType.includes('rejected'))  return 'error'
  if (eventType.includes('alert'))     return 'warning'
  return 'info'
}
```

---

### Step 5 — Integration: adoption approval Server Action

Update the existing adoption approval Server Action to use the rules engine. Replace any direct `enqueueNotification` calls with the `resolveNotificationDispatch` + `executeDispatch` pattern.

**Example: `src/app/actions/adoptions.ts`** (partial update):

```typescript
'use server'

import { resolveNotificationDispatch } from '@/lib/notifications/rules-engine'
import { executeDispatch } from '@/lib/notifications/dispatch'

// Inside approveAdoptionRequest():

const { channels } = await resolveNotificationDispatch(adopterUserId, 'adoption_approved')

await executeDispatch(channels, {
  userId: adopterUserId,
  eventType: 'adoption_approved',
  title: '¡Tu solicitud fue aprobada!',
  message: `Podés retirar a ${animalName} el ${pickupDate}.`,
  link: `/adopciones/${requestId}`,
  emailSubject: `Solicitud de adopción aprobada — ${animalName}`,
  whatsappMessage: `¡Hola! Tu solicitud de adopción de ${animalName} fue aprobada. Podés retirarla el ${pickupDate}. Ver detalles: ${appBaseUrl}/adopciones/${requestId}`,
})
```

**Example: `src/app/actions/adoptions.ts`** (rejection):

```typescript
const { channels } = await resolveNotificationDispatch(adopterUserId, 'adoption_rejected')

await executeDispatch(channels, {
  userId: adopterUserId,
  eventType: 'adoption_rejected',
  title: 'Solicitud no aprobada',
  message: `Tu solicitud de adopción de ${animalName} no fue aprobada en este momento. Podés presentar una nueva solicitud para otro animal.`,
  link: `/adopciones/${requestId}`,
})
```

---

### Step 6 — Unit tests

**`src/lib/notifications/__tests__/rules-engine.test.ts`**:

```typescript
import { vi, describe, it, expect, beforeEach } from 'vitest'

vi.mock('../preferences', () => ({
  isChannelEnabledForUser: vi.fn(),
}))
vi.mock('../contact-availability', () => ({
  getUserContactInfo: vi.fn(),
  isChannelAvailable: vi.fn(),
}))

import { resolveNotificationDispatch } from '../rules-engine'
import { isChannelEnabledForUser } from '../preferences'
import { getUserContactInfo, isChannelAvailable } from '../contact-availability'

const fullContactInfo = { email: 'u@example.com', whatsappPhone: '+595991000000', hasEmail: true, hasWhatsapp: true }
const noPhoneContactInfo = { email: 'u@example.com', whatsappPhone: null, hasEmail: true, hasWhatsapp: false }

beforeEach(() => {
  vi.clearAllMocks()
  vi.mocked(getUserContactInfo).mockResolvedValue(fullContactInfo)
  vi.mocked(isChannelEnabledForUser).mockResolvedValue(true)
  vi.mocked(isChannelAvailable).mockImplementation(
    (channel, info) => channel === 'in_app' || (channel === 'email' && info.hasEmail) || (channel === 'whatsapp' && info.hasWhatsapp)
  )
})

describe('resolveNotificationDispatch', () => {
  it('returns all allowed channels when preferences and contact info are complete', async () => {
    const plan = await resolveNotificationDispatch('user-1', 'adoption_approved')

    // adoption_approved allows email + whatsapp + in_app (per routing config)
    expect(plan.channels).toContain('email')
    expect(plan.channels).toContain('whatsapp')
    expect(plan.channels).toContain('in_app')
    expect(plan.excluded).toHaveLength(0)
  })

  it('excludes channel not in system config', async () => {
    // animal_update allows only in_app per routing config
    const plan = await resolveNotificationDispatch('user-1', 'animal_update')

    expect(plan.channels).toEqual(['in_app'])
    expect(plan.excluded).toContainEqual({ channel: 'email', reason: 'not_in_system_config' })
    expect(plan.excluded).toContainEqual({ channel: 'whatsapp', reason: 'not_in_system_config' })
  })

  it('excludes channel disabled by user preference', async () => {
    vi.mocked(isChannelEnabledForUser).mockImplementation(
      (_userId, channel) => channel !== 'whatsapp'
    )

    const plan = await resolveNotificationDispatch('user-1', 'adoption_approved')

    expect(plan.channels).not.toContain('whatsapp')
    expect(plan.excluded).toContainEqual({ channel: 'whatsapp', reason: 'user_preference_off' })
  })

  it('excludes channel when user has no contact info', async () => {
    vi.mocked(getUserContactInfo).mockResolvedValue(noPhoneContactInfo)
    vi.mocked(isChannelAvailable).mockImplementation(
      (channel, info) => channel === 'in_app' || (channel === 'email' && info.hasEmail) || (channel === 'whatsapp' && info.hasWhatsapp)
    )

    const plan = await resolveNotificationDispatch('user-1', 'adoption_approved')

    expect(plan.channels).not.toContain('whatsapp')
    expect(plan.excluded).toContainEqual({ channel: 'whatsapp', reason: 'no_contact_info' })
  })

  it('always includes in_app unless user preference is off', async () => {
    vi.mocked(isChannelEnabledForUser).mockResolvedValue(false)

    const plan = await resolveNotificationDispatch('user-1', 'shelter_alert')

    expect(plan.channels).toHaveLength(0)
    expect(plan.excluded.every((e) => e.reason === 'user_preference_off')).toBe(true)
  })

  it('returns empty channels array when all are excluded', async () => {
    vi.mocked(getUserContactInfo).mockResolvedValue({ email: null, whatsappPhone: null, hasEmail: false, hasWhatsapp: false })
    vi.mocked(isChannelAvailable).mockReturnValue(false)
    vi.mocked(isChannelEnabledForUser).mockResolvedValue(true)

    // animal_update = in_app only; in_app is available regardless of contact info
    // but isChannelAvailable is mocked to return false above
    const plan = await resolveNotificationDispatch('user-1', 'animal_update')

    expect(plan.channels).toHaveLength(0)
    expect(plan.excluded).toContainEqual({ channel: 'in_app', reason: 'no_contact_info' })
  })

  it('runs preference and availability checks in parallel (Promise.all)', async () => {
    let callOrder: string[] = []

    vi.mocked(getUserContactInfo).mockImplementation(async () => {
      callOrder.push('contact')
      return fullContactInfo
    })
    vi.mocked(isChannelEnabledForUser).mockImplementation(async () => {
      callOrder.push('pref')
      return true
    })

    await resolveNotificationDispatch('user-1', 'adoption_approved')

    // Both contact and pref calls should start (order may interleave, not sequential)
    expect(callOrder).toContain('contact')
    expect(callOrder).toContain('pref')
  })
})
```

---

### Files changed

| File | Action | Description |
|------|--------|-------------|
| `src/lib/notifications/routing-config.ts` | Create | System-level EVENT_CHANNEL_CONFIG constant |
| `src/lib/notifications/contact-availability.ts` | Create | `getUserContactInfo()`, `isChannelAvailable()` |
| `src/lib/notifications/rules-engine.ts` | Create | `resolveNotificationDispatch()` — 3-layer filtering |
| `src/lib/notifications/dispatch.ts` | Create | `executeDispatch()` — routes to queue or inbox per channel |
| `src/app/actions/adoptions.ts` | Update | Replace direct enqueue with rules engine + executeDispatch |
| `src/app/actions/donations.ts` | Update | Replace direct enqueue with rules engine + executeDispatch |
| `src/lib/notifications/__tests__/rules-engine.test.ts` | Create | 6 unit tests covering all exclusion layers |

---

### Architecture summary

```
Server Action (e.g., approveAdoptionRequest)
  │
  ├── resolveNotificationDispatch(userId, 'adoption_approved')
  │     ├── Layer 1: EVENT_CHANNEL_CONFIG → ['email', 'whatsapp', 'in_app']
  │     ├── Layer 2: isChannelEnabledForUser() × 3 (parallel) → filters user-disabled
  │     └── Layer 3: getUserContactInfo() + isChannelAvailable() → filters missing contact
  │           └── Returns: { channels: ['email', 'in_app'], excluded: [{channel: 'whatsapp', reason: 'no_contact_info'}] }
  │
  └── executeDispatch(['email', 'in_app'], payload)
        ├── email  → enqueueNotification() → notification_queue INSERT
        └── in_app → createInboxNotification() → notification_inbox INSERT
                           └── Supabase Realtime pushes to client (S03/T02)
```

## Related Issues

- EPIC-6
- S04
- S04/T01 (prerequisite — preference table and `isChannelEnabledForUser()`)
- EPIC-6/S01/T03 (prerequisite — `enqueueNotification()` from notification queue)
- EPIC-6/S03/T01 (prerequisite — `createInboxNotification()` from inbox)
