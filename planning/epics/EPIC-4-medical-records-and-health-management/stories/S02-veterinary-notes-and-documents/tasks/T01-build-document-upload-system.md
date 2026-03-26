---
task: T01
story: S02
epic: EPIC-4
title: Build document upload system
status: ready
priority: medium
created: 2026-03-25T17:13:26.730421
---

# T01: Build document upload system

## Description

Build the document upload system for veterinary files attached to medical records — lab results, X-rays, surgical reports, vaccination certificates (PDFs and images). Use Supabase Storage with a private bucket. Documents are linked to a `medical_documents` table that stores metadata and the storage path. Upload is handled via a Server Action. Files are served via signed URLs with short expiry.

## Acceptance Criteria

- [ ] `medical_documents` table created with FK to `medical_records.id`
- [ ] Supabase Storage bucket `medical-documents` created as private
- [ ] Storage RLS policies: staff/admin/vet can upload; staff/admin/vet can read; adopters cannot access
- [ ] `uploadMedicalDocument` Server Action validates file type and size before upload
- [ ] `MedicalDocumentUploader` Client Component: drag-and-drop or click-to-upload, progress indicator
- [ ] Signed URL generation for download (1-hour expiry)
- [ ] `deleteMedicalDocument` Server Action removes both storage object and DB row
- [ ] Accepted types: PDF, JPEG, PNG, WEBP — max 10MB per file
- [ ] Unit tests for Server Action validation logic

## Implementation Notes

### Table: `medical_documents`

```sql
-- supabase/migrations/20260401000009_create_medical_documents.sql

create table medical_documents (
  id                uuid primary key default gen_random_uuid(),
  medical_record_id uuid not null references medical_records(id) on delete cascade,
  animal_id         uuid not null references animals(id) on delete cascade,
  storage_path      text not null,       -- path within the medical-documents bucket
  file_name         text not null,       -- original file name for display
  file_type         text not null,       -- MIME type: application/pdf, image/jpeg, etc.
  file_size_bytes   int not null,
  document_type     text not null check (document_type in (
                      'lab_result', 'xray', 'surgical_report',
                      'vaccination_certificate', 'prescription', 'other'
                    )),
  description       text,
  uploaded_by       uuid not null references auth.users(id),
  created_at        timestamptz not null default now()
  -- no updated_at: documents are immutable after upload (delete and re-upload to replace)
);

create index medical_documents_medical_record_id_idx on medical_documents(medical_record_id);
create index medical_documents_animal_id_idx on medical_documents(animal_id);

alter table medical_documents enable row level security;

-- Staff/admin/vet: full read + insert
create policy "staff_admin_vet_read_medical_documents"
  on medical_documents for select
  using (
    exists (
      select 1 from profiles
      where profiles.id = auth.uid()
        and profiles.role in ('staff', 'admin', 'vet')
    )
  );

create policy "staff_admin_vet_insert_medical_documents"
  on medical_documents for insert
  with check (
    exists (
      select 1 from profiles
      where profiles.id = auth.uid()
        and profiles.role in ('staff', 'admin', 'vet')
    )
  );

-- Only admin can delete documents (soft delete via archiving is preferred)
create policy "admin_delete_medical_documents"
  on medical_documents for delete
  using (
    exists (
      select 1 from profiles
      where profiles.id = auth.uid()
        and profiles.role = 'admin'
    )
  );
```

### Supabase Storage Bucket

Create via migration or Supabase Studio:

```sql
-- supabase/migrations/20260401000010_create_medical_documents_bucket.sql
insert into storage.buckets (id, name, public)
values ('medical-documents', 'medical-documents', false);
-- public = false: files are not accessible via public URL; require signed URLs

-- Storage RLS: staff/admin/vet can upload
create policy "staff_admin_vet_upload_medical_documents"
  on storage.objects for insert
  to authenticated
  with check (
    bucket_id = 'medical-documents'
    and exists (
      select 1 from profiles
      where profiles.id = auth.uid()
        and profiles.role in ('staff', 'admin', 'vet')
    )
  );

-- Staff/admin/vet can read (download)
create policy "staff_admin_vet_read_medical_documents_storage"
  on storage.objects for select
  to authenticated
  using (
    bucket_id = 'medical-documents'
    and exists (
      select 1 from profiles
      where profiles.id = auth.uid()
        and profiles.role in ('staff', 'admin', 'vet')
    )
  );

-- Only admin can delete from storage
create policy "admin_delete_medical_documents_storage"
  on storage.objects for delete
  to authenticated
  using (
    bucket_id = 'medical-documents'
    and exists (
      select 1 from profiles
      where profiles.id = auth.uid()
        and profiles.role = 'admin'
    )
  );
```

### Constants

```typescript
// src/lib/medical-documents/constants.ts
export const MEDICAL_DOCUMENT_BUCKET = 'medical-documents'
export const MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  // 10MB
export const SIGNED_URL_EXPIRY_SECONDS = 3600         // 1 hour

export const ACCEPTED_MIME_TYPES = [
  'application/pdf',
  'image/jpeg',
  'image/png',
  'image/webp',
] as const

export type AcceptedMimeType = typeof ACCEPTED_MIME_TYPES[number]

export const DOCUMENT_TYPE_LABELS: Record<string, string> = {
  lab_result: 'Resultado de laboratorio',
  xray: 'Radiografía',
  surgical_report: 'Informe quirúrgico',
  vaccination_certificate: 'Certificado de vacunación',
  prescription: 'Receta médica',
  other: 'Otro documento',
}
```

### Server Action: `uploadMedicalDocument`

```typescript
// src/app/actions/medical-documents.ts
'use server'

import { createServerActionClient } from '@supabase/auth-helpers-nextjs'
import { cookies } from 'next/headers'
import { revalidatePath } from 'next/cache'
import {
  MEDICAL_DOCUMENT_BUCKET,
  MAX_FILE_SIZE_BYTES,
  ACCEPTED_MIME_TYPES,
  type AcceptedMimeType,
} from '@/lib/medical-documents/constants'

interface UploadDocumentInput {
  medicalRecordId: string
  animalId: string
  documentType: string
  description: string | null
  file: File
}

interface UploadDocumentResult {
  success: boolean
  documentId?: string
  error?: string
}

export async function uploadMedicalDocument(
  input: UploadDocumentInput
): Promise<UploadDocumentResult> {
  const supabase = createServerActionClient({ cookies })

  const { data: { user } } = await supabase.auth.getUser()
  if (!user) return { success: false, error: 'No autenticado' }

  const { data: profile } = await supabase
    .from('profiles')
    .select('role')
    .eq('id', user.id)
    .single()

  if (!profile || !['staff', 'admin', 'vet'].includes(profile.role)) {
    return { success: false, error: 'Sin permisos para subir documentos médicos' }
  }

  // Validate file type
  if (!ACCEPTED_MIME_TYPES.includes(input.file.type as AcceptedMimeType)) {
    return {
      success: false,
      error: `Tipo de archivo no permitido. Tipos aceptados: PDF, JPEG, PNG, WEBP`,
    }
  }

  // Validate file size
  if (input.file.size > MAX_FILE_SIZE_BYTES) {
    return {
      success: false,
      error: `El archivo supera el límite de 10MB (${(input.file.size / 1024 / 1024).toFixed(1)}MB)`,
    }
  }

  // Build storage path: animal_id/record_id/timestamp_filename
  const timestamp = Date.now()
  const safeFileName = input.file.name.replace(/[^a-zA-Z0-9._-]/g, '_')
  const storagePath = `${input.animalId}/${input.medicalRecordId}/${timestamp}_${safeFileName}`

  const { error: storageError } = await supabase.storage
    .from(MEDICAL_DOCUMENT_BUCKET)
    .upload(storagePath, input.file, {
      contentType: input.file.type,
      upsert: false,
    })

  if (storageError) {
    return { success: false, error: `Error al subir archivo: ${storageError.message}` }
  }

  // Insert metadata row
  const { data: doc, error: dbError } = await supabase
    .from('medical_documents')
    .insert({
      medical_record_id: input.medicalRecordId,
      animal_id: input.animalId,
      storage_path: storagePath,
      file_name: input.file.name,
      file_type: input.file.type,
      file_size_bytes: input.file.size,
      document_type: input.documentType,
      description: input.description,
      uploaded_by: user.id,
    })
    .select('id')
    .single()

  if (dbError) {
    // Rollback: remove the uploaded file if DB insert fails
    await supabase.storage.from(MEDICAL_DOCUMENT_BUCKET).remove([storagePath])
    return { success: false, error: `Error al registrar documento: ${dbError.message}` }
  }

  revalidatePath(`/admin/animals/${input.animalId}/medical`)
  return { success: true, documentId: doc.id }
}
```

