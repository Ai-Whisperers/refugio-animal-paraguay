---
task: T03
story: S01
epic: EPIC-5
title: Setup role assignment
status: ready
priority: medium
created: 2026-03-25T17:13:26.731467
---

# T03: Setup role assignment

## Description

Build the admin interface for reviewing pending volunteer applications and updating volunteer status. Admins can approve (`pending_review → active`), reject (`pending_review → rejected`), deactivate (`active → inactive`), or reactivate (`inactive → active`) volunteers. A Server Action using the service role client enforces admin-only access and executes status transitions.

## Acceptance Criteria

- [ ] Page at `/admin/volunteers` lists all volunteers; non-admins redirect to `/`
- [ ] List can be filtered by status (pending_review, active, inactive, rejected) via query param
- [ ] Each row links to `/admin/volunteers/[id]` with volunteer details and status controls
- [ ] Status update form shows only the allowed transition actions for the current status
- [ ] Server Action validates admin identity, validates the status transition, and updates the row
- [ ] Invalid transitions (e.g. `rejected → active`) return a Spanish error message
- [ ] Unit tests cover the status transition validation helper

## Implementation Notes

### Status transition rules

| Current status | Allowed transitions |
|---------------|---------------------|
| `pending_review` | `active` (approve), `rejected` (reject) |
| `active` | `inactive` (deactivate) |
| `inactive` | `active` (reactivate) |
| `rejected` | *(none)* |

### Status transition validation helper

**`src/lib/volunteers/validate-status-transition.ts`**

```typescript
import type { VolunteerStatus } from './types'

export interface TransitionError {
  message: string
}

const ALLOWED_TRANSITIONS: Record<VolunteerStatus, VolunteerStatus[]> = {
  pending_review: ['active', 'rejected'],
  active: ['inactive'],
  inactive: ['active'],
  rejected: [],
}

export function validateStatusTransition(
  current: VolunteerStatus,
  next: VolunteerStatus,
): TransitionError | null {
  if (!ALLOWED_TRANSITIONS[current].includes(next)) {
    return {
      message: `No se puede cambiar el estado de "${current}" a "${next}".`,
    }
  }
  return null
}

export function getAllowedTransitions(current: VolunteerStatus): VolunteerStatus[] {
  return ALLOWED_TRANSITIONS[current]
}
```

### Unit tests

**`src/lib/volunteers/__tests__/validate-status-transition.test.ts`**

```typescript
import { describe, it, expect } from 'vitest'
import {
  validateStatusTransition,
  getAllowedTransitions,
} from '../validate-status-transition'

describe('validateStatusTransition', () => {
  it('allows pending_review → active', () => {
    expect(validateStatusTransition('pending_review', 'active')).toBeNull()
  })
  it('allows pending_review → rejected', () => {
    expect(validateStatusTransition('pending_review', 'rejected')).toBeNull()
  })
  it('allows active → inactive', () => {
    expect(validateStatusTransition('active', 'inactive')).toBeNull()
  })
  it('allows inactive → active', () => {
    expect(validateStatusTransition('inactive', 'active')).toBeNull()
  })
  it('blocks rejected → active', () => {
    expect(validateStatusTransition('rejected', 'active')).not.toBeNull()
  })
  it('blocks active → rejected', () => {
    expect(validateStatusTransition('active', 'rejected')).not.toBeNull()
  })
  it('blocks active → active (no-op)', () => {
    expect(validateStatusTransition('active', 'active')).not.toBeNull()
  })
  it('error message is in Spanish', () => {
    const err = validateStatusTransition('rejected', 'active')
    expect(err?.message).toMatch(/No se puede/)
  })
})

describe('getAllowedTransitions', () => {
  it('returns two options for pending_review', () => {
    expect(getAllowedTransitions('pending_review')).toHaveLength(2)
  })
  it('returns empty array for rejected', () => {
    expect(getAllowedTransitions('rejected')).toHaveLength(0)
  })
})
```

### Update VolunteerProfile type

Add `VolunteerStatus` as a named export to `src/lib/volunteers/types.ts`:

```typescript
export type VolunteerStatus = 'pending_review' | 'active' | 'inactive' | 'rejected'

export interface VolunteerProfile {
  id: string
  full_name: string
  phone: string | null
  availability: string[]
  skills: string[]
  motivation: string | null
  status: VolunteerStatus
  hours_total: number
  notes: string | null
  created_at: string
  updated_at: string
}
```

