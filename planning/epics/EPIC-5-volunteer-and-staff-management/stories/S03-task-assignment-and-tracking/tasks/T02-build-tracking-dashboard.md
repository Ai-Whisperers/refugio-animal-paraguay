---
task: T02
story: S03
epic: EPIC-5
title: Build tracking dashboard
status: ready
priority: medium
created: 2026-03-25T17:13:26.731979
---

# T02: Build tracking dashboard

## Description

Build an admin-facing tracking dashboard that shows the current operational status of the shelter's volunteer workforce: task completion rates, shift coverage, and per-volunteer activity. Also provides a self-service volunteer dashboard showing the individual's shifts and task overview.

## Acceptance Criteria

- [ ] Admin dashboard shows active volunteer count, open tasks, and upcoming shifts
- [ ] Admin can see task completion rate (completed / total this month)
- [ ] Admin can see shift coverage rate (assigned slots / total capacity for upcoming shifts)
- [ ] Per-volunteer summary is drillable from the admin list
- [ ] Volunteer personal dashboard shows upcoming shifts and open tasks at a glance
- [ ] All data is read via Server Components (no client-side fetching for initial render)
- [ ] Dashboard data queries are efficient (no N+1 queries)

## Implementation Notes

### Tech Stack Constraints

- **Supabase only** — No Prisma, no ORM, no Redis.
- **Next.js 14 App Router** — Server Components; no `useEffect` data fetching.
- **Tailwind CSS 3.4.19 pinned** — CSS vars only.
- `supabaseAdmin` for admin aggregation queries; `createServerComponentClient` with RLS for volunteer self-views.
- No separate analytics service — all aggregation done at query time via Supabase/PostgreSQL.

---

### Step 1 — Admin dashboard overview

**File**: `src/app/admin/volunteers/dashboard/page.tsx`

All metrics computed server-side in a single page with parallel Supabase queries.

