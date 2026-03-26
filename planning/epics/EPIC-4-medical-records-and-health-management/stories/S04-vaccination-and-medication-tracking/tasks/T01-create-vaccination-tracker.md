---
task: T01
story: S04
epic: EPIC-4
title: Create vaccination tracker
status: ready
priority: medium
created: 2026-03-25T17:13:26.730943
---

# T01: Create vaccination tracker

## Description

Build a vaccination tracker at `/admin/animals/[id]/medical/vaccinations` that lets staff and vets log administered vaccines, view upcoming due dates, and see overdue alerts. The `vaccinations` table is already defined in S01/T01 migrations; this task implements the UI and Server Actions on top of it.

## Acceptance Criteria

- [x] Vaccination list shows all administered vaccines for an animal, sorted by date_administered descending
- [x] Each row shows: vaccine name, date administered, batch number (if any), next_due_date, status badge (Overdue / Vigente / Próxima)
- [x] "Registrar vacuna" form: vaccine_name (required), date_administered (required, ISO date), next_due_date (optional), batch_number (optional), administered_by (optional free text for vet name if not in system)
- [x] `createVaccination` Server Action validates input, inserts into `vaccinations` table, calls `revalidatePath`
- [x] Validation: vaccine_name non-empty, date_administered valid ISO date not in the future, next_due_date (if provided) after date_administered
- [x] Status badge computed server-side from today's date vs. next_due_date: `overdue` (past due), `upcoming` (due within 30 days), `current` (due > 30 days away), `no_date` (no next_due_date)
- [x] Overdue vaccines shown with visual alert styling
- [x] Pure validation function is unit-tested
- [x] Implementation complete
- [x] Tests written and passing

## Implementation Notes

### vaccinations Table (from S01/T01)

```sql
create table vaccinations (
  id                  uuid primary key default gen_random_uuid(),
  animal_id           uuid not null references animals(id) on delete cascade,
  vaccine_name        text not null,
  date_administered   date not null,
  next_due_date       date,
  batch_number        text,
  administered_by     text,  -- free text: vet name or clinic
  notes               text,
  created_by          uuid not null references profiles(id),
  created_at          timestamptz not null default now(),
  updated_at          timestamptz not null default now()
);
```

### TypeScript Types

```typescript
// src/lib/vaccinations/types.ts

export type VaccinationStatus = 'overdue' | 'upcoming' | 'current' | 'no_date'

export interface Vaccination {
  id: string
  animal_id: string
  vaccine_name: string
  date_administered: string   // 'YYYY-MM-DD'
  next_due_date: string | null
  batch_number: string | null
  administered_by: string | null
  notes: string | null
  created_at: string
}

export interface VaccinationWithStatus extends Vaccination {
  status: VaccinationStatus
}

export interface CreateVaccinationInput {
  animalId: string
  vaccineName: string
  dateAdministered: string
  nextDueDate: string | null
  batchNumber: string | null
  administeredBy: string | null
  notes: string | null
}
```

### Vaccination Status Logic — Pure Function

```typescript
// src/lib/vaccinations/compute-status.ts

import type { VaccinationStatus } from './types'

export const UPCOMING_THRESHOLD_DAYS = 30

export function computeVaccinationStatus(
  nextDueDate: string | null,
  today: string  // 'YYYY-MM-DD' — injected for testability
): VaccinationStatus {
  if (!nextDueDate) return 'no_date'
  if (nextDueDate < today) return 'overdue'
  const daysUntilDue = daysBetween(today, nextDueDate)
  if (daysUntilDue <= UPCOMING_THRESHOLD_DAYS) return 'upcoming'
  return 'current'
}

// Returns the number of calendar days from dateA to dateB
// Both are 'YYYY-MM-DD' strings
export function daysBetween(dateA: string, dateB: string): number {
  const a = new Date(`${dateA}T00:00:00Z`)
  const b = new Date(`${dateB}T00:00:00Z`)
  return Math.round((b.getTime() - a.getTime()) / (1000 * 60 * 60 * 24))
}
```