### Signed URL Utility

```typescript
// src/lib/medical-documents/get-signed-url.ts
import { createServerComponentClient } from '@supabase/auth-helpers-nextjs'
import { cookies } from 'next/headers'
import { MEDICAL_DOCUMENT_BUCKET, SIGNED_URL_EXPIRY_SECONDS } from './constants'

export async function getSignedDocumentUrl(storagePath: string): Promise<string | null> {
  const supabase = createServerComponentClient({ cookies })

  const { data, error } = await supabase.storage
    .from(MEDICAL_DOCUMENT_BUCKET)
    .createSignedUrl(storagePath, SIGNED_URL_EXPIRY_SECONDS)

  if (error || !data) return null
  return data.signedUrl
}
```

### Client Component: `MedicalDocumentUploader`

```typescript
// src/components/medical/MedicalDocumentUploader.tsx
'use client'

import { useState, useRef } from 'react'
import { uploadMedicalDocument } from '@/app/actions/medical-documents'
import { ACCEPTED_MIME_TYPES, DOCUMENT_TYPE_LABELS } from '@/lib/medical-documents/constants'

interface MedicalDocumentUploaderProps {
  medicalRecordId: string
  animalId: string
  onUploadSuccess: (documentId: string) => void
}

export function MedicalDocumentUploader({
  medicalRecordId,
  animalId,
  onUploadSuccess,
}: MedicalDocumentUploaderProps) {
  const [isUploading, setIsUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [documentType, setDocumentType] = useState('other')
  const [description, setDescription] = useState('')
  const [isDragOver, setIsDragOver] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  async function handleFile(file: File) {
    setIsUploading(true)
    setError(null)

    const result = await uploadMedicalDocument({
      medicalRecordId,
      animalId,
      documentType,
      description: description || null,
      file,
    })

    setIsUploading(false)

    if (!result.success) {
      setError(result.error ?? 'Error desconocido al subir documento')
      return
    }

    setDescription('')
    onUploadSuccess(result.documentId!)
  }

  function handleDrop(event: React.DragEvent<HTMLDivElement>) {
    event.preventDefault()
    setIsDragOver(false)
    const file = event.dataTransfer.files[0]
    if (file) handleFile(file)
  }

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-[var(--text-primary)] mb-1">
            Tipo de documento
          </label>
          <select
            value={documentType}
            onChange={(e) => setDocumentType(e.target.value)}
            className="w-full rounded-md border border-[var(--border)] bg-[var(--bg-input)] px-3 py-2 text-sm"
            disabled={isUploading}
          >
            {Object.entries(DOCUMENT_TYPE_LABELS).map(([value, label]) => (
              <option key={value} value={value}>{label}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-[var(--text-primary)] mb-1">
            Descripción (opcional)
          </label>
          <input
            type="text"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="w-full rounded-md border border-[var(--border)] bg-[var(--bg-input)] px-3 py-2 text-sm"
            placeholder="Ej: Radiografía de cadera izquierda"
            disabled={isUploading}
          />
        </div>
      </div>

      <div
        className={[
          'rounded-lg border-2 border-dashed p-8 text-center cursor-pointer transition-colors',
          isDragOver
            ? 'border-[var(--color-primary)] bg-[var(--bg-primary-subtle)]'
            : 'border-[var(--border)] hover:border-[var(--border-hover)]',
          isUploading ? 'opacity-50 pointer-events-none' : '',
        ].join(' ')}
        onDragOver={(e) => { e.preventDefault(); setIsDragOver(true) }}
        onDragLeave={() => setIsDragOver(false)}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <p className="text-sm text-[var(--text-secondary)]">
          {isUploading
            ? 'Subiendo documento...'
            : 'Arrastra un archivo aquí o haz clic para seleccionar'}
        </p>
        <p className="mt-1 text-xs text-[var(--text-muted)]">
          PDF, JPEG, PNG, WEBP — máximo 10MB
        </p>
        <input
          ref={fileInputRef}
          type="file"
          accept={ACCEPTED_MIME_TYPES.join(',')}
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0]
            if (file) handleFile(file)
          }}
          disabled={isUploading}
        />
      </div>

      {error && (
        <p className="text-sm text-[var(--color-error)]">{error}</p>
      )}
    </div>
  )
}
```

