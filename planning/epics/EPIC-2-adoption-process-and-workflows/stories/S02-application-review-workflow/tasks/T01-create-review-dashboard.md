---
task: T01
story: S02
epic: EPIC-2
title: Create staff adoption review dashboard
status: ready
priority: medium
agent_type: frontend
created: 2026-03-25T17:13:26.727892
---

# T01: Create staff adoption review dashboard

## Description

Build the adoption application review dashboard as a Next.js Server Component page at `/admin/adopciones`. The page fetches all submitted applications from Supabase (staff RLS policy allows this), renders them in a filterable table, and links to a per-application detail view. No client-side state store — filters use URL search params.

## Context

- Server Component by default — data fetched server-side via `createServerClient()`
- Supabase RLS: `staff_read_all_applications` policy allows `staff` and `admin` roles to SELECT all rows
- Status filter via URL search param `?status=submitted` — no `useState`, no Zustand
- CSS: Tailwind CSS 3.4.19 PINNED — use CSS vars, NOT hardcoded colors
- No Prisma, no ORM — raw Supabase queries only

## File structure

```
src/app/admin/adopciones/
├── page.tsx              # Server Component — fetches and renders application list
├── ApplicationTable.tsx  # Server Component — table with status badges
├── StatusFilter.tsx      # Client Component — filter buttons update URL params
└── [id]/
    └── page.tsx          # Server Component — full application detail view
```

## Files to create

### `src/app/admin/adopciones/page.tsx`

```typescript
import { createServerClient } from '@/lib/supabase/server'
import { redirect } from 'next/navigation'
import { ApplicationTable } from './ApplicationTable'
import { StatusFilter } from './StatusFilter'
import type { AdoptionApplicationStatus } from '@/types/adoption'

const VALID_STATUSES: AdoptionApplicationStatus[] = [
  'submitted', 'under_review', 'approved', 'rejected', 'withdrawn',
]

interface PageProps {
  searchParams: { status?: string }
}

export default async function AdopcionesAdminPage({ searchParams }: PageProps) {
  const supabase = await createServerClient()

  const { data: { user } } = await supabase.auth.getUser()
  if (!user) redirect('/login')

  const { data: profile } = await supabase
    .from('profiles')
    .select('role')
    .eq('id', user.id)
    .single()

  if (!profile || !['staff', 'admin'].includes(profile.role)) {
    redirect('/')
  }

  const statusFilter = VALID_STATUSES.includes(searchParams.status as AdoptionApplicationStatus)
    ? (searchParams.status as AdoptionApplicationStatus)
    : null

  let query = supabase
    .from('adoption_applications')
    .select('id, status, submitted_at, data, adopter_id')
    .order('submitted_at', { ascending: false })

  if (statusFilter) {
    query = query.eq('status', statusFilter)
  }

  const { data: applications, error } = await query

  if (error) {
    return (
      <p className="text-[var(--color-error)]">
        Error al cargar solicitudes: {error.message}
      </p>
    )
  }

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-[var(--text-primary)] mb-6">
        Solicitudes de Adopción
      </h1>
      <StatusFilter currentStatus={statusFilter} statuses={VALID_STATUSES} />
      <ApplicationTable applications={applications ?? []} />
    </div>
  )
}
```

### `src/app/admin/adopciones/ApplicationTable.tsx`

```typescript
import Link from 'next/link'
import type { AdoptionApplicationStatus } from '@/types/adoption'

const STATUS_LABELS: Record<AdoptionApplicationStatus, string> = {
  draft: 'Borrador',
  submitted: 'Enviada',
  under_review: 'En revisión',
  approved: 'Aprobada',
  rejected: 'Rechazada',
  withdrawn: 'Retirada',
}

const STATUS_COLORS: Record<AdoptionApplicationStatus, string> = {
  draft: 'bg-[var(--bg-hover)] text-[var(--text-tertiary)]',
  submitted: 'bg-blue-100 text-blue-800',
  under_review: 'bg-yellow-100 text-yellow-800',
  approved: 'bg-green-100 text-green-800',
  rejected: 'bg-red-100 text-red-800',
  withdrawn: 'bg-[var(--bg-hover)] text-[var(--text-secondary)]',
}

interface ApplicationRow {
  id: string
  status: AdoptionApplicationStatus
  submitted_at: string | null
  data: { adopter?: { fullName?: string; email?: string } }
}

interface ApplicationTableProps {
  applications: ApplicationRow[]
}

export function ApplicationTable({ applications }: ApplicationTableProps) {
  if (applications.length === 0) {
    return (
      <p className="mt-8 text-center text-[var(--text-tertiary)]">
        No hay solicitudes para mostrar.
      </p>
    )
  }

  return (
    <div className="mt-6 overflow-x-auto rounded-xl border border-[var(--border-default)]">
      <table className="w-full text-sm">
        <thead className="bg-[var(--bg-card)] border-b border-[var(--border-default)]">
          <tr>
            <th className="px-4 py-3 text-left text-[var(--text-secondary)] font-medium">Solicitante</th>
            <th className="px-4 py-3 text-left text-[var(--text-secondary)] font-medium">Email</th>
            <th className="px-4 py-3 text-left text-[var(--text-secondary)] font-medium">Estado</th>
            <th className="px-4 py-3 text-left text-[var(--text-secondary)] font-medium">Enviada</th>
            <th className="px-4 py-3 text-left text-[var(--text-secondary)] font-medium">Acción</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-[var(--border-default)]">
          {applications.map((app) => (
            <tr key={app.id} className="hover:bg-[var(--bg-hover)]">
              <td className="px-4 py-3 text-[var(--text-primary)]">
                {app.data.adopter?.fullName ?? '—'}
              </td>
              <td className="px-4 py-3 text-[var(--text-secondary)]">
                {app.data.adopter?.email ?? '—'}
              </td>
              <td className="px-4 py-3">
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${STATUS_COLORS[app.status]}`}>
                  {STATUS_LABELS[app.status]}
                </span>
              </td>
              <td className="px-4 py-3 text-[var(--text-secondary)]">
                {app.submitted_at
                  ? new Date(app.submitted_at).toLocaleDateString('es-PY')
                  : '—'}
              </td>
              <td className="px-4 py-3">
                <Link
                  href={`/admin/adopciones/${app.id}`}
                  className="text-[var(--color-primary)] hover:underline text-sm"
                >
                  Ver detalle
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
```

### `src/app/admin/adopciones/StatusFilter.tsx`

```typescript
'use client'

