---
task: T02
story: S04
epic: EPIC-4
title: Setup reminder system
status: ready
priority: medium
created: 2026-03-25T17:13:26.731002
---

# T02: Setup reminder system

## Description

Build a health reminder system that generates staff-visible alerts for upcoming and overdue vaccinations and medications. Uses `pg_cron` to schedule a daily Supabase Edge Function that scans for due items and inserts rows into a `health_reminders` table. Staff see a badge count and dismissible reminder list in the admin UI.

No external queues, no Redis, no BullMQ. All scheduling is handled by `pg_cron` inside Supabase.

## Acceptance Criteria

- [ ] `health_reminders` table exists with RLS: staff/admin/vet can read and dismiss their shelter's reminders
- [ ] `pg_cron` job runs the reminder generation function daily at 08:00 UTC
- [ ] Reminder generation logic scans `vaccinations` and `medications` for items due within 7 days or already overdue
- [ ] Reminders are de-duplicated: re-running the job does not create duplicate rows for the same item on the same day
- [ ] Staff badge in the admin nav shows count of unread reminders
- [ ] Staff can dismiss individual reminders (soft-delete via `dismissed_at`)
- [ ] Unit tests cover the pure reminder-generation logic and status helpers
- [ ] Zero TypeScript type errors, zero lint warnings

## Implementation Notes

### Database schema

**Migration**: `supabase/migrations/20260401000009_create_health_reminders.sql`

```sql
-- health_reminders: staff-visible alerts for upcoming/overdue health events
create table health_reminders (
  id             uuid primary key default gen_random_uuid(),
  animal_id      uuid not null references animals(id) on delete cascade,
  reminder_type  text not null check (reminder_type in ('vaccination', 'medication')),
  reference_id   uuid not null,   -- FK to vaccinations.id or medications.id
  due_date       date not null,
  status         text not null check (status in ('upcoming', 'overdue')),
  dismissed_at   timestamptz,
  created_at     timestamptz not null default now(),

  -- de-duplication: one reminder per reference item per calendar day
  unique (reference_id, reminder_type, due_date::date)
);

-- Index for listing active (non-dismissed) reminders per animal
create index health_reminders_animal_active_idx
  on health_reminders (animal_id)
  where dismissed_at is null;

-- RLS
alter table health_reminders enable row level security;

-- Staff/admin/vet can read active reminders
create policy "staff can read reminders"
  on health_reminders for select
  using (
    (select role from profiles where id = auth.uid()) in ('staff', 'admin', 'vet')
  );

-- Staff/admin/vet can dismiss (update dismissed_at only)
create policy "staff can dismiss reminders"
  on health_reminders for update
  using (
    (select role from profiles where id = auth.uid()) in ('staff', 'admin', 'vet')
  )
  with check (true);

-- Only the service role (Edge Function) may insert
-- No insert policy needed for authenticated users — inserts come via service role key

-- Rollback:
-- drop table if exists health_reminders;
```

**Migration**: `supabase/migrations/20260401000010_create_generate_reminders_fn.sql`

```sql
-- generate_health_reminders(): called by pg_cron daily
-- Inserts upcoming/overdue reminders for vaccinations and medications.
-- Uses ON CONFLICT DO NOTHING for idempotency.
create or replace function generate_health_reminders()
returns void
language plpgsql
security definer
as $$
declare
  v_today date := current_date;
  v_window_days int := 7;
begin
  -- Vaccination reminders
  insert into health_reminders (animal_id, reminder_type, reference_id, due_date, status)
  select
    v.animal_id,
    'vaccination',
    v.id,
    v.next_due_date,
    case
      when v.next_due_date < v_today then 'overdue'
      else 'upcoming'
    end
  from vaccinations v
  where v.next_due_date is not null
    and v.next_due_date <= v_today + v_window_days
    -- exclude items already dismissed today
    and not exists (
      select 1 from health_reminders hr
      where hr.reference_id = v.id
        and hr.reminder_type = 'vaccination'
        and hr.dismissed_at is not null
        and hr.dismissed_at::date = v_today
    )
  on conflict (reference_id, reminder_type, (due_date::date)) do nothing;

  -- Medication reminders
  insert into health_reminders (animal_id, reminder_type, reference_id, due_date, status)
  select
    m.animal_id,
    'medication',
    m.id,
    m.next_dose_date,
    case
      when m.next_dose_date < v_today then 'overdue'
      else 'upcoming'
    end
  from medications m
  where m.next_dose_date is not null
    and m.next_dose_date <= v_today + v_window_days
    and not exists (
      select 1 from health_reminders hr
      where hr.reference_id = m.id
        and hr.reminder_type = 'medication'
        and hr.dismissed_at is not null
        and hr.dismissed_at::date = v_today
    )
  on conflict (reference_id, reminder_type, (due_date::date)) do nothing;
end;
$$;

-- Schedule with pg_cron: daily at 08:00 UTC
-- Requires pg_cron extension enabled in Supabase project settings
select cron.schedule(
  'generate-health-reminders-daily',
  '0 8 * * *',
  $$ select generate_health_reminders(); $$
);

-- Rollback:
-- select cron.unschedule('generate-health-reminders-daily');
-- drop function if exists generate_health_reminders();
```

