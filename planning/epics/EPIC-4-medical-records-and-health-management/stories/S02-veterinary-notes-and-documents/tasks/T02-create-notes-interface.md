---
task: T02
story: S02
epic: EPIC-4
title: Create notes interface
status: ready
priority: medium
created: 2026-03-25T17:13:26.730488
---

# T02: Create notes interface

## Description

Build the veterinary notes interface for the medical records section of an animal's profile. This includes a Server Component page that lists all medical records (notes) for an animal, a Server Action to create new records, and a Client Component form for staff/vets to add entries. Documents uploaded via S02/T01 are displayed per record. The interface lives at `/admin/animals/[id]/medical`.

## Acceptance Criteria

- [ ] `/admin/animals/[id]/medical` page renders all medical records for an animal, newest first
- [ ] Each record shows: date, record type label, vet name, weight/temperature if recorded, diagnosis/notes preview, and attached document count
- [ ] `CreateMedicalRecordForm` Client Component allows staff/vet to create a new record
- [ ] `createMedicalRecord` Server Action validates input, inserts row, revalidates path
- [ ] Confidential records are hidden from adopter view (enforced by RLS — no frontend logic needed)
- [ ] Empty state shown when no records exist
- [ ] Record type displayed as Spanish label (not raw enum value)
- [ ] Attached documents listed per record with download link (signed URL)
- [ ] Admin/staff/vet can expand a record to see full notes and documents
- [ ] Unit tests for `createMedicalRecord` Server Action validation

## Implementation Notes

### Page Route

```
src/app/admin/animals/[id]/medical/
  page.tsx                   ← Server Component (data fetching + layout)
  loading.tsx                ← Skeleton loader
```

### Types Used

```typescript
// src/types/medical.ts (from S01/T01 — already defined)
export type MedicalRecordType =
  | 'intake_exam'
  | 'checkup'
  | 'diagnosis'
  | 'follow_up'
  | 'discharge'
  | 'other'
```

### Constants

```typescript
// src/lib/medical-records/constants.ts
export const RECORD_TYPE_LABELS: Record<string, string> = {
  intake_exam: 'Examen de ingreso',
  checkup: 'Control rutinario',
  diagnosis: 'Diagnóstico',
  follow_up: 'Seguimiento',
  discharge: 'Alta médica',
  other: 'Otro',
}
```

### Server Action: `createMedicalRecord`

```typescript
// src/app/actions/medical-records.ts
'use server'

import { createServerActionClient } from '@supabase/auth-helpers-nextjs'
import { cookies } from 'next/headers'
import { revalidatePath } from 'next/cache'

interface CreateMedicalRecordInput {
  animalId: string
  veterinarianId: string | null
  recordType: string
  visitDate: string         // ISO date string YYYY-MM-DD
  weightKg: number | null
  temperatureC: number | null
  diagnosis: string | null
  notes: string | null
  isConfidential: boolean
}

interface CreateMedicalRecordResult {
  success: boolean
  recordId?: string
  error?: string
}

const VALID_RECORD_TYPES = [
  'intake_exam', 'checkup', 'diagnosis', 'follow_up', 'discharge', 'other',
] as const

export async function createMedicalRecord(
  input: CreateMedicalRecordInput
): Promise<CreateMedicalRecordResult> {
  const supabase = createServerActionClient({ cookies })

  const { data: { user } } = await supabase.auth.getUser()
  if (!user) return { success: false, error: 'No autenticado' }

  const { data: profile } = await supabase
    .from('profiles')
    .select('role')
    .eq('id', user.id)
    .single()

  if (!profile || !['staff', 'admin', 'vet'].includes(profile.role)) {
    return { success: false, error: 'Sin permisos para registrar notas médicas' }
  }

  if (!VALID_RECORD_TYPES.includes(input.recordType as typeof VALID_RECORD_TYPES[number])) {
    return { success: false, error: 'Tipo de registro inválido' }
  }

  if (!input.visitDate || !/^\d{4}-\d{2}-\d{2}$/.test(input.visitDate)) {
    return { success: false, error: 'Fecha de visita inválida' }
  }

  if (input.weightKg !== null && (input.weightKg <= 0 || input.weightKg > 999)) {
    return { success: false, error: 'Peso fuera de rango válido (0–999 kg)' }
  }

  if (input.temperatureC !== null && (input.temperatureC < 30 || input.temperatureC > 45)) {
    return { success: false, error: 'Temperatura fuera de rango válido (30–45 °C)' }
  }

  const { data: record, error: dbError } = await supabase
    .from('medical_records')
    .insert({
      animal_id: input.animalId,
      veterinarian_id: input.veterinarianId,
      record_type: input.recordType,
      visit_date: input.visitDate,
      weight_kg: input.weightKg,
      temperature_c: input.temperatureC,
      diagnosis: input.diagnosis || null,
      notes: input.notes || null,
      is_confidential: input.isConfidential,
      created_by: user.id,
    })
    .select('id')
    .single()

  if (dbError) {
    return { success: false, error: `Error al guardar registro: ${dbError.message}` }
  }

  revalidatePath(`/admin/animals/${input.animalId}/medical`)
  return { success: true, recordId: record.id }
}
```

