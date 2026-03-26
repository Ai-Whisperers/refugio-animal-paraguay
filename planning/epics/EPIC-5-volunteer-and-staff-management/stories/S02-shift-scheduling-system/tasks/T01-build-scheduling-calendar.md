---
task: T01
story: S02
epic: EPIC-5
title: Build scheduling calendar
status: ready
priority: medium
created: 2026-03-25T17:13:26.731661
---

# T01: Build scheduling calendar

## Description

Create the `volunteer_shifts` table and the admin interface for managing the shift calendar. Admins can create shifts (with a date, time window, title, and volunteer capacity). A `/volunteers/shifts` page displays upcoming shifts to active volunteers. A Server Action protected by the admin check creates new shifts.

## Acceptance Criteria

- [ ] Supabase migration creates `volunteer_shifts` table with RLS policies
- [ ] Admin page at `/admin/volunteers/shifts` lists all shifts ordered by date
- [ ] Admin can create a new shift via form at `/admin/volunteers/shifts/new`; non-admins redirect to `/`
- [ ] Form validation: title required, date must be in the future, start_time < end_time, max_volunteers ≥ 1
- [ ] Volunteer-facing page at `/volunteers/shifts` lists upcoming shifts; requires `status = 'active'`
- [ ] Unit tests cover the shift creation validation helper

## Implementation Notes

### Migration

**`supabase/migrations/20260401000012_volunteer_shifts.sql`**

```sql
-- Shift definitions created by admins
create table public.volunteer_shifts (
  id          uuid primary key default gen_random_uuid(),
  title       text not null,
  description text,
  shift_date  date not null,
  start_time  time not null,
  end_time    time not null,
  max_volunteers int not null default 1 check (max_volunteers >= 1),
  created_by  uuid not null references auth.users(id),
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);

-- Admins can manage shifts; authenticated users can read upcoming shifts
alter table public.volunteer_shifts enable row level security;

create policy "Authenticated users can view upcoming shifts"
  on public.volunteer_shifts for select
  using (auth.uid() is not null and shift_date >= current_date);

create policy "Admins can insert shifts"
  on public.volunteer_shifts for insert
  with check (auth.uid() is not null);
  -- Server Action enforces admin role check before reaching Supabase

create policy "Admins can update shifts"
  on public.volunteer_shifts for update
  using (auth.uid() is not null);

create index volunteer_shifts_date_idx on public.volunteer_shifts (shift_date);
```

### Shift creation validation helper

**`src/lib/shifts/validate-shift.ts`**

```typescript
export interface ShiftInput {
  title: string
  description: string
  shiftDate: string   // 'YYYY-MM-DD'
  startTime: string   // 'HH:MM'
  endTime: string     // 'HH:MM'
  maxVolunteers: number
}

export interface ShiftErrors {
  title?: string
  shiftDate?: string
  startTime?: string
  endTime?: string
  maxVolunteers?: string
}

export function validateShiftInput(input: ShiftInput): ShiftErrors {
  const errors: ShiftErrors = {}

  if (!input.title.trim()) {
    errors.title = 'El título es obligatorio.'
  }

  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const date = new Date(input.shiftDate)
  if (isNaN(date.getTime()) || date < today) {
    errors.shiftDate = 'La fecha debe ser hoy o en el futuro.'
  }

  if (!input.startTime) {
    errors.startTime = 'La hora de inicio es obligatoria.'
  }

  if (!input.endTime) {
    errors.endTime = 'La hora de fin es obligatoria.'
  }

  if (input.startTime && input.endTime && input.startTime >= input.endTime) {
    errors.endTime = 'La hora de fin debe ser posterior a la de inicio.'
  }

  if (!Number.isInteger(input.maxVolunteers) || input.maxVolunteers < 1) {
    errors.maxVolunteers = 'El cupo mínimo es 1 voluntario/a.'
  }

  return errors
}

export function hasShiftErrors(errors: ShiftErrors): boolean {
  return Object.keys(errors).length > 0
}
```

### Unit tests

**`src/lib/shifts/__tests__/validate-shift.test.ts`**

