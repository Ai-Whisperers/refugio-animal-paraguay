---
task: T01
story: S03
epic: EPIC-5
title: Create task assignment interface
status: ready
priority: medium
created: 2026-03-25T17:13:26.731919
---

# T01: Create task assignment interface

## Description

Admins can create named tasks (shelter chores, animal care duties, etc.) and assign them to active volunteers. Volunteers see their assigned tasks on a personal dashboard. Task status progresses from `pending → in_progress → completed`.

## Acceptance Criteria

- [ ] Admin can create a task with title, description, due date, and assign to a volunteer
- [ ] Admin can edit or delete unstarted tasks
- [ ] Volunteers see only their own tasks, sorted by due date
- [ ] Volunteers can update their task status: `pending → in_progress → completed`
- [ ] Admin task list shows all tasks filtered by volunteer, status, or date
- [ ] Status transition logic is unit-tested with vitest
- [ ] Task creation is validated (title required, due date not in past, volunteer must be active)

## Implementation Notes

### Tech Stack Constraints

- **Supabase only** — No Prisma, no ORM, no Redis.
- **Next.js 14 App Router** — Server Components by default; `'use client'` only for interactive controls.
- **Server Actions** (`'use server'`) for all mutations.
- **Tailwind CSS 3.4.19 pinned** — CSS vars only (`bg-[var(--bg-card)]`).
- `supabaseAdmin` (service role) for admin reads/writes; `createServerComponentClient` for volunteer reads (RLS applies).
- Admin authorization via `isAdmin(userId)` from `src/lib/auth/is-admin.ts`.

---

### Step 1 — Migration: `volunteer_tasks` table

**File**: `supabase/migrations/20260401000014_volunteer_tasks.sql`

```sql
create type public.task_status as enum ('pending', 'in_progress', 'completed');

create table public.volunteer_tasks (
  id uuid primary key default gen_random_uuid(),
  title text not null,
  description text,
  due_date date not null,
  status public.task_status not null default 'pending',
  assigned_to uuid not null references auth.users(id) on delete cascade,
  created_by uuid not null references auth.users(id),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- updated_at trigger
create or replace function public.set_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create trigger volunteer_tasks_updated_at
  before update on public.volunteer_tasks
  for each row execute function public.set_updated_at();

-- RLS
alter table public.volunteer_tasks enable row level security;

-- Volunteers can read their own tasks
create policy "Volunteers can read their own tasks"
  on public.volunteer_tasks
  for select
  to authenticated
  using (assigned_to = auth.uid());

-- Volunteers can update status of their own tasks (pending → in_progress → completed)
-- Range is validated at application layer; RLS only scopes to owner
create policy "Volunteers can update their own task status"
  on public.volunteer_tasks
  for update
  to authenticated
  using (assigned_to = auth.uid())
  with check (assigned_to = auth.uid());

-- Admin reads and creates/deletes go through supabaseAdmin (service role, bypasses RLS)

create index volunteer_tasks_assigned_to_idx on public.volunteer_tasks(assigned_to);
create index volunteer_tasks_due_date_idx on public.volunteer_tasks(due_date);
create index volunteer_tasks_status_idx on public.volunteer_tasks(status);
```

---

### Step 2 — Types

**File**: `src/lib/tasks/types.ts`

```typescript
export type TaskStatus = 'pending' | 'in_progress' | 'completed'

export interface VolunteerTask {
  id: string
  title: string
  description: string | null
  due_date: string
  status: TaskStatus
  assigned_to: string
  created_by: string
  created_at: string
  updated_at: string
}

export interface CreateTaskInput {
  title: string
  description: string
  due_date: string          // ISO date string
  assigned_to: string       // volunteer user ID
}

export interface CreateTaskErrors {
  title?: string
  due_date?: string
  assigned_to?: string
}
```

---

### Step 3 — Status transition validation

**File**: `src/lib/tasks/validate-task-transition.ts`