> **Note**: `pg_cron` must be enabled in the Supabase project under Database → Extensions. The schedule runs in the database, so no external cron service is needed.

### Enabling pg_cron in Supabase

Apply via Supabase dashboard (Database → Extensions → pg_cron) or via migration:

```sql
-- supabase/migrations/20260401000008b_enable_pg_cron.sql
-- Run once; safe to run again (create if not exists)
create extension if not exists pg_cron with schema extensions;
grant usage on schema cron to postgres;
```

### TypeScript types

**`src/lib/reminders/types.ts`**

```typescript
export type ReminderType = 'vaccination' | 'medication'
export type ReminderStatus = 'upcoming' | 'overdue'

export interface HealthReminder {
  id: string
  animalId: string
  reminderType: ReminderType
  referenceId: string
  dueDate: string          // ISO date string 'YYYY-MM-DD'
  status: ReminderStatus
  dismissedAt: string | null
  createdAt: string
}

export interface ReminderSummary {
  total: number
  overdue: number
  upcoming: number
}
```

### Server Component: reminder count for nav badge

**`src/lib/reminders/get-reminder-count.ts`**

```typescript
import { createServerComponentClient } from '@supabase/auth-helpers-nextjs'
import { cookies } from 'next/headers'
import type { ReminderSummary } from './types'

export async function getReminderCount(): Promise<ReminderSummary> {
  const supabase = createServerComponentClient({ cookies })

  const { data, error } = await supabase
    .from('health_reminders')
    .select('status')
    .is('dismissed_at', null)

  if (error || !data) {
    return { total: 0, overdue: 0, upcoming: 0 }
  }

  const overdue = data.filter(r => r.status === 'overdue').length
  const upcoming = data.filter(r => r.status === 'upcoming').length
  return { total: data.length, overdue, upcoming }
}
```

### Admin nav badge

**`src/components/layout/AdminNavReminders.tsx`**

```typescript
import { getReminderCount } from '@/lib/reminders/get-reminder-count'

export async function AdminNavReminders() {
  const { total, overdue } = await getReminderCount()

  if (total === 0) return null

  return (
    <span
      className={[
        'ml-1 inline-flex items-center justify-center rounded-full px-2 py-0.5 text-xs font-semibold',
        overdue > 0
          ? 'bg-[var(--color-danger)] text-[var(--color-danger-text)]'
          : 'bg-[var(--color-warning)] text-[var(--color-warning-text)]',
      ].join(' ')}
      aria-label={`${total} recordatorio${total !== 1 ? 's' : ''} de salud pendiente${total !== 1 ? 's' : ''}`}
    >
      {total}
    </span>
  )
}
```

Render inside the existing admin sidebar link for "Recordatorios":

```tsx
// In src/components/layout/AdminSidebar.tsx (existing file — add only this import + usage)
import { AdminNavReminders } from './AdminNavReminders'

// Inside the relevant <Link> element:
<Link href="/admin/reminders">
  Recordatorios
  <Suspense fallback={null}>
    <AdminNavReminders />
  </Suspense>
</Link>
```

### Reminders list page

**`src/app/admin/reminders/page.tsx`**