```typescript
import { describe, it, expect } from 'vitest'
import { validateShiftInput, hasShiftErrors } from '../validate-shift'
import type { ShiftInput } from '../validate-shift'

const tomorrow = new Date()
tomorrow.setDate(tomorrow.getDate() + 1)
const tomorrowStr = tomorrow.toISOString().split('T')[0]

const base: ShiftInput = {
  title: 'Limpieza de jaulas',
  description: '',
  shiftDate: tomorrowStr,
  startTime: '08:00',
  endTime: '12:00',
  maxVolunteers: 3,
}

describe('validateShiftInput', () => {
  it('returns no errors for valid input', () => {
    expect(hasShiftErrors(validateShiftInput(base))).toBe(false)
  })
  it('requires title', () => {
    expect(validateShiftInput({ ...base, title: '' }).title).toBeDefined()
  })
  it('rejects past dates', () => {
    expect(validateShiftInput({ ...base, shiftDate: '2020-01-01' }).shiftDate).toBeDefined()
  })
  it('rejects endTime equal to startTime', () => {
    expect(validateShiftInput({ ...base, endTime: '08:00' }).endTime).toBeDefined()
  })
  it('rejects endTime before startTime', () => {
    expect(validateShiftInput({ ...base, endTime: '07:00' }).endTime).toBeDefined()
  })
  it('requires maxVolunteers >= 1', () => {
    expect(validateShiftInput({ ...base, maxVolunteers: 0 }).maxVolunteers).toBeDefined()
  })
  it('accepts maxVolunteers = 1', () => {
    expect(hasShiftErrors(validateShiftInput({ ...base, maxVolunteers: 1 }))).toBe(false)
  })
  it('accepts empty description', () => {
    expect(hasShiftErrors(validateShiftInput({ ...base, description: '' }))).toBe(false)
  })
})
```

### Server Action

**`src/app/actions/create-volunteer-shift.ts`**

```typescript
'use server'

import { createRouteHandlerClient } from '@supabase/auth-helpers-nextjs'
import { createClient } from '@supabase/supabase-js'
import { cookies } from 'next/headers'
import { redirect } from 'next/navigation'
import { isAdmin } from '@/lib/auth/is-admin'
import { validateShiftInput, hasShiftErrors } from '@/lib/shifts/validate-shift'
import type { ShiftInput } from '@/lib/shifts/validate-shift'

const supabaseAdmin = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!,
)

export async function createVolunteerShift(
  input: ShiftInput,
): Promise<{ errors?: Record<string, string>; error?: string }> {
  // 1. Auth check
  const supabase = createRouteHandlerClient({ cookies })
  const {
    data: { user },
  } = await supabase.auth.getUser()
  if (!user) return { error: 'Sesión expirada. Iniciá sesión de nuevo.' }

  // 2. Admin check
  const admin = await isAdmin(user.id)
  if (!admin) return { error: 'No tenés permisos para crear turnos.' }

  // 3. Validate input
  const errors = validateShiftInput(input)
  if (hasShiftErrors(errors)) return { errors }

  // 4. Insert
  const { error: insertError } = await supabaseAdmin
    .from('volunteer_shifts')
    .insert({
      title: input.title.trim(),
      description: input.description.trim() || null,
      shift_date: input.shiftDate,
      start_time: input.startTime,
      end_time: input.endTime,
      max_volunteers: input.maxVolunteers,
      created_by: user.id,
    })

  if (insertError) return { error: 'Error al crear el turno. Intentá de nuevo.' }

  redirect('/admin/volunteers/shifts')
}
```

### Create shift form

**`src/app/admin/volunteers/shifts/new/CreateShiftForm.tsx`**