### Admin check helper

**`src/lib/auth/is-admin.ts`**

```typescript
import { createClient } from '@supabase/supabase-js'

// Service role client — bypasses RLS for privileged reads
const supabaseAdmin = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!,
)

/**
 * Returns true if the given user ID has the 'admin' role.
 * Reads from the `user_roles` table (service role — RLS bypassed).
 */
export async function isAdmin(userId: string): Promise<boolean> {
  const { data } = await supabaseAdmin
    .from('user_roles')
    .select('role')
    .eq('user_id', userId)
    .eq('role', 'admin')
    .maybeSingle()

  return data !== null
}
```

> **Note**: The `user_roles` table is created by the migration in T01 (or a follow-up migration). Schema: `user_id uuid references auth.users`, `role text`, primary key `(user_id, role)`.

### Server Action

**`src/app/actions/update-volunteer-status.ts`**

```typescript
'use server'

import { createRouteHandlerClient } from '@supabase/auth-helpers-nextjs'
import { createClient } from '@supabase/supabase-js'
import { cookies } from 'next/headers'
import { revalidatePath } from 'next/cache'
import { isAdmin } from '@/lib/auth/is-admin'
import { validateStatusTransition } from '@/lib/volunteers/validate-status-transition'
import type { VolunteerStatus } from '@/lib/volunteers/types'

const supabaseAdmin = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!,
)

export async function updateVolunteerStatus(
  volunteerId: string,
  nextStatus: VolunteerStatus,
): Promise<{ error?: string }> {
  // 1. Identify the calling user
  const supabase = createRouteHandlerClient({ cookies })
  const {
    data: { user },
  } = await supabase.auth.getUser()
  if (!user) return { error: 'Sesión expirada. Iniciá sesión de nuevo.' }

  // 2. Verify admin role
  const admin = await isAdmin(user.id)
  if (!admin) return { error: 'No tenés permisos para realizar esta acción.' }

  // 3. Fetch current status of the target volunteer
  const { data: profile, error: fetchError } = await supabaseAdmin
    .from('volunteer_profiles')
    .select('status')
    .eq('id', volunteerId)
    .single()

  if (fetchError || !profile) return { error: 'Voluntario/a no encontrado/a.' }

  // 4. Validate the transition
  const transitionError = validateStatusTransition(
    profile.status as VolunteerStatus,
    nextStatus,
  )
  if (transitionError) return { error: transitionError.message }

  // 5. Apply the update (service role bypasses RLS)
  const { error: updateError } = await supabaseAdmin
    .from('volunteer_profiles')
    .update({ status: nextStatus, updated_at: new Date().toISOString() })
    .eq('id', volunteerId)

  if (updateError) return { error: 'Error al actualizar el estado. Intentá de nuevo.' }

  revalidatePath('/admin/volunteers')
  revalidatePath(`/admin/volunteers/${volunteerId}`)
  return {}
}
```

### Volunteer status form (client component)

**`src/app/admin/volunteers/[id]/VolunteerStatusForm.tsx`**

```typescript
'use client'

import { useTransition, useState } from 'react'
import { updateVolunteerStatus } from '@/app/actions/update-volunteer-status'
import { getAllowedTransitions } from '@/lib/volunteers/validate-status-transition'
import type { VolunteerStatus } from '@/lib/volunteers/types'

const STATUS_LABEL: Record<VolunteerStatus, string> = {
  pending_review: 'Pendiente de revisión',
  active: 'Activo/a',
  inactive: 'Inactivo/a',
  rejected: 'Rechazado/a',
}

const ACTION_LABEL: Record<VolunteerStatus, string> = {
  active: 'Aprobar',
  rejected: 'Rechazar',
  inactive: 'Desactivar',
  // inactive → active reuses 'active' key below
}

const REACTIVATE_LABEL = 'Reactivar'

interface Props {
  volunteerId: string
  currentStatus: VolunteerStatus
}

export function VolunteerStatusForm({ volunteerId, currentStatus }: Props) {
  const [isPending, startTransition] = useTransition()
  const [serverError, setServerError] = useState<string | null>(null)

  const allowed = getAllowedTransitions(currentStatus)

  if (allowed.length === 0) {
    return (
      <p className="text-sm text-[var(--text-secondary)]">
        No hay acciones disponibles para este estado.
      </p>
    )
  }

  function handleAction(nextStatus: VolunteerStatus) {
    setServerError(null)
    startTransition(async () => {
      const result = await updateVolunteerStatus(volunteerId, nextStatus)
      if (result.error) setServerError(result.error)
    })
  }

  return (
    <div className="space-y-3">
      {serverError && (
        <p role="alert" className="rounded bg-[var(--color-danger-subtle)] p-3 text-sm text-[var(--color-danger)]">
          {serverError}
        </p>
      )}
      <div className="flex flex-wrap gap-2">
        {allowed.map(nextStatus => (
          <button
            key={nextStatus}
            disabled={isPending}
            onClick={() => handleAction(nextStatus)}
            className="rounded bg-[var(--color-primary)] px-4 py-2 text-sm font-semibold text-[var(--color-primary-text)] hover:bg-[var(--color-primary-hover)] disabled:opacity-50"
          >
            {currentStatus === 'inactive' && nextStatus === 'active'
              ? REACTIVATE_LABEL
              : ACTION_LABEL[nextStatus]}
          </button>
        ))}
      </div>
      <p className="text-xs text-[var(--text-secondary)]">
        Estado actual: <span className="font-medium">{STATUS_LABEL[currentStatus]}</span>
      </p>
    </div>
  )
}
```