### Validation — Pure Function

```typescript
// src/lib/vaccinations/validate-vaccination.ts

const ISO_DATE_RE = /^\d{4}-\d{2}-\d{2}$/

export interface VaccinationValidationInput {
  vaccineName: string
  dateAdministered: string
  nextDueDate: string | null
}

export function validateVaccinationInput(
  input: VaccinationValidationInput,
  today: string  // 'YYYY-MM-DD' — injected so tests are deterministic
): { valid: boolean; error?: string } {
  if (!input.vaccineName || input.vaccineName.trim().length === 0) {
    return { valid: false, error: 'El nombre de la vacuna es requerido' }
  }

  if (!ISO_DATE_RE.test(input.dateAdministered)) {
    return { valid: false, error: 'Fecha de administración inválida (usar AAAA-MM-DD)' }
  }

  if (input.dateAdministered > today) {
    return { valid: false, error: 'La fecha de administración no puede ser futura' }
  }

  if (input.nextDueDate !== null) {
    if (!ISO_DATE_RE.test(input.nextDueDate)) {
      return { valid: false, error: 'Fecha de próxima dosis inválida (usar AAAA-MM-DD)' }
    }
    if (input.nextDueDate <= input.dateAdministered) {
      return { valid: false, error: 'La próxima dosis debe ser posterior a la fecha de administración' }
    }
  }

  return { valid: true }
}
```

### Server Action

```typescript
// src/app/actions/vaccinations.ts
'use server'
import { revalidatePath } from 'next/cache'
import { createServerClient } from '@/lib/supabase/server'
import { validateVaccinationInput } from '@/lib/vaccinations/validate-vaccination'
import type { CreateVaccinationInput } from '@/lib/vaccinations/types'

export type CreateVaccinationResult =
  | { success: true }
  | { success: false; error: string }

export async function createVaccination(
  input: CreateVaccinationInput
): Promise<CreateVaccinationResult> {
  const supabase = createServerClient()

  const { data: { user } } = await supabase.auth.getUser()
  if (!user) return { success: false, error: 'No autenticado' }

  const { data: profile } = await supabase
    .from('profiles')
    .select('role')
    .eq('id', user.id)
    .single()

  if (!profile || !['staff', 'admin', 'vet'].includes(profile.role)) {
    return { success: false, error: 'Sin permisos para registrar vacunas' }
  }

  const today = new Date().toISOString().slice(0, 10)  // 'YYYY-MM-DD'
  const validation = validateVaccinationInput(
    {
      vaccineName:       input.vaccineName,
      dateAdministered:  input.dateAdministered,
      nextDueDate:       input.nextDueDate,
    },
    today
  )
  if (!validation.valid) {
    return { success: false, error: validation.error! }
  }

  const { error } = await supabase.from('vaccinations').insert({
    animal_id:          input.animalId,
    vaccine_name:       input.vaccineName.trim(),
    date_administered:  input.dateAdministered,
    next_due_date:      input.nextDueDate,
    batch_number:       input.batchNumber?.trim() || null,
    administered_by:    input.administeredBy?.trim() || null,
    notes:              input.notes?.trim() || null,
    created_by:         user.id,
  })

  if (error) {
    return { success: false, error: 'Error al registrar la vacuna' }
  }

  revalidatePath(`/admin/animals/${input.animalId}/medical/vaccinations`)
  revalidatePath(`/admin/animals/${input.animalId}/medical/timeline`)
  return { success: true }
}
```

### Page — Server Component