```typescript
import type { TaskStatus } from './types'

const ALLOWED_TASK_TRANSITIONS: Record<TaskStatus, TaskStatus[]> = {
  pending: ['in_progress'],
  in_progress: ['completed'],
  completed: [],
}

const STATUS_LABELS: Record<TaskStatus, string> = {
  pending: 'Pendiente',
  in_progress: 'En progreso',
  completed: 'Completada',
}

export interface TaskTransitionError {
  code: 'invalid_transition'
  message: string
}

export function validateTaskTransition(
  current: TaskStatus,
  next: TaskStatus
): TaskTransitionError | null {
  if (ALLOWED_TASK_TRANSITIONS[current].includes(next)) {
    return null
  }
  return {
    code: 'invalid_transition',
    message: `No se puede cambiar el estado de "${STATUS_LABELS[current]}" a "${STATUS_LABELS[next]}".`,
  }
}

export function getAllowedTaskTransitions(current: TaskStatus): TaskStatus[] {
  return ALLOWED_TASK_TRANSITIONS[current]
}

export function getStatusLabel(status: TaskStatus): string {
  return STATUS_LABELS[status]
}
```

---

### Step 4 — Task creation validation

**File**: `src/lib/tasks/validate-task-input.ts`

```typescript
import type { CreateTaskInput, CreateTaskErrors } from './types'

export function validateTaskInput(input: CreateTaskInput): CreateTaskErrors {
  const errors: CreateTaskErrors = {}

  if (!input.title.trim()) {
    errors.title = 'El título es obligatorio.'
  }

  if (!input.due_date) {
    errors.due_date = 'La fecha límite es obligatoria.'
  } else {
    const today = new Date()
    today.setHours(0, 0, 0, 0)
    const due = new Date(input.due_date)
    due.setHours(0, 0, 0, 0)
    if (due < today) {
      errors.due_date = 'La fecha límite no puede ser en el pasado.'
    }
  }

  if (!input.assigned_to) {
    errors.assigned_to = 'Debes seleccionar un voluntario.'
  }

  return errors
}

export function hasTaskErrors(errors: CreateTaskErrors): boolean {
  return Object.keys(errors).length > 0
}
```

---

### Step 5 — Unit tests

**File**: `src/lib/tasks/__tests__/validate-task-transition.test.ts`

```typescript
import { describe, it, expect } from 'vitest'
import { validateTaskTransition, getAllowedTaskTransitions } from '../validate-task-transition'

describe('validateTaskTransition', () => {
  it('allows pending → in_progress', () => {
    expect(validateTaskTransition('pending', 'in_progress')).toBeNull()
  })

  it('allows in_progress → completed', () => {
    expect(validateTaskTransition('in_progress', 'completed')).toBeNull()
  })

  it('blocks pending → completed (skipping a step)', () => {
    const result = validateTaskTransition('pending', 'completed')
    expect(result?.code).toBe('invalid_transition')
  })

  it('blocks in_progress → pending (reverse)', () => {
    const result = validateTaskTransition('in_progress', 'pending')
    expect(result?.code).toBe('invalid_transition')
  })

  it('blocks completed → any transition', () => {
    expect(validateTaskTransition('completed', 'pending')?.code).toBe('invalid_transition')
    expect(validateTaskTransition('completed', 'in_progress')?.code).toBe('invalid_transition')
  })

  it('returns Spanish error message', () => {
    const result = validateTaskTransition('completed', 'pending')
    expect(result?.message).toContain('Completada')
  })

  it('getAllowedTaskTransitions returns empty array for completed', () => {
    expect(getAllowedTaskTransitions('completed')).toEqual([])
  })

  it('getAllowedTaskTransitions returns [in_progress] for pending', () => {
    expect(getAllowedTaskTransitions('pending')).toEqual(['in_progress'])
  })
})
```

---

### Step 6 — Server Actions

**File**: `src/app/actions/volunteer-task-actions.ts`

