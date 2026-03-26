---
task: T01
story: S04
epic: EPIC-5
title: Implement hour tracking
status: ready
priority: medium
created: 2026-03-25T17:13:26.732180
---

# T01: Implement hour tracking

## Description

Track volunteer hours contributed to the shelter. Hours are logged automatically when a shift is completed (shift_date has passed and the volunteer was assigned) and can also be entered manually by admins. The running total is denormalized onto `volunteer_profiles.hours_total` for fast dashboard reads.

## Acceptance Criteria

- [ ] `volunteer_hours` table stores per-entry hour records (shift-based and manual)
- [ ] Admin can manually log hours for any active volunteer
- [ ] Hours total on `volunteer_profiles` stays accurate after any insert
- [ ] Validation rejects: negative hours, hours > 24 per entry, future dates
- [ ] Admin can view a volunteer's full hour log from the detail page
- [ ] All data served via Server Components (no client-side fetching)
- [ ] Unit tests cover hour validation logic

## Implementation Notes

### Tech Stack Constraints

- **Supabase only** — No Prisma, no ORM, no Redis.
- **Next.js 14 App Router** — Server Components; Server Actions for mutations.
- **Tailwind CSS 3.4.19 pinned** — CSS vars only.
- `supabaseAdmin` for admin writes; `createServerComponentClient` with RLS for reads.
- Hours total kept in sync via PostgreSQL trigger (no application-layer race condition).

---

### Step 1 — Database migration

**File**: `supabase/migrations/20260401000015_volunteer_hours.sql`

```sql
-- Volunteer hour log table
create table public.volunteer_hours (
  id           uuid        primary key default gen_random_uuid(),
  volunteer_id uuid        not null references auth.users(id) on delete cascade,
  hours        numeric(5,2) not null check (hours > 0 and hours <= 24),
  logged_date  date        not null,
  notes        text,
  source       text        not null check (source in ('manual', 'shift')),
  shift_id     uuid        references public.volunteer_shifts(id) on delete set null,
  logged_by    uuid        not null references auth.users(id),
  created_at   timestamptz not null default now()
);

-- Index for fast per-volunteer lookups
create index volunteer_hours_volunteer_id_idx
  on public.volunteer_hours (volunteer_id, logged_date desc);

-- Unique constraint: one shift entry per volunteer (prevents double-logging)
create unique index volunteer_hours_shift_unique
  on public.volunteer_hours (volunteer_id, shift_id)
  where shift_id is not null;

-- RLS
alter table public.volunteer_hours enable row level security;

-- Volunteers can read their own hours
create policy "Volunteers can read own hours"
  on public.volunteer_hours for select
  to authenticated
  using (volunteer_id = auth.uid());

-- Admins read all via supabaseAdmin (bypasses RLS)

-- Trigger: keep hours_total in sync on volunteer_profiles
create or replace function public.sync_volunteer_hours_total()
returns trigger
language plpgsql
security definer
as $$
begin
  update public.volunteer_profiles
  set hours_total = (
    select coalesce(sum(hours), 0)
    from public.volunteer_hours
    where volunteer_id = coalesce(new.volunteer_id, old.volunteer_id)
  )
  where id = coalesce(new.volunteer_id, old.volunteer_id);

  return coalesce(new, old);
end;
$$;

create trigger trg_sync_volunteer_hours_total
  after insert or update or delete
  on public.volunteer_hours
  for each row
  execute function public.sync_volunteer_hours_total();
```

---

### Step 2 — Validation helpers

**File**: `src/lib/hours/validate-hour-entry.ts`

```typescript
export interface HourEntryInput {
  volunteer_id: string
  hours: number
  logged_date: string  // 'YYYY-MM-DD'
  notes?: string
  source: 'manual' | 'shift'
  shift_id?: string
}

export interface HourEntryErrors {
  hours?: string
  logged_date?: string
  volunteer_id?: string
}

const MAX_HOURS_PER_ENTRY = 24
const MIN_HOURS = 0.25  // 15 minutes minimum

export function validateHourEntry(input: HourEntryInput): HourEntryErrors {
  const errors: HourEntryErrors = {}

  // Hours must be positive and within daily maximum
  if (isNaN(input.hours) || input.hours < MIN_HOURS) {
    errors.hours = `Las horas deben ser al menos ${MIN_HOURS} (15 minutos)`
  } else if (input.hours > MAX_HOURS_PER_ENTRY) {
    errors.hours = `Las horas no pueden superar ${MAX_HOURS_PER_ENTRY} por entrada`
  }

  // Date must not be in the future
  const today = new Date().toISOString().split('T')[0]
  if (!input.logged_date) {
    errors.logged_date = 'La fecha es requerida'
  } else if (input.logged_date > today) {
    errors.logged_date = 'No se pueden registrar horas en el futuro'
  }

  // Volunteer must be specified
  if (!input.volunteer_id) {
    errors.volunteer_id = 'El voluntario es requerido'
  }

  return errors
}

export function hasHourErrors(errors: HourEntryErrors): boolean {
  return Object.values(errors).some(Boolean)
}
```