```typescript
import { createServerComponentClient } from '@supabase/auth-helpers-nextjs'
import { cookies } from 'next/headers'
import { ReminderList } from '@/components/reminders/ReminderList'
import type { HealthReminder } from '@/lib/reminders/types'

export default async function RemindersPage() {
  const supabase = createServerComponentClient({ cookies })

  const { data, error } = await supabase
    .from('health_reminders')
    .select(`
      id,
      animal_id,
      reminder_type,
      reference_id,
      due_date,
      status,
      dismissed_at,
      created_at,
      animals ( name, species )
    `)
    .is('dismissed_at', null)
    .order('status', { ascending: false })   // overdue first
    .order('due_date', { ascending: true })

  const reminders: HealthReminder[] = (data ?? []).map(row => ({
    id: row.id,
    animalId: row.animal_id,
    reminderType: row.reminder_type,
    referenceId: row.reference_id,
    dueDate: row.due_date,
    status: row.status,
    dismissedAt: row.dismissed_at,
    createdAt: row.created_at,
  }))

  return (
    <main className="p-6">
      <h1 className="text-2xl font-semibold text-[var(--text-primary)] mb-6">
        Recordatorios de salud
      </h1>
      {error && (
        <p className="text-[var(--color-danger)] mb-4">
          Error al cargar recordatorios.
        </p>
      )}
      <ReminderList reminders={reminders} />
    </main>
  )
}
```

### ReminderList component

**`src/components/reminders/ReminderList.tsx`**

```typescript
import { DismissReminderButton } from './DismissReminderButton'
import type { HealthReminder } from '@/lib/reminders/types'

const STATUS_LABEL: Record<string, string> = {
  overdue: 'Vencido',
  upcoming: 'Próximo',
}

const STATUS_ROW_CLASS: Record<string, string> = {
  overdue: 'border-l-4 border-[var(--color-danger)] bg-[var(--color-danger-subtle)]',
  upcoming: 'border-l-4 border-[var(--color-warning)] bg-[var(--color-warning-subtle)]',
}

const TYPE_LABEL: Record<string, string> = {
  vaccination: 'Vacuna',
  medication: 'Medicamento',
}

interface Props {
  reminders: HealthReminder[]
}

export function ReminderList({ reminders }: Props) {
  if (reminders.length === 0) {
    return (
      <p className="text-[var(--text-secondary)]">
        Sin recordatorios pendientes.
      </p>
    )
  }

  return (
    <ul className="space-y-3">
      {reminders.map(reminder => (
        <li
          key={reminder.id}
          className={`flex items-center justify-between rounded-lg p-4 ${STATUS_ROW_CLASS[reminder.status] ?? ''}`}
        >
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-xs font-medium uppercase tracking-wide text-[var(--text-secondary)]">
                {TYPE_LABEL[reminder.reminderType]} — {STATUS_LABEL[reminder.status]}
              </span>
            </div>
            <p className="text-sm font-medium text-[var(--text-primary)]">
              Animal ID: {reminder.animalId}
            </p>
            <p className="text-sm text-[var(--text-secondary)]">
              Vence: {reminder.dueDate}
            </p>
          </div>
          <DismissReminderButton reminderId={reminder.id} />
        </li>
      ))}
    </ul>
  )
}
```

### Dismiss Server Action

**`src/app/actions/reminders.ts`**

```typescript
'use server'

import { createServerActionClient } from '@supabase/auth-helpers-nextjs'
import { cookies } from 'next/headers'
import { revalidatePath } from 'next/cache'

export async function dismissReminder(reminderId: string): Promise<void> {
  const supabase = createServerActionClient({ cookies })

  const { data: { user } } = await supabase.auth.getUser()
  if (!user) throw new Error('No autenticado')

  const { data: profile } = await supabase
    .from('profiles')
    .select('role')
    .eq('id', user.id)
    .single()

  if (!profile || !['staff', 'admin', 'vet'].includes(profile.role)) {
    throw new Error('Sin permisos')
  }

  const { error } = await supabase
    .from('health_reminders')
    .update({ dismissed_at: new Date().toISOString() })
    .eq('id', reminderId)
    .is('dismissed_at', null)  // idempotent: no-op if already dismissed

  if (error) throw new Error('Error al descartar recordatorio')

  revalidatePath('/admin/reminders')
}
```

### DismissReminderButton Client Component

**`src/components/reminders/DismissReminderButton.tsx`**

```typescript
'use client'

import { useTransition } from 'react'
import { dismissReminder } from '@/app/actions/reminders'

interface Props {
  reminderId: string
}

export function DismissReminderButton({ reminderId }: Props) {
  const [isPending, startTransition] = useTransition()

  function handleDismiss() {
    startTransition(async () => {
      await dismissReminder(reminderId)
    })
  }

  return (
    <button
      onClick={handleDismiss}
      disabled={isPending}
      aria-label="Descartar recordatorio"
      className="rounded px-3 py-1 text-sm font-medium text-[var(--text-secondary)] hover:bg-[var(--bg-hover)] disabled:opacity-50"
    >
      {isPending ? 'Descartando…' : 'Descartar'}
    </button>
  )
}
```