### Admin volunteer detail page

**`src/app/admin/volunteers/[id]/page.tsx`**

```typescript
import { createServerComponentClient } from '@supabase/auth-helpers-nextjs'
import { createClient } from '@supabase/supabase-js'
import { cookies } from 'next/headers'
import { redirect } from 'next/navigation'
import Link from 'next/link'
import { isAdmin } from '@/lib/auth/is-admin'
import { VolunteerStatusForm } from './VolunteerStatusForm'
import { AVAILABILITY_OPTIONS, SKILL_OPTIONS } from '@/lib/volunteers/constants'
import type { VolunteerProfile } from '@/lib/volunteers/types'

const supabaseAdmin = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!,
)

export default async function AdminVolunteerDetailPage({
  params,
}: {
  params: { id: string }
}) {
  const supabase = createServerComponentClient({ cookies })
  const {
    data: { user },
  } = await supabase.auth.getUser()
  if (!user) redirect('/login')

  const admin = await isAdmin(user.id)
  if (!admin) redirect('/')

  const { data: profile } = await supabaseAdmin
    .from('volunteer_profiles')
    .select('*')
    .eq('id', params.id)
    .single<VolunteerProfile>()

  if (!profile) redirect('/admin/volunteers')

  const availabilityLabels = AVAILABILITY_OPTIONS.filter(o =>
    profile.availability.includes(o.value),
  ).map(o => o.label)

  const skillLabels = SKILL_OPTIONS.filter(o =>
    profile.skills.includes(o.value),
  ).map(o => o.label)

  return (
    <main className="min-h-screen bg-[var(--bg-page)] py-12 px-4">
      <div className="mx-auto max-w-xl space-y-6">
        <div className="flex items-center gap-4">
          <Link
            href="/admin/volunteers"
            className="text-sm text-[var(--color-primary)] hover:underline"
          >
            ← Volver
          </Link>
          <h1 className="text-3xl font-bold text-[var(--text-primary)]">
            {profile.full_name}
          </h1>
        </div>

        <dl className="space-y-3 text-sm">
          {profile.phone && (
            <div>
              <dt className="font-medium text-[var(--text-secondary)]">Teléfono</dt>
              <dd className="text-[var(--text-primary)]">{profile.phone}</dd>
            </div>
          )}
          <div>
            <dt className="font-medium text-[var(--text-secondary)]">Disponibilidad</dt>
            <dd className="text-[var(--text-primary)]">{availabilityLabels.join(', ') || '—'}</dd>
          </div>
          <div>
            <dt className="font-medium text-[var(--text-secondary)]">Habilidades</dt>
            <dd className="text-[var(--text-primary)]">{skillLabels.join(', ') || '—'}</dd>
          </div>
          {profile.motivation && (
            <div>
              <dt className="font-medium text-[var(--text-secondary)]">Motivación</dt>
              <dd className="text-[var(--text-primary)]">{profile.motivation}</dd>
            </div>
          )}
          <div>
            <dt className="font-medium text-[var(--text-secondary)]">Horas acumuladas</dt>
            <dd className="text-[var(--text-primary)]">{profile.hours_total}</dd>
          </div>
          {profile.notes && (
            <div>
              <dt className="font-medium text-[var(--text-secondary)]">Notas internas</dt>
              <dd className="text-[var(--text-primary)]">{profile.notes}</dd>
            </div>
          )}
        </dl>

        <section>
          <h2 className="mb-3 text-lg font-semibold text-[var(--text-primary)]">
            Cambiar estado
          </h2>
          <VolunteerStatusForm
            volunteerId={profile.id}
            currentStatus={profile.status}
          />
        </section>
      </div>
    </main>
  )
}
```