```typescript
'use server'

import { createRouteHandlerClient } from '@supabase/auth-helpers-nextjs'
import { cookies } from 'next/headers'
import { revalidatePath } from 'next/cache'
import { supabaseAdmin } from '@/lib/supabase/admin'
import { isAdmin } from '@/lib/auth/is-admin'
import { validateTaskInput, hasTaskErrors } from '@/lib/tasks/validate-task-input'
import { validateTaskTransition } from '@/lib/tasks/validate-task-transition'
import type { CreateTaskInput, TaskStatus } from '@/lib/tasks/types'

// ─── Admin: create task ───────────────────────────────────────────────────────

export async function createVolunteerTask(
  input: CreateTaskInput
): Promise<{ errors?: Record<string, string>; error?: string }> {
  const supabase = createRouteHandlerClient({ cookies })
  const { data: { user } } = await supabase.auth.getUser()

  if (!user) return { error: 'No autenticado.' }
  if (!(await isAdmin(user.id))) return { error: 'Acceso denegado.' }

  const errors = validateTaskInput(input)
  if (hasTaskErrors(errors)) return { errors }

  // Verify assigned volunteer is active
  const { data: profile } = await supabaseAdmin
    .from('volunteer_profiles')
    .select('status')
    .eq('id', input.assigned_to)
    .maybeSingle()

  if (!profile || profile.status !== 'active') {
    return { errors: { assigned_to: 'El voluntario seleccionado no está activo.' } }
  }

  const { error: insertErr } = await supabaseAdmin
    .from('volunteer_tasks')
    .insert({
      title: input.title.trim(),
      description: input.description.trim() || null,
      due_date: input.due_date,
      assigned_to: input.assigned_to,
      created_by: user.id,
    })

  if (insertErr) return { error: 'Error al crear la tarea. Intenta nuevamente.' }

  revalidatePath('/admin/volunteers/tasks')
  revalidatePath(`/admin/volunteers/${input.assigned_to}`)
  return {}
}

// ─── Admin: delete task ───────────────────────────────────────────────────────

export async function deleteVolunteerTask(
  taskId: string
): Promise<{ error?: string }> {
  const supabase = createRouteHandlerClient({ cookies })
  const { data: { user } } = await supabase.auth.getUser()

  if (!user) return { error: 'No autenticado.' }
  if (!(await isAdmin(user.id))) return { error: 'Acceso denegado.' }

  // Only allow deleting tasks that haven't been started
  const { data: task } = await supabaseAdmin
    .from('volunteer_tasks')
    .select('status')
    .eq('id', taskId)
    .maybeSingle()

  if (!task) return { error: 'Tarea no encontrada.' }
  if (task.status !== 'pending') {
    return { error: 'Solo se pueden eliminar tareas que aún no han comenzado.' }
  }

  await supabaseAdmin.from('volunteer_tasks').delete().eq('id', taskId)

  revalidatePath('/admin/volunteers/tasks')
  return {}
}

// ─── Volunteer: update task status ───────────────────────────────────────────

export async function updateTaskStatus(
  taskId: string,
  nextStatus: TaskStatus
): Promise<{ error?: string }> {
  const supabase = createRouteHandlerClient({ cookies })
  const { data: { user } } = await supabase.auth.getUser()

  if (!user) return { error: 'No autenticado.' }

  // Fetch current task — scoped to the authenticated user via RLS
  const { data: task } = await supabase
    .from('volunteer_tasks')
    .select('id, status, assigned_to')
    .eq('id', taskId)
    .maybeSingle()

  if (!task) return { error: 'Tarea no encontrada.' }

  const transitionError = validateTaskTransition(task.status as TaskStatus, nextStatus)
  if (transitionError) return { error: transitionError.message }

  const { error: updateErr } = await supabase
    .from('volunteer_tasks')
    .update({ status: nextStatus })
    .eq('id', taskId)

  if (updateErr) return { error: 'Error al actualizar la tarea.' }

  revalidatePath('/volunteers/tasks')
  return {}
}
```

**Note on `updateTaskStatus`**: The volunteer update uses `supabase` (user-scoped client with cookies), not `supabaseAdmin`. The RLS policy `"Volunteers can update their own task status"` restricts the update to rows where `assigned_to = auth.uid()`. This means a volunteer cannot update another volunteer's task even by guessing the UUID — the row won't be found or writable.

---

### Step 7 — Admin task list page

**File**: `src/app/admin/volunteers/tasks/page.tsx`

