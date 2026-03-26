---
task: T02
story: S02
epic: EPIC-5
title: Implement shift assignment
status: ready
priority: medium
created: 2026-03-25T17:13:26.731720
---

# T02: Implement shift assignment

## Description

Allow active volunteers to sign up for and cancel upcoming shifts. Admins can see who is assigned to each shift. Enforces capacity limits (max volunteers per shift) and prevents duplicate sign-ups.

## Acceptance Criteria

- [ ] Active volunteers can sign up for upcoming shifts (one click)
- [ ] Sign-up is blocked if shift is at capacity
- [ ] Sign-up is blocked if volunteer is already registered
- [ ] Sign-up is blocked if volunteer status is not `active`
- [ ] Volunteers can cancel their own sign-up
- [ ] Admin shift list shows current headcount vs. capacity per shift
- [ ] Admin shift detail shows list of assigned volunteers by name
- [ ] Validation logic is unit-tested with vitest

## Implementation Notes

### Tech Stack Constraints

- **Supabase only** — PostgreSQL + Auth + Storage. No Prisma, no ORM, no Redis.
- **Next.js 14 App Router** — Server Components by default; `'use client'` only for interactive elements.
- **Server Actions** (`'use server'`) for all mutations.
- **Tailwind CSS 3.4.19 pinned** — use CSS vars (`bg-[var(--bg-card)]`), never hardcode colors.
- `createRouteHandlerClient` (with cookies) for Server Actions auth; `createServerComponentClient` for Server Component reads.
- `supabaseAdmin` (`createClient(URL, SERVICE_ROLE_KEY)`) for privileged reads and writes that bypass RLS.
- Admin authorization via `isAdmin(userId)` (queries `user_roles` table — defined in EPIC-5/S01/T03).

---

### Step 1 — Migration: `shift_assignments` table

**File**: `supabase/migrations/20260401000013_shift_assignments.sql`

```sql
-- shift_assignments: tracks which volunteer is signed up for which shift
create table public.shift_assignments (
  id uuid primary key default gen_random_uuid(),
  shift_id uuid not null references public.volunteer_shifts(id) on delete cascade,
  volunteer_id uuid not null references auth.users(id) on delete cascade,
  assigned_at timestamptz not null default now(),

  -- one volunteer can only sign up once per shift
  unique (shift_id, volunteer_id)
);

-- read: any authenticated user can see who is assigned to shifts
-- write: enforced at application layer (Server Action checks active status + capacity)
alter table public.shift_assignments enable row level security;

create policy "Authenticated users can read shift assignments"
  on public.shift_assignments
  for select
  to authenticated
  using (true);

-- no insert/update/delete RLS policies — writes go through supabaseAdmin
-- after application-layer validation (active volunteer, capacity, no duplicate)

-- index for fast lookup: all assignments for a shift
create index shift_assignments_shift_id_idx on public.shift_assignments(shift_id);

-- index for fast lookup: all shifts a volunteer is signed up for
create index shift_assignments_volunteer_id_idx on public.shift_assignments(volunteer_id);
```

**Why no insert RLS?**
Writes use `supabaseAdmin` (service role) after Server Action validates: (1) user is authenticated, (2) volunteer profile `status = 'active'`, (3) shift is not full, (4) no existing assignment. Service role bypasses RLS; application layer IS the authorization.

---

### Step 2 — Validation helper

**File**: `src/lib/shifts/validate-assignment.ts`