```typescript
import { createServerComponentClient } from '@supabase/auth-helpers-nextjs'
import { cookies } from 'next/headers'
import { redirect } from 'next/navigation'
import { isAdmin } from '@/lib/auth/is-admin'
import { supabaseAdmin } from '@/lib/supabase/admin'

interface MetricCardProps {
  label: string
  value: string | number
  subtext?: string
}

function MetricCard({ label, value, subtext }: MetricCardProps) {
  return (
    <div className="bg-[var(--bg-card)] border border-[var(--border)] rounded-lg p-4">
      <p className="text-sm text-[var(--text-secondary)]">{label}</p>
      <p className="text-3xl font-bold text-[var(--text-primary)] mt-1">{value}</p>
      {subtext && <p className="text-xs text-[var(--text-secondary)] mt-1">{subtext}</p>}
    </div>
  )
}

export default async function AdminVolunteerDashboard() {
  const supabase = createServerComponentClient({ cookies })
  const { data: { user } } = await supabase.auth.getUser()

  if (!user) redirect('/auth/login')
  if (!(await isAdmin(user.id))) redirect('/dashboard')

  const today = new Date().toISOString().split('T')[0]
  const thisMonthStart = today.slice(0, 7) + '-01'  // 'YYYY-MM-01'

  // Run all aggregation queries in parallel
  const [
    { count: activeCount },
    { count: pendingCount },
    { data: taskStats },
    { data: shiftStats },
    { data: recentVolunteers },
  ] = await Promise.all([
    // Active volunteer count
    supabaseAdmin
      .from('volunteer_profiles')
      .select('*', { count: 'exact', head: true })
      .eq('status', 'active'),

    // Pending review count
    supabaseAdmin
      .from('volunteer_profiles')
      .select('*', { count: 'exact', head: true })
      .eq('status', 'pending_review'),

    // Task stats this month
    supabaseAdmin
      .from('volunteer_tasks')
      .select('status')
      .gte('created_at', thisMonthStart),

    // Upcoming shift coverage
    supabaseAdmin
      .from('volunteer_shifts')
      .select(`
        id,
        max_volunteers,
        shift_assignments(count)
      `)
      .gte('shift_date', today),

    // Recently active volunteers (registered in last 30 days)
    supabaseAdmin
      .from('volunteer_profiles')
      .select('id, full_name, status, created_at')
      .order('created_at', { ascending: false })
      .limit(5),
  ])

  // Compute task completion rate
  const totalTasks = taskStats?.length ?? 0
  const completedTasks = taskStats?.filter((t) => t.status === 'completed').length ?? 0
  const openTasks = taskStats?.filter((t) => t.status !== 'completed').length ?? 0
  const taskCompletionRate = totalTasks > 0
    ? Math.round((completedTasks / totalTasks) * 100)
    : 0

  // Compute shift coverage rate
  let totalCapacity = 0
  let totalAssigned = 0
  for (const shift of shiftStats ?? []) {
    totalCapacity += shift.max_volunteers
    totalAssigned += (shift.shift_assignments as { count: number }[])[0]?.count ?? 0
  }
  const coverageRate = totalCapacity > 0
    ? Math.round((totalAssigned / totalCapacity) * 100)
    : 0

  return (
    <main className="max-w-5xl mx-auto py-8 px-4">
      <h1 className="text-2xl font-bold text-[var(--text-primary)] mb-6">
        Dashboard de voluntarios
      </h1>

      {/* Top metrics row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <MetricCard
          label="Voluntarios activos"
          value={activeCount ?? 0}
        />
        <MetricCard
          label="Pendientes de revisión"
          value={pendingCount ?? 0}
          subtext={
            (pendingCount ?? 0) > 0
              ? 'Requieren atención'
              : undefined
          }
        />
        <MetricCard
          label="Tareas completadas (mes)"
          value={`${taskCompletionRate}%`}
          subtext={`${completedTasks} de ${totalTasks} tareas`}
        />
        <MetricCard
          label="Cobertura de turnos"
          value={`${coverageRate}%`}
          subtext={`${totalAssigned}/${totalCapacity} lugares asignados`}
        />
      </div>

      {/* Open tasks alert */}
      {openTasks > 0 && (
        <div className="mb-6 p-3 rounded bg-[var(--color-warning-bg)] border border-[var(--color-warning)] text-sm text-[var(--color-warning)]">
          {openTasks} tarea{openTasks === 1 ? '' : 's'} pendiente{openTasks === 1 ? '' : 's'} este mes
          {' '}·{' '}
          <a href="/admin/volunteers/tasks" className="underline">
            Ver tareas
          </a>
        </div>
      )}

      {/* Pending review alert */}
      {(pendingCount ?? 0) > 0 && (
        <div className="mb-6 p-3 rounded bg-[var(--color-info-bg)] border border-[var(--color-info)] text-sm text-[var(--color-info)]">
          {pendingCount} voluntario{(pendingCount ?? 0) === 1 ? '' : 's'} esperando revisión
          {' '}·{' '}
          <a href="/admin/volunteers?status=pending_review" className="underline">
            Revisar ahora
          </a>
        </div>
      )}

      {/* Quick links */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mb-8">
        {[
          { href: '/admin/volunteers', label: 'Ver voluntarios' },
          { href: '/admin/volunteers/shifts', label: 'Gestionar turnos' },
          { href: '/admin/volunteers/tasks', label: 'Ver tareas' },
          { href: '/admin/volunteers/shifts/new', label: 'Crear turno' },
          { href: '/admin/volunteers/tasks/new', label: 'Crear tarea' },
          { href: '/admin/volunteers?status=pending_review', label: 'Revisar inscripciones' },
        ].map(({ href, label }) => (
          <a
            key={href}
            href={href}
            className="block px-4 py-3 text-sm rounded border border-[var(--border)] text-[var(--text-primary)] hover:bg-[var(--bg-hover)] hover:border-[var(--color-primary)]"
          >
            {label}
          </a>
        ))}
      </div>

      {/* Recent volunteers */}
      <section>
        <h2 className="text-lg font-semibold text-[var(--text-primary)] mb-3">
          Voluntarios recientes
        </h2>
        <ul className="divide-y divide-[var(--border)]">
          {(recentVolunteers ?? []).map((v) => (
            <li key={v.id} className="py-3 flex items-center justify-between">
              <a
                href={`/admin/volunteers/${v.id}`}
                className="text-[var(--text-primary)] hover:text-[var(--color-primary)]"
              >
                {v.full_name}
              </a>
              <span className="text-xs text-[var(--text-secondary)]">
                {v.status} · {new Date(v.created_at).toLocaleDateString('es-PY')}
              </span>
            </li>
          ))}
        </ul>
      </section>
    </main>
  )
}
```