```typescript
import { createServerComponentClient } from '@supabase/auth-helpers-nextjs'
import { cookies } from 'next/headers'
import { redirect } from 'next/navigation'
import { isAdmin } from '@/lib/auth/is-admin'
import { supabaseAdmin } from '@/lib/supabase/admin'
import { getStatusLabel } from '@/lib/tasks/validate-task-transition'
import type { TaskStatus } from '@/lib/tasks/types'

const STATUS_FILTER_OPTIONS: { value: TaskStatus | 'all'; label: string }[] = [
  { value: 'all', label: 'Todas' },
  { value: 'pending', label: 'Pendientes' },
  { value: 'in_progress', label: 'En progreso' },
  { value: 'completed', label: 'Completadas' },
]

interface Props {
  searchParams: { status?: string }
}

export default async function AdminTasksPage({ searchParams }: Props) {
  const supabase = createServerComponentClient({ cookies })
  const { data: { user } } = await supabase.auth.getUser()

  if (!user) redirect('/auth/login')
  if (!(await isAdmin(user.id))) redirect('/dashboard')

  const statusFilter = searchParams.status as TaskStatus | 'all' | undefined

  let query = supabaseAdmin
    .from('volunteer_tasks')
    .select(`
      id,
      title,
      due_date,
      status,
      volunteer:volunteer_profiles!assigned_to(id, full_name)
    `)
    .order('due_date', { ascending: true })

  if (statusFilter && statusFilter !== 'all') {
    query = query.eq('status', statusFilter)
  }

  const { data: tasks } = await query

  return (
    <main className="max-w-4xl mx-auto py-8 px-4">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-[var(--text-primary)]">Tareas de voluntarios</h1>
        <a
          href="/admin/volunteers/tasks/new"
          className="px-4 py-2 text-sm rounded bg-[var(--color-primary)] text-white hover:bg-[var(--color-primary-hover)]"
        >
          Crear tarea
        </a>
      </div>

      {/* Status filter tabs */}
      <div className="flex gap-2 mb-4 flex-wrap">
        {STATUS_FILTER_OPTIONS.map(({ value, label }) => {
          const isActive = (statusFilter ?? 'all') === value
          return (
            <a
              key={value}
              href={value === 'all' ? '/admin/volunteers/tasks' : `/admin/volunteers/tasks?status=${value}`}
              className={`px-3 py-1 rounded text-sm border ${
                isActive
                  ? 'bg-[var(--color-primary)] text-white border-[var(--color-primary)]'
                  : 'border-[var(--border)] text-[var(--text-secondary)] hover:bg-[var(--bg-hover)]'
              }`}
            >
              {label}
            </a>
          )
        })}
      </div>

      {(tasks ?? []).length === 0 ? (
        <p className="text-[var(--text-secondary)]">No hay tareas para mostrar.</p>
      ) : (
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-[var(--text-secondary)] border-b border-[var(--border)]">
              <th className="pb-2 pr-4">Tarea</th>
              <th className="pb-2 pr-4">Voluntario</th>
              <th className="pb-2 pr-4">Vencimiento</th>
              <th className="pb-2">Estado</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[var(--border)]">
            {(tasks ?? []).map((task) => {
              const v = task.volunteer as { id: string; full_name: string }
              return (
                <tr key={task.id}>
                  <td className="py-3 pr-4 text-[var(--text-primary)]">{task.title}</td>
                  <td className="py-3 pr-4">
                    <a
                      href={`/admin/volunteers/${v.id}`}
                      className="text-[var(--color-primary)] hover:underline"
                    >
                      {v.full_name}
                    </a>
                  </td>
                  <td className="py-3 pr-4 text-[var(--text-secondary)]">{task.due_date}</td>
                  <td className="py-3">
                    <span
                      className={`px-2 py-0.5 rounded text-xs font-medium ${
                        task.status === 'completed'
                          ? 'bg-[var(--color-success-bg)] text-[var(--color-success)]'
                          : task.status === 'in_progress'
                          ? 'bg-[var(--color-warning-bg)] text-[var(--color-warning)]'
                          : 'bg-[var(--bg-muted)] text-[var(--text-secondary)]'
                      }`}
                    >
                      {getStatusLabel(task.status as TaskStatus)}
                    </span>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      )}
    </main>
  )
}
```

---

### Step 8 — Admin create task form (client component + page)

**File**: `src/app/admin/volunteers/tasks/new/CreateTaskForm.tsx`