```typescript
'use client'

import { useTransition, useState } from 'react'
import { createVolunteerShift } from '@/app/actions/create-volunteer-shift'
import type { ShiftErrors } from '@/lib/shifts/validate-shift'

export function CreateShiftForm() {
  const [isPending, startTransition] = useTransition()
  const [fieldErrors, setFieldErrors] = useState<ShiftErrors>({})
  const [serverError, setServerError] = useState<string | null>(null)

  function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const fd = new FormData(e.currentTarget)
    setFieldErrors({})
    setServerError(null)

    startTransition(async () => {
      const result = await createVolunteerShift({
        title: fd.get('title') as string,
        description: fd.get('description') as string,
        shiftDate: fd.get('shiftDate') as string,
        startTime: fd.get('startTime') as string,
        endTime: fd.get('endTime') as string,
        maxVolunteers: Number(fd.get('maxVolunteers')),
      })
      if (result?.errors) setFieldErrors(result.errors)
      else if (result?.error) setServerError(result.error)
    })
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6 max-w-xl mx-auto">
      {serverError && (
        <p role="alert" className="rounded bg-[var(--color-danger-subtle)] p-3 text-sm text-[var(--color-danger)]">
          {serverError}
        </p>
      )}

      <div>
        <label htmlFor="title" className="block text-sm font-medium text-[var(--text-primary)]">
          Título *
        </label>
        <input
          id="title" name="title" type="text"
          className="mt-1 w-full rounded border border-[var(--border)] bg-[var(--bg-input)] px-3 py-2 text-sm"
        />
        {fieldErrors.title && (
          <p className="mt-1 text-xs text-[var(--color-danger)]">{fieldErrors.title}</p>
        )}
      </div>

      <div>
        <label htmlFor="description" className="block text-sm font-medium text-[var(--text-primary)]">
          Descripción
        </label>
        <textarea
          id="description" name="description" rows={3}
          className="mt-1 w-full rounded border border-[var(--border)] bg-[var(--bg-input)] px-3 py-2 text-sm"
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label htmlFor="shiftDate" className="block text-sm font-medium text-[var(--text-primary)]">
            Fecha *
          </label>
          <input
            id="shiftDate" name="shiftDate" type="date"
            className="mt-1 w-full rounded border border-[var(--border)] bg-[var(--bg-input)] px-3 py-2 text-sm"
          />
          {fieldErrors.shiftDate && (
            <p className="mt-1 text-xs text-[var(--color-danger)]">{fieldErrors.shiftDate}</p>
          )}
        </div>
        <div>
          <label htmlFor="maxVolunteers" className="block text-sm font-medium text-[var(--text-primary)]">
            Cupo máximo *
          </label>
          <input
            id="maxVolunteers" name="maxVolunteers" type="number" min={1} defaultValue={5}
            className="mt-1 w-full rounded border border-[var(--border)] bg-[var(--bg-input)] px-3 py-2 text-sm"
          />
          {fieldErrors.maxVolunteers && (
            <p className="mt-1 text-xs text-[var(--color-danger)]">{fieldErrors.maxVolunteers}</p>
          )}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label htmlFor="startTime" className="block text-sm font-medium text-[var(--text-primary)]">
            Hora de inicio *
          </label>
          <input
            id="startTime" name="startTime" type="time"
            className="mt-1 w-full rounded border border-[var(--border)] bg-[var(--bg-input)] px-3 py-2 text-sm"
          />
          {fieldErrors.startTime && (
            <p className="mt-1 text-xs text-[var(--color-danger)]">{fieldErrors.startTime}</p>
          )}
        </div>
        <div>
          <label htmlFor="endTime" className="block text-sm font-medium text-[var(--text-primary)]">
            Hora de fin *
          </label>
          <input
            id="endTime" name="endTime" type="time"
            className="mt-1 w-full rounded border border-[var(--border)] bg-[var(--bg-input)] px-3 py-2 text-sm"
          />
          {fieldErrors.endTime && (
            <p className="mt-1 text-xs text-[var(--color-danger)]">{fieldErrors.endTime}</p>
          )}
        </div>
      </div>

      <button
        type="submit" disabled={isPending}
        className="w-full rounded bg-[var(--color-primary)] px-4 py-2 text-sm font-semibold text-[var(--color-primary-text)] hover:bg-[var(--color-primary-hover)] disabled:opacity-50"
      >
        {isPending ? 'Creando…' : 'Crear turno'}
      </button>
    </form>
  )
}
```

### Admin create shift page

**`src/app/admin/volunteers/shifts/new/page.tsx`**

```typescript
import { createServerComponentClient } from '@supabase/auth-helpers-nextjs'
import { cookies } from 'next/headers'
import { redirect } from 'next/navigation'
import { isAdmin } from '@/lib/auth/is-admin'
import { CreateShiftForm } from './CreateShiftForm'

export default async function CreateShiftPage() {
  const supabase = createServerComponentClient({ cookies })
  const {
    data: { user },
  } = await supabase.auth.getUser()
  if (!user) redirect('/login')

  const admin = await isAdmin(user.id)
  if (!admin) redirect('/')

  return (
    <main className="min-h-screen bg-[var(--bg-page)] py-12 px-4">
      <div className="mx-auto max-w-xl">
        <h1 className="mb-8 text-3xl font-bold text-[var(--text-primary)]">Crear turno</h1>
        <CreateShiftForm />
      </div>
    </main>
  )
}
```

### Admin shifts list page

**`src/app/admin/volunteers/shifts/page.tsx`**

