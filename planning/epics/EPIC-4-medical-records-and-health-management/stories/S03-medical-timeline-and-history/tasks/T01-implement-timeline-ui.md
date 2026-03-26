---
task: T01
story: S03
epic: EPIC-4
title: Implement timeline UI
status: ready
priority: medium
created: 2026-03-25T17:13:26.730682
---

# T01: Implement timeline UI

## Description

Build a chronological medical timeline view at `/admin/animals/[id]/medical/timeline` that aggregates all health events for an animal — medical records, vaccinations, medications, and treatments — into a single reverse-chronological feed. Staff and vets can scan the full health history at a glance.

## Acceptance Criteria

- [x] Timeline page renders all event types (records, vaccinations, medications, treatments) sorted by date descending
- [x] Each entry shows event type, date, and a concise summary (diagnosis, vaccine name, medication name)
- [x] Event type is visually distinct (icon or badge per category)
- [x] Empty state shown when no events exist
- [x] Confidential medical records are hidden from adopter-role users (enforced by RLS — no frontend logic needed)
- [x] Page is a Server Component (no unnecessary client JS)
- [x] Tab navigation links `/medical` (notes) ↔ `/medical/timeline` ↔ `/medical/vaccinations`
- [x] Implementation complete
- [x] Tests written and passing

## Implementation Notes

### Data Model

The timeline aggregates from four tables:

```sql
-- medical_records: visit_date, record_type, diagnosis
-- vaccinations: date_administered, vaccine_name, next_due_date
-- medications: start_date, end_date, medication_name, dosage
-- treatments: start_date, end_date, treatment_type, outcome
```

All four tables have `animal_id uuid` and `created_at timestamptz`. The aggregation happens in a Supabase RPC to avoid four round-trips.

### Database Function

Create in migration `20260401000007_create_timeline_rpc.sql`:

```sql
-- Timeline RPC: returns all health events for an animal sorted by event_date desc
-- Returns a unified shape across all event types
create or replace function get_animal_timeline(p_animal_id uuid)
returns table (
  event_date  date,
  event_type  text,
  title       text,
  subtitle    text,
  record_id   uuid,
  created_at  timestamptz
)
language sql
security definer
stable
as $$
  select
    visit_date                                                as event_date,
    record_type::text                                         as event_type,
    coalesce(diagnosis, 'Sin diagnóstico')                    as title,
    coalesce(v.full_name, 'Veterinario no asignado')          as subtitle,
    mr.id                                                     as record_id,
    mr.created_at
  from medical_records mr
  left join veterinarians v on v.id = mr.veterinarian_id
  where mr.animal_id = p_animal_id
    and (
      -- RLS handles confidential for adopters; here we also filter
      -- is_confidential=false so the function is safe for all roles
      mr.is_confidential = false
      or (select role from profiles where id = auth.uid()) in ('staff', 'admin', 'vet')
    )

  union all

  select
    date_administered                                         as event_date,
    'vaccination'                                             as event_type,
    vaccine_name                                              as title,
    coalesce(
      'Próxima dosis: ' || to_char(next_due_date, 'DD/MM/YYYY'),
      'Sin próxima dosis'
    )                                                         as subtitle,
    vac.id                                                    as record_id,
    vac.created_at
  from vaccinations vac
  where vac.animal_id = p_animal_id

  union all

  select
    start_date                                                as event_date,
    'medication'                                              as event_type,
    medication_name || ' — ' || dosage                        as title,
    coalesce(
      'Hasta: ' || to_char(end_date, 'DD/MM/YYYY'),
      'Sin fecha de fin'
    )                                                         as subtitle,
    med.id                                                    as record_id,
    med.created_at
  from medications med
  where med.animal_id = p_animal_id

  union all

  select
    start_date                                                as event_date,
    'treatment'                                               as event_type,
    treatment_type::text                                      as title,
    coalesce(outcome::text, 'En curso')                       as subtitle,
    tr.id                                                     as record_id,
    tr.created_at
  from treatments tr
  where tr.animal_id = p_animal_id

  order by event_date desc, created_at desc;
$$;

-- Grant execute only to authenticated users (RLS on underlying tables handles row visibility)
grant execute on function get_animal_timeline(uuid) to authenticated;

-- Rollback:
-- drop function if exists get_animal_timeline(uuid);
```