import { useRouter, usePathname, useSearchParams } from 'next/navigation'
import type { AdoptionApplicationStatus } from '@/types/adoption'

const STATUS_LABELS: Record<AdoptionApplicationStatus, string> = {
  draft: 'Borrador',
  submitted: 'Enviadas',
  under_review: 'En revisión',
  approved: 'Aprobadas',
  rejected: 'Rechazadas',
  withdrawn: 'Retiradas',
}

interface StatusFilterProps {
  currentStatus: AdoptionApplicationStatus | null
  statuses: AdoptionApplicationStatus[]
}

export function StatusFilter({ currentStatus, statuses }: StatusFilterProps) {
  const router = useRouter()
  const pathname = usePathname()
  const searchParams = useSearchParams()

  function setStatus(status: AdoptionApplicationStatus | null) {
    const params = new URLSearchParams(searchParams.toString())
    if (status) {
      params.set('status', status)
    } else {
      params.delete('status')
    }
    router.push(`${pathname}?${params.toString()}`)
  }

  return (
    <div className="flex flex-wrap gap-2">
      <button
        onClick={() => setStatus(null)}
        className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors
          ${!currentStatus
            ? 'bg-[var(--color-primary)] text-white'
            : 'bg-[var(--bg-hover)] text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
          }`}
      >
        Todas
      </button>
      {statuses.map((status) => (
        <button
          key={status}
          onClick={() => setStatus(status)}
          className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors
            ${currentStatus === status
              ? 'bg-[var(--color-primary)] text-white'
              : 'bg-[var(--bg-hover)] text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
            }`}
        >
          {STATUS_LABELS[status]}
        </button>
      ))}
    </div>
  )
}
```

### `src/app/admin/adopciones/[id]/page.tsx`

```typescript
import { createServerClient } from '@/lib/supabase/server'
import { redirect, notFound } from 'next/navigation'
import Link from 'next/link'
import type { AdoptionApplicationRow } from '@/types/adoption'

interface PageProps {
  params: { id: string }
}

export default async function AdoptionDetailPage({ params }: PageProps) {
  const supabase = await createServerClient()

  const { data: { user } } = await supabase.auth.getUser()
  if (!user) redirect('/login')

  const { data: profile } = await supabase
    .from('profiles')
    .select('role')
    .eq('id', user.id)
    .single()

  if (!profile || !['staff', 'admin'].includes(profile.role)) {
    redirect('/')
  }

  const { data: application } = await supabase
    .from('adoption_applications')
    .select('*')
    .eq('id', params.id)
    .single<AdoptionApplicationRow>()

  if (!application) notFound()

  const { data: adopter } = await supabase
    .from('adoption_applications')
    .select('data')
    .eq('id', params.id)
    .single()

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <Link
        href="/admin/adopciones"
        className="text-sm text-[var(--text-tertiary)] hover:text-[var(--text-primary)] mb-6 inline-block"
      >
        ← Volver a solicitudes
      </Link>
      <h1 className="text-2xl font-bold text-[var(--text-primary)] mb-2">
        Solicitud de Adopción
      </h1>
      <p className="text-xs text-[var(--text-tertiary)] mb-6">ID: {application.id}</p>

      <div className="bg-[var(--bg-card)] rounded-xl p-6 space-y-4 border border-[var(--border-default)]">
        <pre className="text-xs text-[var(--text-secondary)] overflow-auto">
          {JSON.stringify(application.data, null, 2)}
        </pre>
      </div>

      {/* Approve/reject actions are implemented in T02 */}
    </div>
  )
}
```

## Acceptance Criteria

- [ ] `/admin/adopciones` page only accessible to `staff` and `admin` roles — non-staff redirected to `/`
- [ ] Applications fetched server-side via Supabase — no client-side fetch
- [ ] Status filter updates URL search param `?status=` without full page reload
- [ ] Table shows applicant name, email, status badge, submitted date, detail link
- [ ] Status badges use CSS vars — no hardcoded Tailwind color classes except semantic (blue/green/red for status)
- [ ] Empty state shown when no applications match filter
- [ ] Detail page `/admin/adopciones/[id]` renders full `data` JSONB — `notFound()` on missing ID
- [ ] TypeScript: no type errors in any file

## Implementation Notes

- The `VALID_STATUSES` whitelist in `page.tsx` prevents arbitrary SQL injection via `searchParams.status`. Always validate search params before using them in queries.
- `StatusFilter.tsx` must be `'use client'` because it calls `useRouter` — but it receives its initial state from the Server Component via props, not from its own fetch.
- The detail page shows raw JSON for now — T02 adds the approve/reject action buttons.
- `profiles.role` column is assumed from EPIC-0 auth setup.

## Related

- Depends on: S01/T01 (table `adoption_applications`), EPIC-0 (auth + profiles table with role)
- T02 adds approve/reject actions to the detail page
- Part of: S02 — Application Review Workflow