### Page: `/admin/animals/[id]/medical/page.tsx`

```typescript
// src/app/admin/animals/[id]/medical/page.tsx
import { createServerComponentClient } from '@supabase/auth-helpers-nextjs'
import { cookies } from 'next/headers'
import { redirect } from 'next/navigation'
import { MedicalRecordList } from '@/components/medical/MedicalRecordList'
import { CreateMedicalRecordForm } from '@/components/medical/CreateMedicalRecordForm'

interface PageProps {
  params: { id: string }
}

export default async function AnimalMedicalPage({ params }: PageProps) {
  const supabase = createServerComponentClient({ cookies })

  const { data: { user } } = await supabase.auth.getUser()
  if (!user) redirect('/login')

  const { data: profile } = await supabase
    .from('profiles')
    .select('role')
    .eq('id', user.id)
    .single()

  // Adopters are handled by RLS on the query — they see only non-confidential records.
  // Completely unauthenticated users are redirected above.
  const canWrite = profile?.role && ['staff', 'admin', 'vet'].includes(profile.role)

  // Fetch animal name for header
  const { data: animal } = await supabase
    .from('animals')
    .select('id, name')
    .eq('id', params.id)
    .single()

  if (!animal) redirect('/admin/animals')

  // Fetch medical records with vet name and document count
  const { data: records } = await supabase
    .from('medical_records')
    .select(`
      id,
      record_type,
      visit_date,
      weight_kg,
      temperature_c,
      diagnosis,
      notes,
      is_confidential,
      created_at,
      veterinarians (
        id,
        full_name,
        clinic_name
      ),
      medical_documents (count)
    `)
    .eq('animal_id', params.id)
    .order('visit_date', { ascending: false })

  // Fetch active veterinarians for the create form dropdown
  const { data: veterinarians } = await supabase
    .from('veterinarians')
    .select('id, full_name, clinic_name, is_internal')
    .eq('is_active', true)
    .order('full_name')

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-[var(--text-primary)]">
          Historial médico — {animal.name}
        </h1>
      </div>

      {canWrite && (
        <CreateMedicalRecordForm
          animalId={params.id}
          veterinarians={veterinarians ?? []}
        />
      )}

      <MedicalRecordList
        records={records ?? []}
        animalId={params.id}
      />
    </div>
  )
}
```

### Client Component: `CreateMedicalRecordForm`