---

### Step 2 — Volunteer personal dashboard

**File**: `src/app/volunteers/dashboard/page.tsx`

```typescript
import { createServerComponentClient } from '@supabase/auth-helpers-nextjs'
import { cookies } from 'next/headers'
import { redirect } from 'next/navigation'
import { getStatusLabel } from '@/lib/tasks/validate-task-transition'
import type { TaskStatus } from '@/lib/tasks/types'

export default async function VolunteerDashboardPage() {
  const supabase = createServerComponentClient({ cookies })
  const { data: { user } } = await supabase.auth.getUser()

  if (!user) redirect('/auth/login')

  const today = new Date().toISOString().split('T')[0]

  // All queries scoped by RLS to authenticated user
  const [
    { data: profile },
    { data: upcomingShifts },
    { data: openTasks },
  ] = await Promise.all([
    supabase
      .from('volunteer_profiles')
      .select('full_name, status, hours_total')
      .eq('id', user.id)
      .maybeSingle(),

    // Upcoming shifts I'm signed up for
    supabase
      .from('shift_assignments')
      .select(`
        shift:volunteer_shifts(id, title, shift_date, start_time, end_time)
      `)
      .gte('volunteer_shifts.shift_date', today)
      .order('volunteer_shifts.shift_date', { ascending: true })
      .limit(3),

    // Open tasks assigned to me
    supabase
      .from('volunteer_tasks')
      .select('id, title, due_date, status')
      .neq('status', 'completed')
      .order('due_date', { ascending: true })
      .limit(5),
  ])

  if (!profile) redirect('/volunteers/profile')

  if (profile.status !== 'active') {
    return (
      <main className="max-w-xl mx-auto py-8 px-4 text-center">
        <h1 className="text-xl font-bold text-[var(--text-primary)] mb-2">
          Hola, {profile.full_name}
        </h1>
        <p className="text-[var(--text-secondary)]">
          Tu perfil está en estado <strong>{profile.status}</strong>.
          Recibirás una notificación cuando sea aprobado.
        </p>
      </main>
    )
  }

  return (
    <main className="max-w-2xl mx-auto py-8 px-4">
      <h1 className="text-2xl font-bold text-[var(--text-primary)] mb-1">
        Hola, {profile.full_name}
      </h1>
      <p className="text-sm text-[var(--text-secondary)] mb-6">
        Total de horas contribuidas: <strong>{profile.hours_total ?? 0}</strong>
      </p>

      {/* Upcoming shifts */}
      <section className="mb-8">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-lg font-semibold text-[var(--text-primary)]">Próximos turnos</h2>
          <a href="/volunteers/shifts" className="text-sm text-[var(--color-primary)] hover:underline">
            Ver todos
          </a>
        </div>

        {(upcomingShifts ?? []).length === 0 ? (
          <p className="text-sm text-[var(--text-secondary)]">
            No tenés turnos próximos.{' '}
            <a href="/volunteers/shifts" className="text-[var(--color-primary)] hover:underline">
              Ver turnos disponibles
            </a>
          </p>
        ) : (
          <ul className="space-y-2">
            {(upcomingShifts ?? []).map((a) => {
              const s = a.shift as {
                id: string
                title: string
                shift_date: string
                start_time: string
                end_time: string
              }
              return (
                <li
                  key={s.id}
                  className="bg-[var(--bg-card)] border border-[var(--border)] rounded p-3 text-sm"
                >
                  <span className="font-medium text-[var(--text-primary)]">{s.title}</span>
                  <span className="text-[var(--text-secondary)] ml-2">
                    {s.shift_date} · {s.start_time.slice(0, 5)}–{s.end_time.slice(0, 5)}
                  </span>
                </li>
              )
            })}
          </ul>
        )}
      </section>

      {/* Open tasks */}
      <section>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-lg font-semibold text-[var(--text-primary)]">Mis tareas</h2>
          <a href="/volunteers/tasks" className="text-sm text-[var(--color-primary)] hover:underline">
            Ver todas
          </a>
        </div>

        {(openTasks ?? []).length === 0 ? (
          <p className="text-sm text-[var(--text-secondary)]">No tenés tareas pendientes.</p>
        ) : (
          <ul className="space-y-2">
            {(openTasks ?? []).map((task) => (
              <li
                key={task.id}
                className="bg-[var(--bg-card)] border border-[var(--border)] rounded p-3 text-sm flex items-center justify-between"
              >
                <span className="text-[var(--text-primary)]">{task.title}</span>
                <span className="text-xs text-[var(--text-secondary)]">
                  {getStatusLabel(task.status as TaskStatus)} · {task.due_date}
                </span>
              </li>
            ))}
          </ul>
        )}
      </section>
    </main>
  )
}
```