```typescript
// src/app/admin/animals/[id]/medical/vaccinations/page.tsx
import { createServerClient } from '@/lib/supabase/server'
import { notFound } from 'next/navigation'
import { MedicalTabNav } from '@/components/medical/MedicalTabNav'
import { VaccinationList } from '@/components/vaccinations/VaccinationList'
import { CreateVaccinationForm } from '@/components/vaccinations/CreateVaccinationForm'
import {
  computeVaccinationStatus,
} from '@/lib/vaccinations/compute-status'
import type { VaccinationWithStatus } from '@/lib/vaccinations/types'

interface Props {
  params: { id: string }
}

export default async function AnimalVaccinationsPage({ params }: Props) {
  const supabase = createServerClient()

  const { data: animal } = await supabase
    .from('animals')
    .select('id, name')
    .eq('id', params.id)
    .single()

  if (!animal) notFound()

  const { data: vaccinations } = await supabase
    .from('vaccinations')
    .select('id, vaccine_name, date_administered, next_due_date, batch_number, administered_by, notes, created_at')
    .eq('animal_id', params.id)
    .order('date_administered', { ascending: false })

  const today = new Date().toISOString().slice(0, 10)

  const withStatus: VaccinationWithStatus[] = (vaccinations ?? []).map((v) => ({
    ...v,
    animal_id: params.id,
    status: computeVaccinationStatus(v.next_due_date, today),
  }))

  return (
    <div className="space-y-[var(--spacing-6)]">
      <h1 className="text-[var(--text-primary)] text-2xl font-semibold">
        Vacunas — {animal.name}
      </h1>

      <MedicalTabNav animalId={params.id} activeTab="vaccinations" />

      <CreateVaccinationForm animalId={params.id} />

      <VaccinationList vaccinations={withStatus} />
    </div>
  )
}
```

### Vaccination List — Server Component

```typescript
// src/components/vaccinations/VaccinationList.tsx
import { VaccinationStatusBadge } from '@/components/vaccinations/VaccinationStatusBadge'
import type { VaccinationWithStatus } from '@/lib/vaccinations/types'

interface Props {
  vaccinations: VaccinationWithStatus[]
}

const STATUS_ROW_CLASS: Record<string, string> = {
  overdue:   'bg-[var(--color-danger-subtle)] border-[var(--color-danger)]',
  upcoming:  'bg-[var(--color-warning-subtle)] border-[var(--color-warning)]',
  current:   'bg-[var(--bg-card)] border-[var(--border-default)]',
  no_date:   'bg-[var(--bg-card)] border-[var(--border-default)]',
}

export function VaccinationList({ vaccinations }: Props) {
  if (vaccinations.length === 0) {
    return (
      <div className="rounded-[var(--radius-md)] border border-[var(--border-default)] p-[var(--spacing-8)] text-center">
        <p className="text-[var(--text-muted)] text-sm">
          Sin vacunas registradas todavía.
        </p>
      </div>
    )
  }

  return (
    <ul className="space-y-[var(--spacing-2)]">
      {vaccinations.map((v) => {
        const [yr, mo, dy] = v.date_administered.split('-')
        const displayDate = `${dy}/${mo}/${yr}`
        let displayDue = '—'
        if (v.next_due_date) {
          const [yr2, mo2, dy2] = v.next_due_date.split('-')
          displayDue = `${dy2}/${mo2}/${yr2}`
        }

        return (
          <li
            key={v.id}
            className={[
              'flex items-start justify-between gap-[var(--spacing-4)]',
              'rounded-[var(--radius-md)] border p-[var(--spacing-3)]',
              STATUS_ROW_CLASS[v.status],
            ].join(' ')}
          >
            <div className="flex-1 min-w-0">
              <p className="text-[var(--text-primary)] text-sm font-medium truncate">
                {v.vaccine_name}
              </p>
              <p className="text-[var(--text-muted)] text-xs mt-0.5">
                Aplicada: {displayDate}
                {v.administered_by ? ` · ${v.administered_by}` : ''}
                {v.batch_number ? ` · Lote: ${v.batch_number}` : ''}
              </p>
              <p className="text-[var(--text-muted)] text-xs">
                Próxima dosis: {displayDue}
              </p>
            </div>
            <VaccinationStatusBadge status={v.status} />
          </li>
        )
      })}
    </ul>
  )
}
```

### Status Badge Component