### Unit Tests for Upload Validation

```typescript
// src/app/actions/__tests__/medical-documents.test.ts
// Test the validation logic (not the Supabase calls — mock those)

import { validateUploadInput } from '@/lib/medical-documents/validate-upload'
import { MAX_FILE_SIZE_BYTES } from '@/lib/medical-documents/constants'

describe('validateUploadInput', () => {
  it('rejects files exceeding 10MB', () => {
    const oversizedFile = new File(['x'.repeat(MAX_FILE_SIZE_BYTES + 1)], 'big.pdf', {
      type: 'application/pdf',
    })
    const result = validateUploadInput(oversizedFile)
    expect(result.valid).toBe(false)
    expect(result.error).toContain('10MB')
  })

  it('rejects unsupported file types', () => {
    const file = new File(['data'], 'doc.docx', {
      type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    })
    const result = validateUploadInput(file)
    expect(result.valid).toBe(false)
    expect(result.error).toContain('no permitido')
  })

  it('accepts valid PDF under size limit', () => {
    const file = new File(['%PDF-1.4'], 'report.pdf', { type: 'application/pdf' })
    const result = validateUploadInput(file)
    expect(result.valid).toBe(true)
  })

  it('accepts valid JPEG image', () => {
    const file = new File(['image-data'], 'xray.jpg', { type: 'image/jpeg' })
    const result = validateUploadInput(file)
    expect(result.valid).toBe(true)
  })
})
```

Extract validation into a pure function for testability:

```typescript
// src/lib/medical-documents/validate-upload.ts
import { ACCEPTED_MIME_TYPES, MAX_FILE_SIZE_BYTES, type AcceptedMimeType } from './constants'

export function validateUploadInput(file: File): { valid: boolean; error?: string } {
  if (!ACCEPTED_MIME_TYPES.includes(file.type as AcceptedMimeType)) {
    return { valid: false, error: 'Tipo de archivo no permitido. Tipos aceptados: PDF, JPEG, PNG, WEBP' }
  }
  if (file.size > MAX_FILE_SIZE_BYTES) {
    return {
      valid: false,
      error: `El archivo supera el límite de 10MB (${(file.size / 1024 / 1024).toFixed(1)}MB)`,
    }
  }
  return { valid: true }
}
```

## Related Issues

- EPIC-4
- S02
- S01/T01 (medical_records table that documents attach to)
- S02/T02 (notes interface that displays these documents)