---

### Step 3 — Unit tests

**File**: `src/lib/hours/__tests__/validate-hour-entry.test.ts`

```typescript
import { describe, it, expect } from 'vitest'
import { validateHourEntry, hasHourErrors } from '../validate-hour-entry'

const TODAY = new Date().toISOString().split('T')[0]
const YESTERDAY = new Date(Date.now() - 86400000).toISOString().split('T')[0]

const validInput = {
  volunteer_id: 'uuid-1',
  hours: 4,
  logged_date: YESTERDAY,
  source: 'manual' as const,
}

describe('validateHourEntry', () => {
  it('returns no errors for valid input', () => {
    const errors = validateHourEntry(validInput)
    expect(hasHourErrors(errors)).toBe(false)
  })

  it('rejects zero hours', () => {
    const errors = validateHourEntry({ ...validInput, hours: 0 })
    expect(errors.hours).toBeDefined()
  })

  it('rejects negative hours', () => {
    const errors = validateHourEntry({ ...validInput, hours: -1 })
    expect(errors.hours).toBeDefined()
  })

  it('rejects hours greater than 24', () => {
    const errors = validateHourEntry({ ...validInput, hours: 25 })
    expect(errors.hours).toBeDefined()
  })

  it('accepts exactly 24 hours', () => {
    const errors = validateHourEntry({ ...validInput, hours: 24 })
    expect(errors.hours).toBeUndefined()
  })

  it('accepts 0.25 hours (minimum)', () => {
    const errors = validateHourEntry({ ...validInput, hours: 0.25 })
    expect(errors.hours).toBeUndefined()
  })

  it('rejects a future date', () => {
    const tomorrow = new Date(Date.now() + 86400000).toISOString().split('T')[0]
    const errors = validateHourEntry({ ...validInput, logged_date: tomorrow })
    expect(errors.logged_date).toBeDefined()
  })

  it('accepts today as logged_date', () => {
    const errors = validateHourEntry({ ...validInput, logged_date: TODAY })
    expect(errors.logged_date).toBeUndefined()
  })

  it('rejects missing volunteer_id', () => {
    const errors = validateHourEntry({ ...validInput, volunteer_id: '' })
    expect(errors.volunteer_id).toBeDefined()
  })

  it('returns Spanish error messages', () => {
    const errors = validateHourEntry({ ...validInput, hours: 0 })
    expect(errors.hours).toMatch(/horas/)
  })
})
```

---

### Step 4 — Server Actions

**File**: `src/app/actions/volunteer-hour-actions.ts`

```typescript
'use server'

import { createRouteHandlerClient } from '@supabase/auth-helpers-nextjs'
import { cookies } from 'next/headers'
import { revalidatePath } from 'next/cache'
import { redirect } from 'next/navigation'
import { isAdmin } from '@/lib/auth/is-admin'
import { supabaseAdmin } from '@/lib/supabase/admin'
import {
  validateHourEntry,
  hasHourErrors,
  type HourEntryInput,
} from '@/lib/hours/validate-hour-entry'

export async function logVolunteerHours(
  input: HourEntryInput
): Promise<{ errors?: ReturnType<typeof validateHourEntry>; error?: string }> {
  const supabase = createRouteHandlerClient({ cookies })
  const { data: { user } } = await supabase.auth.getUser()

  if (!user) redirect('/auth/login')
  if (!(await isAdmin(user.id))) return { error: 'Sin autorización' }

  // Validate input
  const errors = validateHourEntry(input)
  if (hasHourErrors(errors)) return { errors }

  // Check volunteer is active
  const { data: profile } = await supabaseAdmin
    .from('volunteer_profiles')
    .select('status')
    .eq('id', input.volunteer_id)
    .maybeSingle()

  if (!profile || profile.status !== 'active') {
    return { error: 'El voluntario no está activo' }
  }

  const { error: insertErr } = await supabaseAdmin
    .from('volunteer_hours')
    .insert({
      volunteer_id: input.volunteer_id,
      hours: input.hours,
      logged_date: input.logged_date,
      notes: input.notes ?? null,
      source: input.source,
      shift_id: input.shift_id ?? null,
      logged_by: user.id,
    })

  if (insertErr) {
    // Duplicate shift entry
    if (insertErr.code === '23505') {
      return { error: 'Ya existe un registro de horas para este turno' }
    }
    return { error: 'No se pudieron registrar las horas' }
  }

  revalidatePath(`/admin/volunteers/${input.volunteer_id}`)
  revalidatePath('/admin/volunteers/dashboard')
  return {}
}

export async function deleteHourEntry(
  entryId: string,
  volunteerId: string
): Promise<{ error?: string }> {
  const supabase = createRouteHandlerClient({ cookies })
  const { data: { user } } = await supabase.auth.getUser()

  if (!user) redirect('/auth/login')
  if (!(await isAdmin(user.id))) return { error: 'Sin autorización' }

  const { error } = await supabaseAdmin
    .from('volunteer_hours')
    .delete()
    .eq('id', entryId)

  if (error) return { error: 'No se pudo eliminar el registro' }

  revalidatePath(`/admin/volunteers/${volunteerId}`)
  return {}
}
```