```typescript
// src/components/vaccinations/VaccinationStatusBadge.tsx
import type { VaccinationStatus } from '@/lib/vaccinations/types'

const BADGE_LABELS: Record<VaccinationStatus, string> = {
  overdue:  'Vencida',
  upcoming: 'Próxima',
  current:  'Vigente',
  no_date:  'Sin fecha',
}

const BADGE_CLASSES: Record<VaccinationStatus, string> = {
  overdue:  'bg-[var(--color-danger)] text-[var(--color-danger-text)]',
  upcoming: 'bg-[var(--color-warning)] text-[var(--color-warning-text)]',
  current:  'bg-[var(--color-success)] text-[var(--color-success-text)]',
  no_date:  'bg-[var(--color-neutral)] text-[var(--color-neutral-text)]',
}

interface Props {
  status: VaccinationStatus
}

export function VaccinationStatusBadge({ status }: Props) {
  return (
    <span
      className={[
        'shrink-0 inline-block px-[var(--spacing-2)] py-0.5',
        'text-xs font-semibold rounded-full',
        BADGE_CLASSES[status],
      ].join(' ')}
    >
      {BADGE_LABELS[status]}
    </span>
  )
}
```

### Create Vaccination Form — Client Component

```typescript
// src/components/vaccinations/CreateVaccinationForm.tsx
'use client'
import { useState, useTransition } from 'react'
import { createVaccination } from '@/app/actions/vaccinations'

interface Props {
  animalId: string
}

export function CreateVaccinationForm({ animalId }: Props) {
  const [isOpen, setIsOpen] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isPending, startTransition] = useTransition()

  function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const form = e.currentTarget
    const fd = new FormData(form)

    const nextDueDateRaw = fd.get('nextDueDate') as string
    startTransition(async () => {
      const result = await createVaccination({
        animalId,
        vaccineName:      (fd.get('vaccineName') as string).trim(),
        dateAdministered: fd.get('dateAdministered') as string,
        nextDueDate:      nextDueDateRaw || null,
        batchNumber:      (fd.get('batchNumber') as string) || null,
        administeredBy:   (fd.get('administeredBy') as string) || null,
        notes:            (fd.get('notes') as string) || null,
      })
      if (!result.success) {
        setError(result.error)
      } else {
        setError(null)
        setIsOpen(false)
        form.reset()
      }
    })
  }

  if (!isOpen) {
    return (
      <button
        type="button"
        onClick={() => setIsOpen(true)}
        className="rounded-[var(--radius-sm)] bg-[var(--color-primary)] text-[var(--color-primary-text)] px-[var(--spacing-4)] py-[var(--spacing-2)] text-sm font-medium"
      >
        + Registrar vacuna
      </button>
    )
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="rounded-[var(--radius-md)] border border-[var(--border-default)] bg-[var(--bg-card)] p-[var(--spacing-4)] space-y-[var(--spacing-4)]"
    >
      <h3 className="text-[var(--text-primary)] font-semibold">Registrar vacuna</h3>

      {error && (
        <p role="alert" className="text-[var(--color-danger)] text-sm">{error}</p>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-[var(--spacing-4)]">
        <div className="flex flex-col gap-1">
          <label htmlFor="vaccineName" className="text-xs font-medium text-[var(--text-muted)]">
            Vacuna *
          </label>
          <input
            id="vaccineName"
            name="vaccineName"
            type="text"
            required
            placeholder="Ej: Rabia, Parvovirus"
            className="rounded-[var(--radius-sm)] border border-[var(--border-default)] bg-[var(--bg-input)] px-[var(--spacing-3)] py-[var(--spacing-2)] text-sm text-[var(--text-primary)]"
          />
        </div>

        <div className="flex flex-col gap-1">
          <label htmlFor="dateAdministered" className="text-xs font-medium text-[var(--text-muted)]">
            Fecha de aplicación *
          </label>
          <input
            id="dateAdministered"
            name="dateAdministered"
            type="date"
            required
            className="rounded-[var(--radius-sm)] border border-[var(--border-default)] bg-[var(--bg-input)] px-[var(--spacing-3)] py-[var(--spacing-2)] text-sm text-[var(--text-primary)]"
          />
        </div>

        <div className="flex flex-col gap-1">
          <label htmlFor="nextDueDate" className="text-xs font-medium text-[var(--text-muted)]">
            Próxima dosis
          </label>
          <input
            id="nextDueDate"
            name="nextDueDate"
            type="date"
            className="rounded-[var(--radius-sm)] border border-[var(--border-default)] bg-[var(--bg-input)] px-[var(--spacing-3)] py-[var(--spacing-2)] text-sm text-[var(--text-primary)]"
          />
        </div>

        <div className="flex flex-col gap-1">
          <label htmlFor="batchNumber" className="text-xs font-medium text-[var(--text-muted)]">
            Número de lote
          </label>
          <input
            id="batchNumber"
            name="batchNumber"
            type="text"
            placeholder="Ej: B-2026-0032"
            className="rounded-[var(--radius-sm)] border border-[var(--border-default)] bg-[var(--bg-input)] px-[var(--spacing-3)] py-[var(--spacing-2)] text-sm text-[var(--text-primary)]"
          />
        </div>

        <div className="flex flex-col gap-1 sm:col-span-2">
          <label htmlFor="administeredBy" className="text-xs font-medium text-[var(--text-muted)]">
            Administrado por
          </label>
          <input
            id="administeredBy"
            name="administeredBy"
            type="text"
            placeholder="Nombre del veterinario o clínica"
            className="rounded-[var(--radius-sm)] border border-[var(--border-default)] bg-[var(--bg-input)] px-[var(--spacing-3)] py-[var(--spacing-2)] text-sm text-[var(--text-primary)]"
          />
        </div>

        <div className="flex flex-col gap-1 sm:col-span-2">
          <label htmlFor="notes" className="text-xs font-medium text-[var(--text-muted)]">
            Notas
          </label>
          <textarea
            id="notes"
            name="notes"
            rows={2}
            className="rounded-[var(--radius-sm)] border border-[var(--border-default)] bg-[var(--bg-input)] px-[var(--spacing-3)] py-[var(--spacing-2)] text-sm text-[var(--text-primary)]"
          />
        </div>
      </div>

      <div className="flex gap-[var(--spacing-2)]">
        <button
          type="submit"
          disabled={isPending}
          className="rounded-[var(--radius-sm)] bg-[var(--color-primary)] text-[var(--color-primary-text)] px-[var(--spacing-4)] py-[var(--spacing-2)] text-sm font-medium disabled:opacity-50"
        >
          {isPending ? 'Guardando…' : 'Guardar'}
        </button>
        <button
          type="button"
          onClick={() => { setIsOpen(false); setError(null) }}
          className="rounded-[var(--radius-sm)] border border-[var(--border-default)] text-[var(--text-muted)] px-[var(--spacing-4)] py-[var(--spacing-2)] text-sm"
        >
          Cancelar
        </button>
      </div>
    </form>
  )
}
```