```typescript
export type AssignmentError =
  | 'not_active_volunteer'
  | 'shift_full'
  | 'already_assigned'
  | 'shift_in_past'

export interface AssignmentValidationResult {
  valid: boolean
  error?: AssignmentError
  message?: string
}

const ERROR_MESSAGES: Record<AssignmentError, string> = {
  not_active_volunteer: 'Solo voluntarios activos pueden registrarse para turnos.',
  shift_full: 'Este turno ya está completo. No hay lugares disponibles.',
  already_assigned: 'Ya estás registrado para este turno.',
  shift_in_past: 'No es posible registrarse para turnos pasados.',
}

export function getAssignmentErrorMessage(error: AssignmentError): string {
  return ERROR_MESSAGES[error]
}

export interface AssignmentCheckParams {
  volunteerStatus: string
  shiftDate: string        // ISO date string: '2026-04-15'
  currentAssignments: number
  maxVolunteers: number
  isAlreadyAssigned: boolean
}

export function validateAssignment(params: AssignmentCheckParams): AssignmentValidationResult {
  const {
    volunteerStatus,
    shiftDate,
    currentAssignments,
    maxVolunteers,
    isAlreadyAssigned,
  } = params

  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const shift = new Date(shiftDate)
  shift.setHours(0, 0, 0, 0)

  if (shift < today) {
    return { valid: false, error: 'shift_in_past', message: ERROR_MESSAGES.shift_in_past }
  }

  if (volunteerStatus !== 'active') {
    return { valid: false, error: 'not_active_volunteer', message: ERROR_MESSAGES.not_active_volunteer }
  }

  if (isAlreadyAssigned) {
    return { valid: false, error: 'already_assigned', message: ERROR_MESSAGES.already_assigned }
  }

  if (currentAssignments >= maxVolunteers) {
    return { valid: false, error: 'shift_full', message: ERROR_MESSAGES.shift_full }
  }

  return { valid: true }
}
```

---

### Step 3 — Unit tests for validation

**File**: `src/lib/shifts/__tests__/validate-assignment.test.ts`

```typescript
import { describe, it, expect } from 'vitest'
import { validateAssignment } from '../validate-assignment'

// Use a date guaranteed to be in the past/future relative to test run
const tomorrowStr = (() => {
  const d = new Date()
  d.setDate(d.getDate() + 1)
  return d.toISOString().split('T')[0]
})()

const yesterdayStr = (() => {
  const d = new Date()
  d.setDate(d.getDate() - 1)
  return d.toISOString().split('T')[0]
})()

const BASE_PARAMS = {
  volunteerStatus: 'active',
  shiftDate: tomorrowStr,
  currentAssignments: 0,
  maxVolunteers: 5,
  isAlreadyAssigned: false,
}

describe('validateAssignment', () => {
  it('returns valid for an eligible volunteer on an upcoming shift', () => {
    expect(validateAssignment(BASE_PARAMS)).toEqual({ valid: true })
  })

  it('blocks sign-up for a past shift', () => {
    const result = validateAssignment({ ...BASE_PARAMS, shiftDate: yesterdayStr })
    expect(result.valid).toBe(false)
    expect(result.error).toBe('shift_in_past')
  })

  it('blocks sign-up when volunteer status is pending_review', () => {
    const result = validateAssignment({ ...BASE_PARAMS, volunteerStatus: 'pending_review' })
    expect(result.valid).toBe(false)
    expect(result.error).toBe('not_active_volunteer')
  })

  it('blocks sign-up when volunteer status is inactive', () => {
    const result = validateAssignment({ ...BASE_PARAMS, volunteerStatus: 'inactive' })
    expect(result.valid).toBe(false)
    expect(result.error).toBe('not_active_volunteer')
  })

  it('blocks sign-up when volunteer is already assigned', () => {
    const result = validateAssignment({ ...BASE_PARAMS, isAlreadyAssigned: true })
    expect(result.valid).toBe(false)
    expect(result.error).toBe('already_assigned')
  })

  it('blocks sign-up when shift is at capacity', () => {
    const result = validateAssignment({ ...BASE_PARAMS, currentAssignments: 5, maxVolunteers: 5 })
    expect(result.valid).toBe(false)
    expect(result.error).toBe('shift_full')
  })

  it('allows sign-up when shift has exactly one spot left', () => {
    const result = validateAssignment({ ...BASE_PARAMS, currentAssignments: 4, maxVolunteers: 5 })
    expect(result.valid).toBe(true)
  })

  it('returns a Spanish error message for shift_full', () => {
    const result = validateAssignment({ ...BASE_PARAMS, currentAssignments: 3, maxVolunteers: 3 })
    expect(result.message).toContain('completo')
  })

  it('returns a Spanish error message for not_active_volunteer', () => {
    const result = validateAssignment({ ...BASE_PARAMS, volunteerStatus: 'rejected' })
    expect(result.message).toContain('activos')
  })
})
```