---

### Step 5 — Admin hour log form (client component)

**File**: `src/app/admin/volunteers/[id]/LogHoursForm.tsx`

```typescript
'use client'

import { useState, useTransition } from 'react'
import { logVolunteerHours } from '@/app/actions/volunteer-hour-actions'

interface LogHoursFormProps {
  volunteerId: string
}

export function LogHoursForm({ volunteerId }: LogHoursFormProps) {
  const [isPending, startTransition] = useTransition()
  const [error, setError] = useState<string | null>(null)
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({})
  const [success, setSuccess] = useState(false)

  const today = new Date().toISOString().split('T')[0]

  function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setError(null)
    setFieldErrors({})
    setSuccess(false)

    const formData = new FormData(e.currentTarget)

    startTransition(async () => {
      const result = await logVolunteerHours({
        volunteer_id: volunteerId,
        hours: parseFloat(formData.get('hours') as string),
        logged_date: formData.get('logged_date') as string,
        notes: (formData.get('notes') as string) || undefined,
        source: 'manual',
      })

      if (result.errors) {
        setFieldErrors(result.errors as Record<string, string>)
      } else if (result.error) {
        setError(result.error)
      } else {
        setSuccess(true)
        ;(e.target as HTMLFormElement).reset()
      }
    })
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <h3 className="text-sm font-semibold text-[var(--text-primary)]">
        Registrar horas
      </h3>

      <div className="flex gap-3">
        <div className="flex-1">
          <label className="block text-xs text-[var(--text-secondary)] mb-1">
            Horas
          </label>
          <input
            name="hours"
            type="number"
            step="0.25"
            min="0.25"
            max="24"
            required
            className="w-full text-sm border border-[var(--border)] rounded px-2 py-1.5 bg-[var(--bg-input)] text-[var(--text-primary)]"
          />
          {fieldErrors.hours && (
            <p className="text-xs text-[var(--color-error)] mt-1">{fieldErrors.hours}</p>
          )}
        </div>

        <div className="flex-1">
          <label className="block text-xs text-[var(--text-secondary)] mb-1">
            Fecha
          </label>
          <input
            name="logged_date"
            type="date"
            max={today}
            defaultValue={today}
            required
            className="w-full text-sm border border-[var(--border)] rounded px-2 py-1.5 bg-[var(--bg-input)] text-[var(--text-primary)]"
          />
          {fieldErrors.logged_date && (
            <p className="text-xs text-[var(--color-error)] mt-1">{fieldErrors.logged_date}</p>
          )}
        </div>
      </div>

      <div>
        <label className="block text-xs text-[var(--text-secondary)] mb-1">
          Notas (opcional)
        </label>
        <input
          name="notes"
          type="text"
          placeholder="Descripción de la actividad"
          className="w-full text-sm border border-[var(--border)] rounded px-2 py-1.5 bg-[var(--bg-input)] text-[var(--text-primary)]"
        />
      </div>

      {error && (
        <p className="text-xs text-[var(--color-error)]">{error}</p>
      )}
      {success && (
        <p className="text-xs text-[var(--color-success)]">
          Horas registradas correctamente
        </p>
      )}

      <button
        type="submit"
        disabled={isPending}
        className="px-4 py-2 text-sm rounded bg-[var(--color-primary)] text-white hover:bg-[var(--color-primary-hover)] disabled:opacity-50"
      >
        {isPending ? 'Guardando…' : 'Registrar horas'}
      </button>
    </form>
  )
}
```

---

### Step 6 — Extend admin volunteer detail page