### Unit Tests

```typescript
// src/lib/vaccinations/__tests__/validate-vaccination.test.ts
import { validateVaccinationInput } from '@/lib/vaccinations/validate-vaccination'

const TODAY = '2026-03-25'

describe('validateVaccinationInput', () => {
  it('rejects empty vaccine name', () => {
    const r = validateVaccinationInput({ vaccineName: '  ', dateAdministered: '2026-03-10', nextDueDate: null }, TODAY)
    expect(r.valid).toBe(false)
    expect(r.error).toMatch(/nombre/)
  })

  it('rejects malformed date_administered', () => {
    const r = validateVaccinationInput({ vaccineName: 'Rabia', dateAdministered: '10/03/2026', nextDueDate: null }, TODAY)
    expect(r.valid).toBe(false)
  })

  it('rejects future date_administered', () => {
    const r = validateVaccinationInput({ vaccineName: 'Rabia', dateAdministered: '2026-12-31', nextDueDate: null }, TODAY)
    expect(r.valid).toBe(false)
    expect(r.error).toMatch(/futura/)
  })

  it('accepts today as date_administered', () => {
    const r = validateVaccinationInput({ vaccineName: 'Rabia', dateAdministered: TODAY, nextDueDate: null }, TODAY)
    expect(r.valid).toBe(true)
  })

  it('rejects next_due_date before date_administered', () => {
    const r = validateVaccinationInput({ vaccineName: 'Rabia', dateAdministered: '2026-03-10', nextDueDate: '2026-03-09' }, TODAY)
    expect(r.valid).toBe(false)
  })

  it('rejects next_due_date equal to date_administered', () => {
    const r = validateVaccinationInput({ vaccineName: 'Rabia', dateAdministered: '2026-03-10', nextDueDate: '2026-03-10' }, TODAY)
    expect(r.valid).toBe(false)
  })

  it('accepts valid input with next_due_date', () => {
    const r = validateVaccinationInput({ vaccineName: 'Rabia', dateAdministered: '2026-03-10', nextDueDate: '2027-03-10' }, TODAY)
    expect(r.valid).toBe(true)
  })
})

// src/lib/vaccinations/__tests__/compute-status.test.ts
import { computeVaccinationStatus, daysBetween } from '@/lib/vaccinations/compute-status'

describe('computeVaccinationStatus', () => {
  it('returns no_date when next_due_date is null', () => {
    expect(computeVaccinationStatus(null, '2026-03-25')).toBe('no_date')
  })

  it('returns overdue when next_due_date is in the past', () => {
    expect(computeVaccinationStatus('2026-03-01', '2026-03-25')).toBe('overdue')
  })

  it('returns upcoming when due within 30 days', () => {
    expect(computeVaccinationStatus('2026-04-10', '2026-03-25')).toBe('upcoming')
  })

  it('returns current when due more than 30 days away', () => {
    expect(computeVaccinationStatus('2027-03-25', '2026-03-25')).toBe('current')
  })

  it('returns upcoming on the exact 30-day boundary', () => {
    expect(computeVaccinationStatus('2026-04-24', '2026-03-25')).toBe('upcoming')
  })
})

describe('daysBetween', () => {
  it('returns 0 for same date', () => {
    expect(daysBetween('2026-03-25', '2026-03-25')).toBe(0)
  })

  it('returns correct positive count', () => {
    expect(daysBetween('2026-03-25', '2026-03-27')).toBe(2)
  })
})
```