---

### Step 4 — Server Actions

**File**: `src/app/actions/shift-assignment-actions.ts`

```typescript
'use server'

import { createRouteHandlerClient } from '@supabase/auth-helpers-nextjs'
import { cookies } from 'next/headers'
import { revalidatePath } from 'next/cache'
import { supabaseAdmin } from '@/lib/supabase/admin'
import { validateAssignment } from '@/lib/shifts/validate-assignment'

// ─── Sign up for a shift ─────────────────────────────────────────────────────

export async function signUpForShift(
  shiftId: string
): Promise<{ error?: string }> {
  const supabase = createRouteHandlerClient({ cookies })
  const { data: { user } } = await supabase.auth.getUser()

  if (!user) {
    return { error: 'No autenticado.' }
  }

  // 1. Fetch volunteer profile status
  const { data: profile, error: profileErr } = await supabaseAdmin
    .from('volunteer_profiles')
    .select('status')
    .eq('id', user.id)
    .maybeSingle()

  if (profileErr || !profile) {
    return { error: 'No se encontró tu perfil de voluntario.' }
  }

  // 2. Fetch shift details (date, capacity, current headcount)
  const { data: shift, error: shiftErr } = await supabaseAdmin
    .from('volunteer_shifts')
    .select(`
      id,
      shift_date,
      max_volunteers,
      shift_assignments(count)
    `)
    .eq('id', shiftId)
    .maybeSingle()

  if (shiftErr || !shift) {
    return { error: 'Turno no encontrado.' }
  }

  // shift_assignments(count) returns [{ count: N }]
  const currentAssignments = (shift.shift_assignments as { count: number }[])[0]?.count ?? 0

  // 3. Check for existing assignment
  const { data: existing } = await supabaseAdmin
    .from('shift_assignments')
    .select('id')
    .eq('shift_id', shiftId)
    .eq('volunteer_id', user.id)
    .maybeSingle()

  // 4. Validate
  const validation = validateAssignment({
    volunteerStatus: profile.status,
    shiftDate: shift.shift_date,
    currentAssignments,
    maxVolunteers: shift.max_volunteers,
    isAlreadyAssigned: existing !== null,
  })

  if (!validation.valid) {
    return { error: validation.message ?? 'No se puede registrar para este turno.' }
  }

  // 5. Insert assignment
  const { error: insertErr } = await supabaseAdmin
    .from('shift_assignments')
    .insert({ shift_id: shiftId, volunteer_id: user.id })

  if (insertErr) {
    // Handle unique constraint violation (race condition)
    if (insertErr.code === '23505') {
      return { error: 'Ya estás registrado para este turno.' }
    }
    return { error: 'Error al registrarse. Intenta nuevamente.' }
  }

  revalidatePath('/volunteers/shifts')
  revalidatePath(`/volunteers/shifts/${shiftId}`)
  revalidatePath('/admin/volunteers/shifts')
  return {}
}

// ─── Cancel shift sign-up ─────────────────────────────────────────────────────

export async function cancelShiftSignup(
  shiftId: string
): Promise<{ error?: string }> {
  const supabase = createRouteHandlerClient({ cookies })
  const { data: { user } } = await supabase.auth.getUser()

  if (!user) {
    return { error: 'No autenticado.' }
  }

  // Only delete the assignment that belongs to the current user
  const { error: deleteErr } = await supabaseAdmin
    .from('shift_assignments')
    .delete()
    .eq('shift_id', shiftId)
    .eq('volunteer_id', user.id)

  if (deleteErr) {
    return { error: 'Error al cancelar el turno. Intenta nuevamente.' }
  }

  revalidatePath('/volunteers/shifts')
  revalidatePath(`/volunteers/shifts/${shiftId}`)
  revalidatePath('/admin/volunteers/shifts')
  return {}
}
```