### Admin volunteers list page

**`src/app/admin/volunteers/page.tsx`**

```typescript
import { createServerComponentClient } from '@supabase/auth-helpers-nextjs'
import { createClient } from '@supabase/supabase-js'
import { cookies } from 'next/headers'
import { redirect } from 'next/navigation'
import Link from 'next/link'
import { isAdmin } from '@/lib/auth/is-admin'
import type { VolunteerProfile, VolunteerStatus } from '@/lib/volunteers/types'

const supabaseAdmin = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!,
)

const STATUS_TABS: { label: string; value: VolunteerStatus | 'all' }[] = [
  { label: 'Todos', value: 'all' },
  { label: 'Pendientes', value: 'pending_review' },
  { label: 'Activos', value: 'active' },
  { label: 'Inactivos', value: 'inactive' },
  { label: 'Rechazados', value: 'rejected' },
]

export default async function AdminVolunteersPage({
  searchParams,
}: {
  searchParams: { status?: string }
}) {
  const supabase = createServerComponentClient({ cookies })
  const {
    data: { user },
  } = await supabase.auth.getUser()
  if (!user) redirect('/login')

  const admin = await isAdmin(user.id)
  if (!admin) redirect('/')

  const filterStatus = searchParams.status as VolunteerStatus | 'all' | undefined

  let query = supabaseAdmin
    .from('volunteer_profiles')
    .select('id, full_name, status, created_at')
    .order('created_at', { ascending: false })

  if (filterStatus && filterStatus !== 'all') {
    query = query.eq('status', filterStatus)
  }

  const { data: volunteers } = await query.returns<
    Pick<VolunteerProfile, 'id' | 'full_name' | 'status' | 'created_at'>[]
  >()

  const active = filterStatus ?? 'all'

  return (
    <main className="min-h-screen bg-[var(--bg-page)] py-12 px-4">
      <div className="mx-auto max-w-2xl space-y-6">
        <h1 className="text-3xl font-bold text-[var(--text-primary)]">Voluntarios</h1>

        <nav className="flex flex-wrap gap-2">
          {STATUS_TABS.map(tab => (
            <Link
              key={tab.value}
              href={tab.value === 'all' ? '/admin/volunteers' : `/admin/volunteers?status=${tab.value}`}
              className={`rounded px-3 py-1.5 text-sm font-medium ${
                active === tab.value
                  ? 'bg-[var(--color-primary)] text-[var(--color-primary-text)]'
                  : 'bg-[var(--bg-card)] text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
              }`}
            >
              {tab.label}
            </Link>
          ))}
        </nav>

        {!volunteers || volunteers.length === 0 ? (
          <p className="text-sm text-[var(--text-secondary)]">No hay voluntarios en este estado.</p>
        ) : (
          <ul className="divide-y divide-[var(--border)] rounded border border-[var(--border)] bg-[var(--bg-card)]">
            {volunteers.map(v => (
              <li key={v.id}>
                <Link
                  href={`/admin/volunteers/${v.id}`}
                  className="flex items-center justify-between px-4 py-3 hover:bg-[var(--bg-hover)]"
                >
                  <span className="font-medium text-[var(--text-primary)]">{v.full_name}</span>
                  <span className="text-xs text-[var(--text-secondary)] capitalize">
                    {v.status.replace('_', ' ')}
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </div>
    </main>
  )
}
```

### File checklist

| File | Action |
|------|--------|
| `src/lib/volunteers/types.ts` | Update — export `VolunteerStatus` type |
| `src/lib/volunteers/validate-status-transition.ts` | Create |
| `src/lib/volunteers/__tests__/validate-status-transition.test.ts` | Create |
| `src/lib/auth/is-admin.ts` | Create |
| `src/app/actions/update-volunteer-status.ts` | Create |
| `src/app/admin/volunteers/page.tsx` | Create |
| `src/app/admin/volunteers/[id]/page.tsx` | Create |
| `src/app/admin/volunteers/[id]/VolunteerStatusForm.tsx` | Create |

## Related Issues

- EPIC-5
- S01