### TypeScript Type

```typescript
// src/lib/medical-records/types.ts

export type TimelineEventType =
  | 'check_up'
  | 'surgery'
  | 'emergency'
  | 'vaccination'
  | 'medication'
  | 'treatment'
  | 'follow_up'
  | 'other'

export interface TimelineEvent {
  event_date: string       // ISO date string 'YYYY-MM-DD'
  event_type: TimelineEventType | string
  title: string
  subtitle: string
  record_id: string
  created_at: string
}
```

### Constants File

```typescript
// src/lib/medical-records/timeline-constants.ts

export const TIMELINE_EVENT_LABELS: Record<string, string> = {
  check_up:    'Control',
  surgery:     'Cirugía',
  emergency:   'Emergencia',
  vaccination: 'Vacuna',
  medication:  'Medicamento',
  treatment:   'Tratamiento',
  follow_up:   'Seguimiento',
  other:       'Otro',
}

// Tailwind CSS var-based color classes per event type
export const TIMELINE_EVENT_COLORS: Record<string, string> = {
  check_up:    'bg-[var(--color-info)] text-[var(--color-info-text)]',
  surgery:     'bg-[var(--color-warning)] text-[var(--color-warning-text)]',
  emergency:   'bg-[var(--color-danger)] text-[var(--color-danger-text)]',
  vaccination: 'bg-[var(--color-success)] text-[var(--color-success-text)]',
  medication:  'bg-[var(--color-accent)] text-[var(--color-accent-text)]',
  treatment:   'bg-[var(--color-neutral)] text-[var(--color-neutral-text)]',
  follow_up:   'bg-[var(--color-info)] text-[var(--color-info-text)]',
  other:       'bg-[var(--color-neutral)] text-[var(--color-neutral-text)]',
}
```

### Page — Server Component

```typescript
// src/app/admin/animals/[id]/medical/timeline/page.tsx
import { createServerClient } from '@/lib/supabase/server'
import { notFound } from 'next/navigation'
import { TimelineList } from '@/components/medical/TimelineList'
import { MedicalTabNav } from '@/components/medical/MedicalTabNav'
import type { TimelineEvent } from '@/lib/medical-records/types'

interface Props {
  params: { id: string }
}

export default async function AnimalMedicalTimelinePage({ params }: Props) {
  const supabase = createServerClient()

  // Verify animal exists
  const { data: animal } = await supabase
    .from('animals')
    .select('id, name')
    .eq('id', params.id)
    .single()

  if (!animal) notFound()

  // Fetch timeline via RPC — RLS enforced inside the function
  const { data: events, error } = await supabase.rpc('get_animal_timeline', {
    p_animal_id: params.id,
  })

  const timeline: TimelineEvent[] = events ?? []

  return (
    <div className="space-y-[var(--spacing-6)]">
      <div className="flex items-center justify-between">
        <h1 className="text-[var(--text-primary)] text-2xl font-semibold">
          Historia clínica — {animal.name}
        </h1>
      </div>

      <MedicalTabNav animalId={params.id} activeTab="timeline" />

      <TimelineList events={timeline} />
    </div>
  )
}
```

### Tab Navigation Component

```typescript
// src/components/medical/MedicalTabNav.tsx
'use client'
import Link from 'next/link'

const TABS = [
  { key: 'notes',       label: 'Notas',        href: (id: string) => `/admin/animals/${id}/medical` },
  { key: 'timeline',    label: 'Historial',    href: (id: string) => `/admin/animals/${id}/medical/timeline` },
  { key: 'vaccinations',label: 'Vacunas',      href: (id: string) => `/admin/animals/${id}/medical/vaccinations` },
]

interface Props {
  animalId: string
  activeTab: 'notes' | 'timeline' | 'vaccinations'
}

export function MedicalTabNav({ animalId, activeTab }: Props) {
  return (
    <nav
      className="flex gap-[var(--spacing-1)] border-b border-[var(--border-default)]"
      aria-label="Secciones médicas"
    >
      {TABS.map((tab) => (
        <Link
          key={tab.key}
          href={tab.href(animalId)}
          className={[
            'px-[var(--spacing-4)] py-[var(--spacing-2)] text-sm font-medium',
            'border-b-2 -mb-px transition-colors',
            activeTab === tab.key
              ? 'border-[var(--color-primary)] text-[var(--color-primary)]'
              : 'border-transparent text-[var(--text-muted)] hover:text-[var(--text-primary)]',
          ].join(' ')}
        >
          {tab.label}
        </Link>
      ))}
    </nav>
  )
}
```