### Unit tests

**`src/lib/reminders/__tests__/reminder-helpers.test.ts`**

```typescript
import { describe, it, expect } from 'vitest'
import { computeReminderStatus, isWithinWindow } from '../reminder-helpers'

describe('computeReminderStatus', () => {
  it('returns overdue when due date is before today', () => {
    expect(computeReminderStatus('2026-03-01', '2026-04-01')).toBe('overdue')
  })

  it('returns upcoming when due date is today', () => {
    expect(computeReminderStatus('2026-04-01', '2026-04-01')).toBe('upcoming')
  })

  it('returns upcoming when due date is after today', () => {
    expect(computeReminderStatus('2026-04-05', '2026-04-01')).toBe('upcoming')
  })
})

describe('isWithinWindow', () => {
  const WINDOW_DAYS = 7

  it('returns true when due date is today', () => {
    expect(isWithinWindow('2026-04-01', '2026-04-01', WINDOW_DAYS)).toBe(true)
  })

  it('returns true when due date is within window', () => {
    expect(isWithinWindow('2026-04-07', '2026-04-01', WINDOW_DAYS)).toBe(true)
  })

  it('returns false when due date is beyond window', () => {
    expect(isWithinWindow('2026-04-09', '2026-04-01', WINDOW_DAYS)).toBe(false)
  })

  it('returns true when due date is in the past (overdue)', () => {
    expect(isWithinWindow('2026-03-25', '2026-04-01', WINDOW_DAYS)).toBe(true)
  })
})
```

**`src/lib/reminders/reminder-helpers.ts`**

```typescript
import type { ReminderStatus } from './types'

export const REMINDER_WINDOW_DAYS = 7

/**
 * Determine reminder status based on due date vs today.
 * Both params are ISO date strings 'YYYY-MM-DD'.
 */
export function computeReminderStatus(dueDate: string, today: string): ReminderStatus {
  return dueDate < today ? 'overdue' : 'upcoming'
}

/**
 * Returns true if dueDate is overdue or within windowDays from today.
 * Both dueDate and today are ISO date strings.
 */
export function isWithinWindow(dueDate: string, today: string, windowDays: number): boolean {
  const due = new Date(dueDate)
  const todayDate = new Date(today)
  const windowEnd = new Date(today)
  windowEnd.setDate(todayDate.getDate() + windowDays)
  return due <= windowEnd
}
```

### File checklist

| File | Action |
|------|--------|
| `supabase/migrations/20260401000009_create_health_reminders.sql` | Create |
| `supabase/migrations/20260401000010_create_generate_reminders_fn.sql` | Create |
| `src/lib/reminders/types.ts` | Create |
| `src/lib/reminders/reminder-helpers.ts` | Create |
| `src/lib/reminders/get-reminder-count.ts` | Create |
| `src/lib/reminders/__tests__/reminder-helpers.test.ts` | Create |
| `src/app/actions/reminders.ts` | Create |
| `src/app/admin/reminders/page.tsx` | Create |
| `src/components/reminders/ReminderList.tsx` | Create |
| `src/components/reminders/DismissReminderButton.tsx` | Create |
| `src/components/layout/AdminNavReminders.tsx` | Create |
| `src/components/layout/AdminSidebar.tsx` | Modify — add `<AdminNavReminders />` in reminders nav link |

### Key design decisions

- **pg_cron over Edge Function cron triggers**: pg_cron runs inside the database and does not require a deployed Edge Function to exist at a public URL. The generation function is a plain SQL/PLpgSQL function invoked by the scheduler.
- **ON CONFLICT DO NOTHING for idempotency**: The unique constraint `(reference_id, reminder_type, due_date::date)` ensures that re-running the job on the same day produces no duplicates, even if triggered manually.
- **Soft-delete via `dismissed_at`**: Allows auditing of dismissed reminders without DELETE permissions for staff. A dismissed reminder is never re-inserted on the same calendar day (the `not exists` check in the generation function).
- **Service role for inserts**: The `generate_health_reminders()` function is `security definer`, so it runs with the definer's privileges (the postgres role). Authenticated users have no INSERT policy on `health_reminders`, preventing staff from injecting fake reminders.
- **`Suspense` wrapper for badge**: `<AdminNavReminders />` is an async Server Component. Wrapping it in `<Suspense fallback={null}>` ensures the nav renders immediately even if the reminder count query is slow.

## Related Issues

- EPIC-4
- S04
- T01-create-vaccination-tracker (provides `vaccinations.next_due_date` referenced here)