```typescript
// src/components/medical/CreateMedicalRecordForm.tsx
'use client'

import { useState } from 'react'
import { createMedicalRecord } from '@/app/actions/medical-records'
import { RECORD_TYPE_LABELS } from '@/lib/medical-records/constants'

interface Veterinarian {
  id: string
  full_name: string
  clinic_name: string | null
  is_internal: boolean
}

interface CreateMedicalRecordFormProps {
  animalId: string
  veterinarians: Veterinarian[]
}

export function CreateMedicalRecordForm({
  animalId,
  veterinarians,
}: CreateMedicalRecordFormProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [recordType, setRecordType] = useState('checkup')
  const [veterinarianId, setVeterinarianId] = useState('')
  const [visitDate, setVisitDate] = useState(
    new Date().toISOString().slice(0, 10)  // today
  )
  const [weightKg, setWeightKg] = useState('')
  const [temperatureC, setTemperatureC] = useState('')
  const [diagnosis, setDiagnosis] = useState('')
  const [notes, setNotes] = useState('')
  const [isConfidential, setIsConfidential] = useState(false)

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault()
    setIsSubmitting(true)
    setError(null)

    const result = await createMedicalRecord({
      animalId,
      veterinarianId: veterinarianId || null,
      recordType,
      visitDate,
      weightKg: weightKg ? parseFloat(weightKg) : null,
      temperatureC: temperatureC ? parseFloat(temperatureC) : null,
      diagnosis: diagnosis || null,
      notes: notes || null,
      isConfidential,
    })

    setIsSubmitting(false)

    if (!result.success) {
      setError(result.error ?? 'Error desconocido')
      return
    }

    // Reset form and close
    setRecordType('checkup')
    setVeterinarianId('')
    setVisitDate(new Date().toISOString().slice(0, 10))
    setWeightKg('')
    setTemperatureC('')
    setDiagnosis('')
    setNotes('')
    setIsConfidential(false)
    setIsOpen(false)
  }

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="rounded-md bg-[var(--color-primary)] px-4 py-2 text-sm font-medium text-white hover:bg-[var(--color-primary-hover)] transition-colors"
      >
        + Nueva nota médica
      </button>
    )
  }

  return (
    <div className="rounded-lg border border-[var(--border)] bg-[var(--bg-card)] p-6">
      <h2 className="mb-4 text-lg font-medium text-[var(--text-primary)]">
        Nueva nota médica
      </h2>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-[var(--text-primary)] mb-1">
              Tipo de registro
            </label>
            <select
              value={recordType}
              onChange={(e) => setRecordType(e.target.value)}
              className="w-full rounded-md border border-[var(--border)] bg-[var(--bg-input)] px-3 py-2 text-sm"
              disabled={isSubmitting}
              required
            >
              {Object.entries(RECORD_TYPE_LABELS).map(([value, label]) => (
                <option key={value} value={value}>{label}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-[var(--text-primary)] mb-1">
              Fecha de visita
            </label>
            <input
              type="date"
              value={visitDate}
              onChange={(e) => setVisitDate(e.target.value)}
              className="w-full rounded-md border border-[var(--border)] bg-[var(--bg-input)] px-3 py-2 text-sm"
              disabled={isSubmitting}
              required
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-[var(--text-primary)] mb-1">
            Veterinario
          </label>
          <select
            value={veterinarianId}
            onChange={(e) => setVeterinarianId(e.target.value)}
            className="w-full rounded-md border border-[var(--border)] bg-[var(--bg-input)] px-3 py-2 text-sm"
            disabled={isSubmitting}
          >
            <option value="">Sin veterinario asignado</option>
            {veterinarians.map((vet) => (
              <option key={vet.id} value={vet.id}>
                {vet.full_name}
                {vet.clinic_name ? ` — ${vet.clinic_name}` : ''}
                {vet.is_internal ? ' (interno)' : ''}
              </option>
            ))}
          </select>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-[var(--text-primary)] mb-1">
              Peso (kg)
            </label>
            <input
              type="number"
              value={weightKg}
              onChange={(e) => setWeightKg(e.target.value)}
              step="0.1"
              min="0.1"
              max="999"
              placeholder="Ej: 12.5"
              className="w-full rounded-md border border-[var(--border)] bg-[var(--bg-input)] px-3 py-2 text-sm"
              disabled={isSubmitting}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-[var(--text-primary)] mb-1">
              Temperatura (°C)
            </label>
            <input
              type="number"
              value={temperatureC}
              onChange={(e) => setTemperatureC(e.target.value)}
              step="0.1"
              min="30"
              max="45"
              placeholder="Ej: 38.5"
              className="w-full rounded-md border border-[var(--border)] bg-[var(--bg-input)] px-3 py-2 text-sm"
              disabled={isSubmitting}
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-[var(--text-primary)] mb-1">
            Diagnóstico
          </label>
          <input
            type="text"
            value={diagnosis}
            onChange={(e) => setDiagnosis(e.target.value)}
            placeholder="Hallazgos clínicos o diagnóstico"
            className="w-full rounded-md border border-[var(--border)] bg-[var(--bg-input)] px-3 py-2 text-sm"
            disabled={isSubmitting}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-[var(--text-primary)] mb-1">
            Notas
          </label>
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            rows={4}
            placeholder="Observaciones, indicaciones, próximos pasos..."
            className="w-full rounded-md border border-[var(--border)] bg-[var(--bg-input)] px-3 py-2 text-sm resize-none"
            disabled={isSubmitting}
          />
        </div>

        <div className="flex items-center gap-2">
          <input
            type="checkbox"
            id="isConfidential"
            checked={isConfidential}
            onChange={(e) => setIsConfidential(e.target.checked)}
            className="h-4 w-4 rounded border border-[var(--border)]"
            disabled={isSubmitting}
          />
          <label
            htmlFor="isConfidential"
            className="text-sm text-[var(--text-secondary)]"
          >
            Marcar como confidencial (no visible para adoptantes)
          </label>
        </div>

        {error && (
          <p className="text-sm text-[var(--color-error)]">{error}</p>
        )}

        <div className="flex gap-3 justify-end">
          <button
            type="button"
            onClick={() => setIsOpen(false)}
            className="rounded-md border border-[var(--border)] px-4 py-2 text-sm text-[var(--text-secondary)] hover:bg-[var(--bg-hover)] transition-colors"
            disabled={isSubmitting}
          >
            Cancelar
          </button>
          <button
            type="submit"
            className="rounded-md bg-[var(--color-primary)] px-4 py-2 text-sm font-medium text-white hover:bg-[var(--color-primary-hover)] transition-colors disabled:opacity-50"
            disabled={isSubmitting}
          >
            {isSubmitting ? 'Guardando...' : 'Guardar nota'}
          </button>
        </div>
      </form>
    </div>
  )
}
```