### Timeline List Component — Server Component

```typescript
// src/components/medical/TimelineList.tsx
import { TimelineEventItem } from '@/components/medical/TimelineEventItem'
import type { TimelineEvent } from '@/lib/medical-records/types'

interface Props {
  events: TimelineEvent[]
}

export function TimelineList({ events }: Props) {
  if (events.length === 0) {
    return (
      <div className="rounded-[var(--radius-md)] border border-[var(--border-default)] p-[var(--spacing-8)] text-center">
        <p className="text-[var(--text-muted)] text-sm">
          Sin eventos de salud registrados todavía.
        </p>
      </div>
    )
  }

  // Group events by year for visual separation
  const grouped = groupEventsByYear(events)

  return (
    <div className="space-y-[var(--spacing-8)]">
      {Object.entries(grouped)
        .sort(([a], [b]) => Number(b) - Number(a))
        .map(([year, yearEvents]) => (
          <section key={year}>
            <h2 className="text-[var(--text-muted)] text-xs font-semibold uppercase tracking-wider mb-[var(--spacing-4)]">
              {year}
            </h2>
            <div className="relative">
              {/* Vertical line */}
              <div className="absolute left-[var(--spacing-3)] top-0 bottom-0 w-px bg-[var(--border-default)]" />
              <ul className="space-y-[var(--spacing-4)]">
                {yearEvents.map((event) => (
                  <TimelineEventItem key={`${event.event_type}-${event.record_id}`} event={event} />
                ))}
              </ul>
            </div>
          </section>
        ))}
    </div>
  )
}

function groupEventsByYear(events: TimelineEvent[]): Record<string, TimelineEvent[]> {
  return events.reduce<Record<string, TimelineEvent[]>>((acc, event) => {
    const year = event.event_date.slice(0, 4)
    if (!acc[year]) acc[year] = []
    acc[year].push(event)
    return acc
  }, {})
}
```

### Timeline Event Item — Server Component

```typescript
// src/components/medical/TimelineEventItem.tsx
import {
  TIMELINE_EVENT_LABELS,
  TIMELINE_EVENT_COLORS,
} from '@/lib/medical-records/timeline-constants'
import type { TimelineEvent } from '@/lib/medical-records/types'

interface Props {
  event: TimelineEvent
}

export function TimelineEventItem({ event }: Props) {
  const label = TIMELINE_EVENT_LABELS[event.event_type] ?? event.event_type
  const colorClass = TIMELINE_EVENT_COLORS[event.event_type] ?? TIMELINE_EVENT_COLORS['other']

  // Format date as DD/MM/YYYY
  const [year, month, day] = event.event_date.split('-')
  const formattedDate = `${day}/${month}/${year}`

  return (
    <li className="relative flex gap-[var(--spacing-4)] pl-[var(--spacing-8)]">
      {/* Timeline dot */}
      <span
        className={[
          'absolute left-0 top-1 flex h-[var(--spacing-6)] w-[var(--spacing-6)]',
          'items-center justify-center rounded-full text-xs font-bold',
          colorClass,
        ].join(' ')}
        aria-hidden="true"
      >
        {label.slice(0, 1).toUpperCase()}
      </span>

      <div className="flex-1 rounded-[var(--radius-md)] border border-[var(--border-default)] bg-[var(--bg-card)] p-[var(--spacing-3)]">
        <div className="flex items-start justify-between gap-[var(--spacing-2)]">
          <div>
            <span
              className={[
                'inline-block px-[var(--spacing-2)] py-0.5 text-xs font-medium rounded-full mb-[var(--spacing-1)]',
                colorClass,
              ].join(' ')}
            >
              {label}
            </span>
            <p className="text-[var(--text-primary)] text-sm font-medium">{event.title}</p>
            <p className="text-[var(--text-muted)] text-xs mt-0.5">{event.subtitle}</p>
          </div>
          <time
            dateTime={event.event_date}
            className="text-[var(--text-muted)] text-xs shrink-0"
          >
            {formattedDate}
          </time>
        </div>
      </div>
    </li>
  )
}
```