**Notes**:
- `supabase.auth.getUser()` is called first (auth boundary). All DB reads/writes use `supabaseAdmin` (service role) after auth is confirmed.
- The unique constraint on `(shift_id, volunteer_id)` acts as a final safety net against race conditions; the `23505` error code is handled explicitly.
- `cancelShiftSignup` uses `.eq('volunteer_id', user.id)` as a scoped delete — a volunteer can never cancel another volunteer's sign-up, even via direct Server Action invocation.

---

### Step 5 — Volunteer shifts page (updated with sign-up/cancel)

**File**: `src/app/volunteers/shifts/page.tsx`

This replaces the read-only version created in T01.

```typescript
import { createServerComponentClient } from '@supabase/auth-helpers-nextjs'
import { cookies } from 'next/headers'
import { redirect } from 'next/navigation'
import { supabaseAdmin } from '@/lib/supabase/admin'
import ShiftSignupButton from './ShiftSignupButton'

interface ShiftRow {
  id: string
  title: string
  description: string | null
  shift_date: string
  start_time: string
  end_time: string
  max_volunteers: number
  assignmentCount: number
  isAssigned: boolean
}

export default async function VolunteerShiftsPage() {
  const supabase = createServerComponentClient({ cookies })
  const { data: { user } } = await supabase.auth.getUser()

  if (!user) redirect('/auth/login')

  // Check volunteer is active
  const { data: profile } = await supabaseAdmin
    .from('volunteer_profiles')
    .select('status')
    .eq('id', user.id)
    .maybeSingle()

  if (!profile || profile.status !== 'active') {
    redirect('/volunteers/profile')
  }

  // Fetch upcoming shifts with assignment counts + whether current user is signed up
  const today = new Date().toISOString().split('T')[0]

  const { data: shifts } = await supabaseAdmin
    .from('volunteer_shifts')
    .select(`
      id,
      title,
      description,
      shift_date,
      start_time,
      end_time,
      max_volunteers,
      shift_assignments(count),
      my_assignment:shift_assignments!inner(volunteer_id)
    `)
    .gte('shift_date', today)
    .order('shift_date', { ascending: true })

  // Note: The above join for my_assignment uses a PostgREST trick.
  // A simpler, more readable approach is two queries:

  const { data: rawShifts } = await supabaseAdmin
    .from('volunteer_shifts')
    .select('id, title, description, shift_date, start_time, end_time, max_volunteers')
    .gte('shift_date', today)
    .order('shift_date', { ascending: true })

  const { data: myAssignments } = await supabaseAdmin
    .from('shift_assignments')
    .select('shift_id')
    .eq('volunteer_id', user.id)

  const assignedShiftIds = new Set((myAssignments ?? []).map((a) => a.shift_id))

  // Get counts per shift
  const { data: counts } = await supabaseAdmin
    .from('shift_assignments')
    .select('shift_id')

  const countMap = new Map<string, number>()
  for (const row of counts ?? []) {
    countMap.set(row.shift_id, (countMap.get(row.shift_id) ?? 0) + 1)
  }

  const shiftRows: ShiftRow[] = (rawShifts ?? []).map((s) => ({
    ...s,
    assignmentCount: countMap.get(s.id) ?? 0,
    isAssigned: assignedShiftIds.has(s.id),
  }))

  return (
    <main className="max-w-3xl mx-auto py-8 px-4">
      <h1 className="text-2xl font-bold text-[var(--text-primary)] mb-6">
        Turnos disponibles
      </h1>

      {shiftRows.length === 0 && (
        <p className="text-[var(--text-secondary)]">
          No hay turnos próximos disponibles.
        </p>
      )}

      <ul className="space-y-4">
        {shiftRows.map((shift) => {
          const spotsLeft = shift.max_volunteers - shift.assignmentCount
          const isFull = spotsLeft <= 0

          return (
            <li
              key={shift.id}
              className="bg-[var(--bg-card)] border border-[var(--border)] rounded-lg p-4"
            >
              <div className="flex items-start justify-between gap-4">
                <div>
                  <h2 className="font-semibold text-[var(--text-primary)]">
                    {shift.title}
                  </h2>
                  {shift.description && (
                    <p className="text-sm text-[var(--text-secondary)] mt-1">
                      {shift.description}
                    </p>
                  )}
                  <p className="text-sm text-[var(--text-secondary)] mt-2">
                    {shift.shift_date} · {shift.start_time.slice(0, 5)}–{shift.end_time.slice(0, 5)}
                  </p>
                  <p className="text-sm mt-1">
                    <span
                      className={
                        isFull
                          ? 'text-[var(--color-error)]'
                          : 'text-[var(--text-secondary)]'
                      }
                    >
                      {isFull
                        ? 'Completo'
                        : `${spotsLeft} lugar${spotsLeft === 1 ? '' : 'es'} disponible${spotsLeft === 1 ? '' : 's'}`}
                    </span>
                  </p>
                </div>

                <ShiftSignupButton
                  shiftId={shift.id}
                  isAssigned={shift.isAssigned}
                  isFull={isFull && !shift.isAssigned}
                />
              </div>
            </li>
          )
        })}
      </ul>
    </main>
  )
}
```