---

### Step 3 — Per-volunteer admin summary (extend existing detail page)

The admin volunteer detail page (`/admin/volunteers/[id]/page.tsx`) created in S01/T03 should be extended to include a task and shift summary section. Add the following block inside the existing page Server Component, after the profile details:

```typescript
// Append to existing /admin/volunteers/[id]/page.tsx
// After fetching profile, also fetch:

const today = new Date().toISOString().split('T')[0]

const [{ data: assignedTasks }, { data: assignedShifts }] = await Promise.all([
  supabaseAdmin
    .from('volunteer_tasks')
    .select('id, title, due_date, status')
    .eq('assigned_to', params.id)
    .neq('status', 'completed')
    .order('due_date', { ascending: true })
    .limit(5),

  supabaseAdmin
    .from('shift_assignments')
    .select(`
      shift:volunteer_shifts(id, title, shift_date, start_time, end_time)
    `)
    .eq('volunteer_id', params.id)
    .gte('volunteer_shifts.shift_date', today)
    .order('volunteer_shifts.shift_date', { ascending: true })
    .limit(5),
])

// Render below the volunteer profile section:
// <h2>Tareas asignadas ({assignedTasks?.length ?? 0})</h2>
// <h2>Turnos próximos ({assignedShifts?.length ?? 0})</h2>
```

The exact JSX is part of the S01/T03 page extension — include as a collapsible or stacked section within the existing admin detail layout.

---

### Data flow summary

```
Admin visits /admin/volunteers/dashboard
  → Server Component runs all queries in parallel (Promise.all)
  → Computes: activeCount, pendingCount, taskCompletionRate, coverageRate
  → Renders MetricCards + alert banners + quick links
  → No client-side JS needed for initial data

Volunteer visits /volunteers/dashboard
  → Server Component: auth + profile check
  → Parallel queries: upcoming signed shifts + open tasks (RLS scoped)
  → Redirects to /volunteers/profile if profile missing
  → Shows inactive-state message if not yet active
```

---

### Files to create/update

| File | Action |
|------|--------|
| `src/app/admin/volunteers/dashboard/page.tsx` | CREATE |
| `src/app/volunteers/dashboard/page.tsx` | CREATE |
| `src/app/admin/volunteers/[id]/page.tsx` | UPDATE (add task + shift summary) |

## Related Issues

- EPIC-5
- S03
- Depends on: S01/T01 (volunteer_profiles), S01/T03 (isAdmin), S02/T01 (shifts), S02/T02 (assignments), S03/T01 (tasks)