### Server Component: `MedicalRecordList`

```typescript
// src/components/medical/MedicalRecordList.tsx
import { RECORD_TYPE_LABELS } from '@/lib/medical-records/constants'
import { MedicalRecordCard } from './MedicalRecordCard'

interface MedicalRecord {
  id: string
  record_type: string
  visit_date: string
  weight_kg: number | null
  temperature_c: number | null
  diagnosis: string | null
  notes: string | null
  is_confidential: boolean
  created_at: string
  veterinarians: {
    id: string
    full_name: string
    clinic_name: string | null
  } | null
  medical_documents: { count: number }[]
}

interface MedicalRecordListProps {
  records: MedicalRecord[]
  animalId: string
}

export function MedicalRecordList({ records, animalId }: MedicalRecordListProps) {
  if (records.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-[var(--border)] p-12 text-center">
        <p className="text-sm text-[var(--text-secondary)]">
          No hay registros médicos para este animal.
        </p>
        <p className="mt-1 text-xs text-[var(--text-muted)]">
          Los registros aparecerán aquí una vez creados.
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {records.map((record) => (
        <MedicalRecordCard
          key={record.id}
          record={record}
          animalId={animalId}
        />
      ))}
    </div>
  )
}
```

### Client Component: `MedicalRecordCard`