---

### Step 6 — `ShiftSignupButton` client component

**File**: `src/app/volunteers/shifts/ShiftSignupButton.tsx`

```typescript
'use client'

import { useTransition } from 'react'
import { signUpForShift, cancelShiftSignup } from '@/app/actions/shift-assignment-actions'

interface Props {
  shiftId: string
  isAssigned: boolean
  isFull: boolean
}

export default function ShiftSignupButton({ shiftId, isAssigned, isFull }: Props) {
  const [isPending, startTransition] = useTransition()
  const [error, setError] = useState<string | null>(null)

  // useState needs the import — include it
  // Note: we need useState imported alongside useTransition
  // Add: import { useState, useTransition } from 'react'

  function handleClick() {
    setError(null)
    startTransition(async () => {
      const result = isAssigned
        ? await cancelShiftSignup(shiftId)
        : await signUpForShift(shiftId)

      if (result.error) {
        setError(result.error)
      }
    })
  }

  if (isFull) {
    return (
      <span className="text-sm text-[var(--text-disabled)] italic">
        Sin lugares
      </span>
    )
  }

  return (
    <div className="flex flex-col items-end gap-1">
      <button
        onClick={handleClick}
        disabled={isPending}
        className={
          isAssigned
            ? 'px-3 py-1.5 text-sm rounded border border-[var(--border)] text-[var(--text-secondary)] hover:bg-[var(--bg-hover)] disabled:opacity-50'
            : 'px-3 py-1.5 text-sm rounded bg-[var(--color-primary)] text-white hover:bg-[var(--color-primary-hover)] disabled:opacity-50'
        }
      >
        {isPending
          ? isAssigned ? 'Cancelando…' : 'Registrando…'
          : isAssigned ? 'Cancelar' : 'Registrarme'}
      </button>
      {error && (
        <p className="text-xs text-[var(--color-error)] max-w-[180px] text-right">
          {error}
        </p>
      )}
    </div>
  )
}
```

**Corrected import** (the above inline note needs to be applied in the actual file):

```typescript
'use client'

import { useState, useTransition } from 'react'
// ... rest of component
```

---

### Step 7 — Admin shift detail with assigned volunteers

**File**: `src/app/admin/volunteers/shifts/[id]/page.tsx`