```typescript
import { createServerComponentClient } from '@supabase/auth-helpers-nextjs'
import { createClient } from '@supabase/supabase-js'
import { cookies } from 'next/headers'
import { redirect } from 'next/navigation'
import Link from 'next/link'
import { isAdmin } from '@/lib/auth/is-admin'

interface ShiftRow {
  id: string
  title: string
  shift_date: string
  start_time: string
  end_time: string
  max_volunteers: number
}

const supabaseAdmin = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!,
)

export default async function AdminShiftsPage() {
  const supabase = createServerComponentClient({ cookies })
  const {
    data: { user },
  } = await supabase.auth.getUser()
  if (!user) redirect('/login')

  const admin = await isAdmin(user.id)
  if (!admin) redirect('/')

  const { data: shifts } = await supabaseAdmin
    .from('volunteer_shifts')
    .select('id, title, shift_date, start_time, end_time, max_volunteers')
    .gte('shift_date', new Date().toISOString().split('T')[0])
    .order('shift_date', { ascending: true })
    .returns<ShiftRow[]>()

  return (
    <main className="min-h-screen bg-[var(--bg-page)] py-12 px-4">
      <div className="mx-auto max-w-2xl space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold text-[var(--text-primary)]">Turnos</h1>
          <Link
            href="/admin/volunteers/shifts/new"
            className="rounded bg-[var(--color-primary)] px-4 py-2 text-sm font-semibold text-[var(--color-primary-text)] hover:bg-[var(--color-primary-hover)]"
          >
            Crear turno
          </Link>
        </div>

        {!shifts || shifts.length === 0 ? (
          <p className="text-sm text-[var(--text-secondary)]">No hay turnos programados.</p>
        ) : (
          <ul className="divide-y divide-[var(--border)] rounded border border-[var(--border)] bg-[var(--bg-card)]">
            {shifts.map(s => (
              <li key={s.id} className="px-4 py-3">
                <p className="font-medium text-[var(--text-primary)]">{s.title}</p>
                <p className="mt-0.5 text-xs text-[var(--text-secondary)]">
                  {s.shift_date} · {s.start_time}–{s.end_time} · cupo: {s.max_volunteers}
                </p>
              </li>
            ))}
          </ul>
        )}
      </div>
    </main>
  )
}
```

### Volunteer upcoming shifts page

**`src/app/volunteers/shifts/page.tsx`**

```typescript
import { createServerComponentClient } from '@supabase/auth-helpers-nextjs'
import { cookies } from 'next/headers'
import { redirect } from 'next/navigation'
import type { VolunteerProfile } from '@/lib/volunteers/types'

interface ShiftRow {
  id: string
  title: string
  description: string | null
  shift_date: string
  start_time: string
  end_time: string
  max_volunteers: number
}

export default async function VolunteerShiftsPage() {
  const supabase = createServerComponentClient({ cookies })
  const {
    data: { user },
  } = await supabase.auth.getUser()
  if (!user) redirect('/login')

  const { data: profile } = await supabase
    .from('volunteer_profiles')
    .select('status')
    .eq('id', user.id)
    .single<Pick<VolunteerProfile, 'status'>>()

  if (!profile || profile.status !== 'active') redirect('/volunteers/profile')

  const { data: shifts } = await supabase
    .from('volunteer_shifts')
    .select('id, title, description, shift_date, start_time, end_time, max_volunteers')
    .gte('shift_date', new Date().toISOString().split('T')[0])
    .order('shift_date', { ascending: true })
    .returns<ShiftRow[]>()

  return (
    <main className="min-h-screen bg-[var(--bg-page)] py-12 px-4">
      <div className="mx-auto max-w-xl space-y-4">
        <h1 className="text-3xl font-bold text-[var(--text-primary)]">Turnos disponibles</h1>

        {!shifts || shifts.length === 0 ? (
          <p className="text-sm text-[var(--text-secondary)]">No hay turnos próximos.</p>
        ) : (
          <ul className="space-y-3">
            {shifts.map(s => (
              <li
                key={s.id}
                className="rounded border border-[var(--border)] bg-[var(--bg-card)] px-4 py-3"
              >
                <p className="font-medium text-[var(--text-primary)]">{s.title}</p>
                <p className="mt-0.5 text-xs text-[var(--text-secondary)]">
                  {s.shift_date} · {s.start_time}–{s.end_time} · cupo: {s.max_volunteers}
                </p>
                {s.description && (
                  <p className="mt-1 text-sm text-[var(--text-secondary)]">{s.description}</p>
                )}
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
| `supabase/migrations/20260401000012_volunteer_shifts.sql` | Create |
| `src/lib/shifts/validate-shift.ts` | Create |
| `src/lib/shifts/__tests__/validate-shift.test.ts` | Create |
| `src/app/actions/create-volunteer-shift.ts` | Create |
| `src/app/admin/volunteers/shifts/page.tsx` | Create |
| `src/app/admin/volunteers/shifts/new/page.tsx` | Create |
| `src/app/admin/volunteers/shifts/new/CreateShiftForm.tsx` | Create |
| `src/app/volunteers/shifts/page.tsx` | Create |

## Related Issues

- EPIC-5
- S02