```typescript
// src/components/medical/MedicalRecordCard.tsx
'use client'

import { useState } from 'react'
import { RECORD_TYPE_LABELS } from '@/lib/medical-records/constants'
import { MedicalDocumentList } from './MedicalDocumentList'

interface MedicalRecord {
  id: string
  record_type: string
  visit_date: string
  weight_kg: number | null
  temperature_c: number | null
  diagnosis: string | null
  notes: string | null
  is_confidential: boolean
  created_at: string
  veterinarians: {
    id: string
    full_name: string
    clinic_name: string | null
  } | null
  medical_documents: { count: number }[]
}

interface MedicalRecordCardProps {
  record: MedicalRecord
  animalId: string
}

export function MedicalRecordCard({ record, animalId }: MedicalRecordCardProps) {
  const [isExpanded, setIsExpanded] = useState(false)

  const documentCount = record.medical_documents[0]?.count ?? 0

  const formattedDate = new Date(record.visit_date + 'T00:00:00').toLocaleDateString('es-PY', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  })

  return (
    <div className="rounded-lg border border-[var(--border)] bg-[var(--bg-card)] overflow-hidden">
      {/* Card header — always visible */}
      <button
        className="w-full text-left px-5 py-4 flex items-start gap-4 hover:bg-[var(--bg-hover)] transition-colors"
        onClick={() => setIsExpanded((prev) => !prev)}
        aria-expanded={isExpanded}
      >
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-sm font-medium text-[var(--text-primary)]">
              {RECORD_TYPE_LABELS[record.record_type] ?? record.record_type}
            </span>
            {record.is_confidential && (
              <span className="inline-flex items-center rounded px-1.5 py-0.5 text-xs font-medium bg-[var(--bg-warning-subtle)] text-[var(--color-warning)]">
                Confidencial
              </span>
            )}
            {documentCount > 0 && (
              <span className="inline-flex items-center rounded px-1.5 py-0.5 text-xs text-[var(--text-muted)] bg-[var(--bg-subtle)]">
                {documentCount} {documentCount === 1 ? 'documento' : 'documentos'}
              </span>
            )}
          </div>

          <div className="mt-1 flex items-center gap-3 text-sm text-[var(--text-secondary)]">
            <span>{formattedDate}</span>
            {record.veterinarians && (
              <span>· {record.veterinarians.full_name}</span>
            )}
            {record.weight_kg !== null && (
              <span>· {record.weight_kg} kg</span>
            )}
            {record.temperature_c !== null && (
              <span>· {record.temperature_c} °C</span>
            )}
          </div>

          {record.diagnosis && !isExpanded && (
            <p className="mt-1 text-sm text-[var(--text-secondary)] truncate">
              {record.diagnosis}
            </p>
          )}
        </div>

        <svg
          className={[
            'h-4 w-4 text-[var(--text-muted)] flex-shrink-0 mt-0.5 transition-transform',
            isExpanded ? 'rotate-180' : '',
          ].join(' ')}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* Expanded detail */}
      {isExpanded && (
        <div className="px-5 pb-5 border-t border-[var(--border)] pt-4 space-y-4">
          {record.diagnosis && (
            <div>
              <p className="text-xs font-medium text-[var(--text-muted)] uppercase tracking-wide mb-1">
                Diagnóstico
              </p>
              <p className="text-sm text-[var(--text-primary)]">{record.diagnosis}</p>
            </div>
          )}

          {record.notes && (
            <div>
              <p className="text-xs font-medium text-[var(--text-muted)] uppercase tracking-wide mb-1">
                Notas
              </p>
              <p className="text-sm text-[var(--text-primary)] whitespace-pre-wrap">{record.notes}</p>
            </div>
          )}

          {documentCount > 0 && (
            <div>
              <p className="text-xs font-medium text-[var(--text-muted)] uppercase tracking-wide mb-2">
                Documentos adjuntos
              </p>
              <MedicalDocumentList
                medicalRecordId={record.id}
                animalId={animalId}
              />
            </div>
          )}
        </div>
      )}
    </div>
  )
}
```

### Server Component: `MedicalDocumentList`

Fetches documents for a specific record and generates signed URLs server-side.

```typescript
// src/components/medical/MedicalDocumentList.tsx
import { createServerComponentClient } from '@supabase/auth-helpers-nextjs'
import { cookies } from 'next/headers'
import { getSignedDocumentUrl } from '@/lib/medical-documents/get-signed-url'
import { DOCUMENT_TYPE_LABELS } from '@/lib/medical-documents/constants'

interface MedicalDocumentListProps {
  medicalRecordId: string
  animalId: string
}

export async function MedicalDocumentList({
  medicalRecordId,
}: MedicalDocumentListProps) {
  const supabase = createServerComponentClient({ cookies })

  const { data: documents } = await supabase
    .from('medical_documents')
    .select('id, file_name, file_type, file_size_bytes, document_type, description, created_at, storage_path')
    .eq('medical_record_id', medicalRecordId)
    .order('created_at', { ascending: true })

  if (!documents || documents.length === 0) return null

  // Generate signed URLs in parallel
  const withUrls = await Promise.all(
    documents.map(async (doc) => ({
      ...doc,
      signedUrl: await getSignedDocumentUrl(doc.storage_path),
    }))
  )

  return (
    <ul className="space-y-2">
      {withUrls.map((doc) => (
        <li
          key={doc.id}
          className="flex items-center gap-3 rounded-md border border-[var(--border)] bg-[var(--bg-subtle)] px-3 py-2"
        >
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-[var(--text-primary)] truncate">
              {doc.file_name}
            </p>
            <p className="text-xs text-[var(--text-muted)]">
              {DOCUMENT_TYPE_LABELS[doc.document_type] ?? doc.document_type}
              {doc.description ? ` — ${doc.description}` : ''}
              {' · '}
              {(doc.file_size_bytes / 1024).toFixed(0)} KB
            </p>
          </div>

          {doc.signedUrl && (
            <a
              href={doc.signedUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="flex-shrink-0 text-xs text-[var(--color-primary)] hover:underline"
            >
              Descargar
            </a>
          )}
        </li>
      ))}
    </ul>
  )
}
```