```typescript
import { createServerComponentClient } from '@supabase/auth-helpers-nextjs'
import { cookies } from 'next/headers'
import { redirect, notFound } from 'next/navigation'
import { isAdmin } from '@/lib/auth/is-admin'
import { supabaseAdmin } from '@/lib/supabase/admin'

interface Props {
  params: { id: string }
}

export default async function AdminShiftDetailPage({ params }: Props) {
  const supabase = createServerComponentClient({ cookies })
  const { data: { user } } = await supabase.auth.getUser()

  if (!user) redirect('/auth/login')
  if (!(await isAdmin(user.id))) redirect('/dashboard')

  // Fetch shift
  const { data: shift } = await supabaseAdmin
    .from('volunteer_shifts')
    .select('id, title, description, shift_date, start_time, end_time, max_volunteers')
    .eq('id', params.id)
    .maybeSingle()

  if (!shift) notFound()

  // Fetch assigned volunteers with their profile names
  // shift_assignments → volunteer_profiles (joined on volunteer_id = volunteer_profiles.id)
  const { data: assignments } = await supabaseAdmin
    .from('shift_assignments')
    .select(`
      id,
      assigned_at,
      volunteer:volunteer_profiles(id, full_name, phone)
    `)
    .eq('shift_id', params.id)
    .order('assigned_at', { ascending: true })

  const assignedCount = assignments?.length ?? 0
  const spotsLeft = shift.max_volunteers - assignedCount

  return (
    <main className="max-w-2xl mx-auto py-8 px-4">
      <div className="mb-2">
        <a
          href="/admin/volunteers/shifts"
          className="text-sm text-[var(--color-primary)] hover:underline"
        >
          ← Volver a turnos
        </a>
      </div>

      <h1 className="text-2xl font-bold text-[var(--text-primary)] mb-1">
        {shift.title}
      </h1>

      {shift.description && (
        <p className="text-[var(--text-secondary)] mb-4">{shift.description}</p>
      )}

      <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm mb-6">
        <dt className="text-[var(--text-secondary)]">Fecha</dt>
        <dd className="text-[var(--text-primary)]">{shift.shift_date}</dd>

        <dt className="text-[var(--text-secondary)]">Horario</dt>
        <dd className="text-[var(--text-primary)]">
          {shift.start_time.slice(0, 5)}–{shift.end_time.slice(0, 5)}
        </dd>

        <dt className="text-[var(--text-secondary)]">Capacidad</dt>
        <dd className="text-[var(--text-primary)]">
          {assignedCount} / {shift.max_volunteers}
          {spotsLeft > 0 ? (
            <span className="ml-2 text-[var(--text-secondary)]">
              ({spotsLeft} lugar{spotsLeft === 1 ? '' : 'es'} libre{spotsLeft === 1 ? '' : 's'})
            </span>
          ) : (
            <span className="ml-2 text-[var(--color-error)]">(completo)</span>
          )}
        </dd>
      </dl>

      <h2 className="text-lg font-semibold text-[var(--text-primary)] mb-3">
        Voluntarios registrados
      </h2>

      {assignedCount === 0 ? (
        <p className="text-[var(--text-secondary)] text-sm">
          Ningún voluntario registrado aún.
        </p>
      ) : (
        <ul className="divide-y divide-[var(--border)]">
          {(assignments ?? []).map((a) => {
            const v = a.volunteer as { id: string; full_name: string; phone: string | null }
            return (
              <li key={a.id} className="py-3 flex items-center justify-between">
                <div>
                  <a
                    href={`/admin/volunteers/${v.id}`}
                    className="font-medium text-[var(--text-primary)] hover:text-[var(--color-primary)]"
                  >
                    {v.full_name}
                  </a>
                  {v.phone && (
                    <p className="text-sm text-[var(--text-secondary)]">{v.phone}</p>
                  )}
                </div>
                <span className="text-xs text-[var(--text-secondary)]">
                  {new Date(a.assigned_at).toLocaleDateString('es-PY')}
                </span>
              </li>
            )
          })}
        </ul>
      )}
    </main>
  )
}
```

---

### Step 8 — Updated admin shifts list (with headcount)

**File**: `src/app/admin/volunteers/shifts/page.tsx`

Extend the T01 version to show `assigned / max_volunteers` per shift and link to detail page.