### Files to Create

| File | Type | Purpose |
|------|------|---------|
| `src/lib/vaccinations/types.ts` | Types | `Vaccination`, `VaccinationWithStatus`, `VaccinationStatus`, `CreateVaccinationInput` |
| `src/lib/vaccinations/validate-vaccination.ts` | Utility | Pure `validateVaccinationInput()` function |
| `src/lib/vaccinations/compute-status.ts` | Utility | `computeVaccinationStatus()`, `daysBetween()` |
| `src/app/actions/vaccinations.ts` | Server Action | `createVaccination()` with auth/role/validation/insert |
| `src/app/admin/animals/[id]/medical/vaccinations/page.tsx` | Server Component | Vaccination tracker page |
| `src/components/vaccinations/VaccinationList.tsx` | Server Component | Renders vaccination list with overdue styling |
| `src/components/vaccinations/VaccinationStatusBadge.tsx` | Server Component | Status badge (Vencida / Próxima / Vigente / Sin fecha) |
| `src/components/vaccinations/CreateVaccinationForm.tsx` | Client Component | Form toggle + controlled form |
| `src/lib/vaccinations/__tests__/validate-vaccination.test.ts` | Test | 7 unit tests for validation |
| `src/lib/vaccinations/__tests__/compute-status.test.ts` | Test | 6 unit tests for status computation |

## Related Issues

- EPIC-4
- S04