### Unit Tests for `createMedicalRecord` Validation

```typescript
// src/app/actions/__tests__/medical-records.test.ts
// Tests validation logic extracted from Server Action

import { validateMedicalRecordInput } from '@/lib/medical-records/validate-record'

describe('validateMedicalRecordInput', () => {
  const baseInput = {
    animalId: '00000000-0000-0000-0000-000000000001',
    veterinarianId: null,
    recordType: 'checkup',
    visitDate: '2026-04-01',
    weightKg: null,
    temperatureC: null,
    diagnosis: null,
    notes: null,
    isConfidential: false,
  }

  it('accepts a valid minimal input', () => {
    const result = validateMedicalRecordInput(baseInput)
    expect(result.valid).toBe(true)
  })

  it('rejects an invalid record type', () => {
    const result = validateMedicalRecordInput({ ...baseInput, recordType: 'broken' })
    expect(result.valid).toBe(false)
    expect(result.error).toContain('Tipo de registro inválido')
  })

  it('rejects a malformed visit date', () => {
    const result = validateMedicalRecordInput({ ...baseInput, visitDate: '01/04/2026' })
    expect(result.valid).toBe(false)
    expect(result.error).toContain('Fecha de visita inválida')
  })

  it('rejects weight of 0', () => {
    const result = validateMedicalRecordInput({ ...baseInput, weightKg: 0 })
    expect(result.valid).toBe(false)
    expect(result.error).toContain('Peso fuera de rango')
  })

  it('accepts weight within valid range', () => {
    const result = validateMedicalRecordInput({ ...baseInput, weightKg: 12.5 })
    expect(result.valid).toBe(true)
  })

  it('rejects temperature below 30°C', () => {
    const result = validateMedicalRecordInput({ ...baseInput, temperatureC: 29.9 })
    expect(result.valid).toBe(false)
    expect(result.error).toContain('Temperatura fuera de rango')
  })

  it('rejects temperature above 45°C', () => {
    const result = validateMedicalRecordInput({ ...baseInput, temperatureC: 45.1 })
    expect(result.valid).toBe(false)
    expect(result.error).toContain('Temperatura fuera de rango')
  })

  it('accepts valid temperature', () => {
    const result = validateMedicalRecordInput({ ...baseInput, temperatureC: 38.5 })
    expect(result.valid).toBe(true)
  })
})
```

### Pure Validation Function

```typescript
// src/lib/medical-records/validate-record.ts
const VALID_RECORD_TYPES = [
  'intake_exam', 'checkup', 'diagnosis', 'follow_up', 'discharge', 'other',
] as const

interface MedicalRecordInput {
  animalId: string
  veterinarianId: string | null
  recordType: string
  visitDate: string
  weightKg: number | null
  temperatureC: number | null
  diagnosis: string | null
  notes: string | null
  isConfidential: boolean
}

export function validateMedicalRecordInput(
  input: MedicalRecordInput
): { valid: boolean; error?: string } {
  if (!VALID_RECORD_TYPES.includes(input.recordType as typeof VALID_RECORD_TYPES[number])) {
    return { valid: false, error: 'Tipo de registro inválido' }
  }

  if (!input.visitDate || !/^\d{4}-\d{2}-\d{2}$/.test(input.visitDate)) {
    return { valid: false, error: 'Fecha de visita inválida' }
  }

  if (input.weightKg !== null && (input.weightKg <= 0 || input.weightKg > 999)) {
    return { valid: false, error: 'Peso fuera de rango válido (0–999 kg)' }
  }

  if (input.temperatureC !== null && (input.temperatureC < 30 || input.temperatureC > 45)) {
    return { valid: false, error: 'Temperatura fuera de rango válido (30–45 °C)' }
  }

  return { valid: true }
}
```

## Related Issues

- EPIC-4
- S02
- S01/T01 (medical_records table)
- S01/T02 (migrations)
- S02/T01 (document upload system — documents displayed per record here)