```typescript
'use client'

import { useState, useTransition } from 'react'
import { createVolunteerTask } from '@/app/actions/volunteer-task-actions'

interface ActiveVolunteer {
  id: string
  full_name: string
}

interface Props {
  volunteers: ActiveVolunteer[]
}

export default function CreateTaskForm({ volunteers }: Props) {
  const [isPending, startTransition] = useTransition()
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({})
  const [serverError, setServerError] = useState<string | null>(null)

  function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setFieldErrors({})
    setServerError(null)

    const formData = new FormData(e.currentTarget)
    const input = {
      title: formData.get('title') as string,
      description: formData.get('description') as string,
      due_date: formData.get('due_date') as string,
      assigned_to: formData.get('assigned_to') as string,
    }

    startTransition(async () => {
      const result = await createVolunteerTask(input)
      if (result.errors) setFieldErrors(result.errors)
      else if (result.error) setServerError(result.error)
      // On success, Server Action revalidates + navigation handled by redirect in action
    })
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4 max-w-lg">
      {serverError && (
        <div className="p-3 rounded bg-[var(--color-error-bg)] text-[var(--color-error)] text-sm">
          {serverError}
        </div>
      )}

      <div>
        <label className="block text-sm font-medium text-[var(--text-primary)] mb-1">
          Título <span className="text-[var(--color-error)]">*</span>
        </label>
        <input
          name="title"
          type="text"
          required
          className="w-full border border-[var(--border)] rounded px-3 py-2 text-sm bg-[var(--bg-input)] text-[var(--text-primary)] focus:outline-none focus:ring-1 focus:ring-[var(--color-primary)]"
        />
        {fieldErrors.title && (
          <p className="text-xs text-[var(--color-error)] mt-1">{fieldErrors.title}</p>
        )}
      </div>

      <div>
        <label className="block text-sm font-medium text-[var(--text-primary)] mb-1">
          Descripción
        </label>
        <textarea
          name="description"
          rows={3}
          className="w-full border border-[var(--border)] rounded px-3 py-2 text-sm bg-[var(--bg-input)] text-[var(--text-primary)] focus:outline-none focus:ring-1 focus:ring-[var(--color-primary)]"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-[var(--text-primary)] mb-1">
          Fecha límite <span className="text-[var(--color-error)]">*</span>
        </label>
        <input
          name="due_date"
          type="date"
          required
          className="w-full border border-[var(--border)] rounded px-3 py-2 text-sm bg-[var(--bg-input)] text-[var(--text-primary)]"
        />
        {fieldErrors.due_date && (
          <p className="text-xs text-[var(--color-error)] mt-1">{fieldErrors.due_date}</p>
        )}
      </div>

      <div>
        <label className="block text-sm font-medium text-[var(--text-primary)] mb-1">
          Asignar a <span className="text-[var(--color-error)]">*</span>
        </label>
        <select
          name="assigned_to"
          required
          className="w-full border border-[var(--border)] rounded px-3 py-2 text-sm bg-[var(--bg-input)] text-[var(--text-primary)]"
        >
          <option value="">Seleccionar voluntario…</option>
          {volunteers.map((v) => (
            <option key={v.id} value={v.id}>
              {v.full_name}
            </option>
          ))}
        </select>
        {fieldErrors.assigned_to && (
          <p className="text-xs text-[var(--color-error)] mt-1">{fieldErrors.assigned_to}</p>
        )}
      </div>

      <button
        type="submit"
        disabled={isPending}
        className="px-4 py-2 rounded bg-[var(--color-primary)] text-white text-sm hover:bg-[var(--color-primary-hover)] disabled:opacity-50"
      >
        {isPending ? 'Creando…' : 'Crear tarea'}
      </button>
    </form>
  )
}
```

**File**: `src/app/admin/volunteers/tasks/new/page.tsx`

```typescript
import { createServerComponentClient } from '@supabase/auth-helpers-nextjs'
import { cookies } from 'next/headers'
import { redirect } from 'next/navigation'
import { isAdmin } from '@/lib/auth/is-admin'
import { supabaseAdmin } from '@/lib/supabase/admin'
import CreateTaskForm from './CreateTaskForm'

export default async function NewTaskPage() {
  const supabase = createServerComponentClient({ cookies })
  const { data: { user } } = await supabase.auth.getUser()

  if (!user) redirect('/auth/login')
  if (!(await isAdmin(user.id))) redirect('/dashboard')

  // Fetch active volunteers for the assignment dropdown
  const { data: volunteers } = await supabaseAdmin
    .from('volunteer_profiles')
    .select('id, full_name')
    .eq('status', 'active')
    .order('full_name', { ascending: true })

  return (
    <main className="max-w-2xl mx-auto py-8 px-4">
      <div className="mb-4">
        <a
          href="/admin/volunteers/tasks"
          className="text-sm text-[var(--color-primary)] hover:underline"
        >
          ← Volver a tareas
        </a>
      </div>
      <h1 className="text-2xl font-bold text-[var(--text-primary)] mb-6">Nueva tarea</h1>
      <CreateTaskForm volunteers={volunteers ?? []} />
    </main>
  )
}
```

---

### Step 9 — Volunteer tasks page

**File**: `src/app/volunteers/tasks/page.tsx`