```typescript
import { createServerComponentClient } from '@supabase/auth-helpers-nextjs'
import { cookies } from 'next/headers'
import { redirect } from 'next/navigation'
import { isAdmin } from '@/lib/auth/is-admin'
import { supabaseAdmin } from '@/lib/supabase/admin'

export default async function AdminShiftsPage() {
  const supabase = createServerComponentClient({ cookies })
  const { data: { user } } = await supabase.auth.getUser()

  if (!user) redirect('/auth/login')
  if (!(await isAdmin(user.id))) redirect('/dashboard')

  const today = new Date().toISOString().split('T')[0]

  const { data: shifts } = await supabaseAdmin
    .from('volunteer_shifts')
    .select('id, title, shift_date, start_time, end_time, max_volunteers')
    .gte('shift_date', today)
    .order('shift_date', { ascending: true })

  // Count assignments per shift
  const { data: assignmentCounts } = await supabaseAdmin
    .from('shift_assignments')
    .select('shift_id')

  const countMap = new Map<string, number>()
  for (const row of assignmentCounts ?? []) {
    countMap.set(row.shift_id, (countMap.get(row.shift_id) ?? 0) + 1)
  }

  return (
    <main className="max-w-3xl mx-auto py-8 px-4">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-[var(--text-primary)]">Turnos</h1>
        <a
          href="/admin/volunteers/shifts/new"
          className="px-4 py-2 text-sm rounded bg-[var(--color-primary)] text-white hover:bg-[var(--color-primary-hover)]"
        >
          Crear turno
        </a>
      </div>

      {(shifts ?? []).length === 0 && (
        <p className="text-[var(--text-secondary)]">No hay turnos próximos.</p>
      )}

      <ul className="divide-y divide-[var(--border)]">
        {(shifts ?? []).map((shift) => {
          const assigned = countMap.get(shift.id) ?? 0
          const isFull = assigned >= shift.max_volunteers

          return (
            <li key={shift.id} className="py-4">
              <a
                href={`/admin/volunteers/shifts/${shift.id}`}
                className="flex items-center justify-between group"
              >
                <div>
                  <span className="font-medium text-[var(--text-primary)] group-hover:text-[var(--color-primary)]">
                    {shift.title}
                  </span>
                  <p className="text-sm text-[var(--text-secondary)] mt-0.5">
                    {shift.shift_date} · {shift.start_time.slice(0, 5)}–{shift.end_time.slice(0, 5)}
                  </p>
                </div>
                <span
                  className={`text-sm font-medium ${
                    isFull ? 'text-[var(--color-error)]' : 'text-[var(--text-secondary)]'
                  }`}
                >
                  {assigned}/{shift.max_volunteers}
                  {isFull ? ' (lleno)' : ''}
                </span>
              </a>
            </li>
          )
        })}
      </ul>
    </main>
  )
}
```

---

### Data flow summary

```
Volunteer clicks "Registrarme"
  → ShiftSignupButton (client, useTransition)
  → signUpForShift(shiftId) Server Action
      → supabase.auth.getUser()           [auth boundary]
      → supabaseAdmin: fetch volunteer_profiles.status
      → supabaseAdmin: fetch volunteer_shifts + count
      → supabaseAdmin: check existing shift_assignment
      → validateAssignment()              [pure validation]
      → supabaseAdmin: INSERT shift_assignments
      → revalidatePath('/volunteers/shifts')
  → UI re-renders with new server data

Volunteer clicks "Cancelar"
  → cancelShiftSignup(shiftId) Server Action
      → supabase.auth.getUser()
      → supabaseAdmin: DELETE WHERE shift_id=? AND volunteer_id=user.id
      → revalidatePath('/volunteers/shifts')
  → UI re-renders
```

---

### Files to create

| File | Action |
|------|--------|
| `supabase/migrations/20260401000013_shift_assignments.sql` | CREATE |
| `src/lib/shifts/validate-assignment.ts` | CREATE |
| `src/lib/shifts/__tests__/validate-assignment.test.ts` | CREATE |
| `src/app/actions/shift-assignment-actions.ts` | CREATE |
| `src/app/volunteers/shifts/ShiftSignupButton.tsx` | CREATE |
| `src/app/volunteers/shifts/page.tsx` | UPDATE (replace T01 version) |
| `src/app/admin/volunteers/shifts/[id]/page.tsx` | CREATE |
| `src/app/admin/volunteers/shifts/page.tsx` | UPDATE (add headcount column) |

## Related Issues

- EPIC-5
- S02
- Depends on: T01 (volunteer_shifts table, isAdmin helper)
- Depends on: S01/T03 (volunteer_profiles.status, user_roles table)