The existing `src/app/admin/volunteers/[id]/page.tsx` (created in S01/T03) should include:

1. A query for the volunteer's hour log
2. Display of the log below the profile section
3. The `LogHoursForm` inline

**Add to the existing page Server Component** after the profile fetch:

```typescript
// Append to existing /admin/volunteers/[id]/page.tsx
// After existing queries, add:

const { data: hourLog } = await supabaseAdmin
  .from('volunteer_hours')
  .select('id, hours, logged_date, notes, source, shift_id')
  .eq('volunteer_id', params.id)
  .order('logged_date', { ascending: false })
  .limit(20)

// Then in the JSX, add a section after profile details:
```

```tsx
{/* Hour log section */}
<section className="mt-8">
  <div className="flex items-center justify-between mb-3">
    <h2 className="text-lg font-semibold text-[var(--text-primary)]">
      Registro de horas
    </h2>
    <span className="text-sm text-[var(--text-secondary)]">
      Total: <strong>{profile.hours_total ?? 0}h</strong>
    </span>
  </div>

  <LogHoursForm volunteerId={params.id} />

  <ul className="mt-4 divide-y divide-[var(--border)]">
    {(hourLog ?? []).map((entry) => (
      <li key={entry.id} className="py-2 flex items-center justify-between text-sm">
        <span className="text-[var(--text-primary)]">
          {entry.logged_date} · {entry.hours}h
          {entry.notes && (
            <span className="text-[var(--text-secondary)] ml-2">{entry.notes}</span>
          )}
        </span>
        <span className="text-xs text-[var(--text-secondary)]">
          {entry.source === 'shift' ? 'Turno' : 'Manual'}
        </span>
      </li>
    ))}
    {(hourLog ?? []).length === 0 && (
      <li className="py-3 text-sm text-[var(--text-secondary)]">
        Sin registros de horas aún
      </li>
    )}
  </ul>
</section>
```

---

### Step 7 — Volunteer self-view (read-only)

Add a read-only hour summary to the volunteer's own dashboard. This is a small addition to `src/app/volunteers/dashboard/page.tsx`:

```typescript
// In the existing VolunteerDashboardPage Promise.all, add a 4th query:
supabase
  .from('volunteer_hours')
  .select('id, hours, logged_date, notes, source')
  .order('logged_date', { ascending: false })
  .limit(5),
```

Then render below the tasks section:

```tsx
{/* Hours summary (already shown on profile: hours_total) */}
<section className="mt-8">
  <h2 className="text-lg font-semibold text-[var(--text-primary)] mb-3">
    Mis horas recientes
  </h2>
  {(recentHours ?? []).length === 0 ? (
    <p className="text-sm text-[var(--text-secondary)]">Sin registros de horas aún.</p>
  ) : (
    <ul className="space-y-1">
      {(recentHours ?? []).map((entry) => (
        <li key={entry.id} className="text-sm text-[var(--text-secondary)]">
          {entry.logged_date} · <strong>{entry.hours}h</strong>
          {entry.notes && <span className="ml-1">— {entry.notes}</span>}
        </li>
      ))}
    </ul>
  )}
</section>
```

---

### Data flow summary

```
Admin visits /admin/volunteers/[id]
  → Server Component reads hourLog (last 20 entries) via supabaseAdmin
  → Renders LogHoursForm (client component)
  → On submit: logVolunteerHours Server Action
      → validateHourEntry (pure, unit-tested)
      → supabaseAdmin.insert into volunteer_hours
      → PostgreSQL trigger: sync_volunteer_hours_total
          → updates volunteer_profiles.hours_total atomically
      → revalidatePath → page re-renders with new total

Volunteer visits /volunteers/dashboard
  → Server Component reads last 5 hour entries (RLS scoped)
  → Displays read-only summary alongside hours_total
```

---

### Files to create/update

| File | Action |
|------|--------|
| `supabase/migrations/20260401000015_volunteer_hours.sql` | CREATE |
| `src/lib/hours/validate-hour-entry.ts` | CREATE |
| `src/lib/hours/__tests__/validate-hour-entry.test.ts` | CREATE |
| `src/app/actions/volunteer-hour-actions.ts` | CREATE |
| `src/app/admin/volunteers/[id]/LogHoursForm.tsx` | CREATE |
| `src/app/admin/volunteers/[id]/page.tsx` | UPDATE (add hour log section) |
| `src/app/volunteers/dashboard/page.tsx` | UPDATE (add recent hours) |

## Related Issues

- EPIC-5
- S04
- Depends on: S01/T01 (volunteer_profiles), S01/T03 (isAdmin), S02/T01 (volunteer_shifts)