```typescript
import { createServerComponentClient } from '@supabase/auth-helpers-nextjs'
import { cookies } from 'next/headers'
import { redirect } from 'next/navigation'
import { getStatusLabel, getAllowedTaskTransitions } from '@/lib/tasks/validate-task-transition'
import type { TaskStatus } from '@/lib/tasks/types'
import TaskStatusButton from './TaskStatusButton'

export default async function VolunteerTasksPage() {
  const supabase = createServerComponentClient({ cookies })
  const { data: { user } } = await supabase.auth.getUser()

  if (!user) redirect('/auth/login')

  // RLS: only returns tasks where assigned_to = auth.uid()
  const { data: tasks } = await supabase
    .from('volunteer_tasks')
    .select('id, title, description, due_date, status')
    .neq('status', 'completed')
    .order('due_date', { ascending: true })

  return (
    <main className="max-w-2xl mx-auto py-8 px-4">
      <h1 className="text-2xl font-bold text-[var(--text-primary)] mb-6">Mis tareas</h1>

      {(tasks ?? []).length === 0 && (
        <p className="text-[var(--text-secondary)]">No tenés tareas pendientes.</p>
      )}

      <ul className="space-y-3">
        {(tasks ?? []).map((task) => {
          const nextSteps = getAllowedTaskTransitions(task.status as TaskStatus)
          return (
            <li
              key={task.id}
              className="bg-[var(--bg-card)] border border-[var(--border)] rounded-lg p-4"
            >
              <div className="flex items-start justify-between gap-4">
                <div>
                  <h2 className="font-medium text-[var(--text-primary)]">{task.title}</h2>
                  {task.description && (
                    <p className="text-sm text-[var(--text-secondary)] mt-1">{task.description}</p>
                  )}
                  <p className="text-xs text-[var(--text-secondary)] mt-2">
                    Vence: {task.due_date} ·{' '}
                    <span className="font-medium">{getStatusLabel(task.status as TaskStatus)}</span>
                  </p>
                </div>

                {nextSteps.length > 0 && (
                  <TaskStatusButton
                    taskId={task.id}
                    nextStatus={nextSteps[0]}
                    label={nextSteps[0] === 'in_progress' ? 'Iniciar' : 'Completar'}
                  />
                )}
              </div>
            </li>
          )
        })}
      </ul>
    </main>
  )
}
```

**File**: `src/app/volunteers/tasks/TaskStatusButton.tsx`

```typescript
'use client'

import { useState, useTransition } from 'react'
import { updateTaskStatus } from '@/app/actions/volunteer-task-actions'
import type { TaskStatus } from '@/lib/tasks/types'

interface Props {
  taskId: string
  nextStatus: TaskStatus
  label: string
}

export default function TaskStatusButton({ taskId, nextStatus, label }: Props) {
  const [isPending, startTransition] = useTransition()
  const [error, setError] = useState<string | null>(null)

  function handleClick() {
    setError(null)
    startTransition(async () => {
      const result = await updateTaskStatus(taskId, nextStatus)
      if (result.error) setError(result.error)
    })
  }

  return (
    <div className="flex flex-col items-end gap-1">
      <button
        onClick={handleClick}
        disabled={isPending}
        className="px-3 py-1.5 text-sm rounded bg-[var(--color-primary)] text-white hover:bg-[var(--color-primary-hover)] disabled:opacity-50"
      >
        {isPending ? 'Guardando…' : label}
      </button>
      {error && (
        <p className="text-xs text-[var(--color-error)] max-w-[160px] text-right">{error}</p>
      )}
    </div>
  )
}
```

---

### Files to create

| File | Action |
|------|--------|
| `supabase/migrations/20260401000014_volunteer_tasks.sql` | CREATE |
| `src/lib/tasks/types.ts` | CREATE |
| `src/lib/tasks/validate-task-transition.ts` | CREATE |
| `src/lib/tasks/validate-task-input.ts` | CREATE |
| `src/lib/tasks/__tests__/validate-task-transition.test.ts` | CREATE |
| `src/app/actions/volunteer-task-actions.ts` | CREATE |
| `src/app/admin/volunteers/tasks/page.tsx` | CREATE |
| `src/app/admin/volunteers/tasks/new/CreateTaskForm.tsx` | CREATE |
| `src/app/admin/volunteers/tasks/new/page.tsx` | CREATE |
| `src/app/volunteers/tasks/page.tsx` | CREATE |
| `src/app/volunteers/tasks/TaskStatusButton.tsx` | CREATE |

## Related Issues

- EPIC-5
- S03
- Depends on: S01/T03 (volunteer_profiles, isAdmin)