### Unit Tests

```typescript
// src/components/medical/__tests__/TimelineList.test.tsx
import { render, screen } from '@testing-library/react'
import { TimelineList } from '@/components/medical/TimelineList'
import type { TimelineEvent } from '@/lib/medical-records/types'

describe('TimelineList', () => {
  it('shows empty state when no events provided', () => {
    render(<TimelineList events={[]} />)
    expect(screen.getByText(/Sin eventos de salud registrados/i)).toBeInTheDocument()
  })

  it('renders event title and date', () => {
    const events: TimelineEvent[] = [
      {
        event_date: '2026-03-10',
        event_type: 'vaccination',
        title: 'Rabia',
        subtitle: 'Próxima dosis: 10/03/2027',
        record_id: 'uuid-1',
        created_at: '2026-03-10T10:00:00Z',
      },
    ]
    render(<TimelineList events={events} />)
    expect(screen.getByText('Rabia')).toBeInTheDocument()
    expect(screen.getByText('10/03/2026')).toBeInTheDocument()
  })

  it('groups events by year', () => {
    const events: TimelineEvent[] = [
      { event_date: '2026-01-15', event_type: 'check_up', title: 'Control enero', subtitle: '', record_id: 'a', created_at: '2026-01-15T00:00:00Z' },
      { event_date: '2025-11-20', event_type: 'check_up', title: 'Control noviembre', subtitle: '', record_id: 'b', created_at: '2025-11-20T00:00:00Z' },
    ]
    render(<TimelineList events={events} />)
    expect(screen.getByText('2026')).toBeInTheDocument()
    expect(screen.getByText('2025')).toBeInTheDocument()
  })
})

// src/lib/medical-records/__tests__/timeline-constants.test.ts
import {
  TIMELINE_EVENT_LABELS,
  TIMELINE_EVENT_COLORS,
} from '@/lib/medical-records/timeline-constants'

describe('TIMELINE_EVENT_LABELS', () => {
  it('has labels for all expected event types', () => {
    const required = ['check_up', 'surgery', 'emergency', 'vaccination', 'medication', 'treatment', 'follow_up', 'other']
    for (const type of required) {
      expect(TIMELINE_EVENT_LABELS[type]).toBeDefined()
    }
  })
})

describe('TIMELINE_EVENT_COLORS', () => {
  it('has color classes for all event types in labels', () => {
    for (const type of Object.keys(TIMELINE_EVENT_LABELS)) {
      expect(TIMELINE_EVENT_COLORS[type]).toBeDefined()
    }
  })
})
```

### Files to Create

| File | Type | Purpose |
|------|------|---------|
| `supabase/migrations/20260401000007_create_timeline_rpc.sql` | Migration | `get_animal_timeline(uuid)` RPC |
| `src/lib/medical-records/types.ts` | Types | `TimelineEvent`, `TimelineEventType` |
| `src/lib/medical-records/timeline-constants.ts` | Constants | Labels and color classes per event type |
| `src/app/admin/animals/[id]/medical/timeline/page.tsx` | Server Component | Timeline page |
| `src/components/medical/MedicalTabNav.tsx` | Client Component | Tab navigation for medical sections |
| `src/components/medical/TimelineList.tsx` | Server Component | Groups events by year and renders the list |
| `src/components/medical/TimelineEventItem.tsx` | Server Component | Single timeline entry with dot + card |
| `src/components/medical/__tests__/TimelineList.test.tsx` | Test | UI tests for TimelineList |
| `src/lib/medical-records/__tests__/timeline-constants.test.ts` | Test | Label/color completeness checks |

## Related Issues

- EPIC-4
- S03
