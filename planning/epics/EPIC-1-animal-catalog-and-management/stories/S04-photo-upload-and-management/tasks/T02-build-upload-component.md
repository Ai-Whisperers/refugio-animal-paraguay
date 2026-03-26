---
task: T02
story: S04
epic: EPIC-1
title: Build upload component
status: ready
priority: medium
agent_type: frontend
created: 2026-03-25T17:13:26.726846
---

# T02: Build upload component

## Description

Build the `AnimalPhotoUpload` Client Component for use in the staff admin panel. Allows drag-and-drop or click-to-select upload of animal photos directly to Supabase Storage. Shows upload progress, preview thumbnails, and allows setting the primary photo. Uses the Supabase browser client — upload happens client-side directly to Storage, no server roundtrip.

## Context

- Client Component (`'use client'`) — file picker, drag-and-drop, upload state
- Staff/admin only — this component only renders inside authenticated admin routes
- Uploads go to `animals-photos` Supabase Storage bucket (configured in S04/T01)
- Storage path: `{animalId}/{uuid}.{ext}` — one subfolder per animal
- After upload: calls `updateAnimalPhotos(animalId, urls)` Server Action to save URLs to DB
- CSS: Tailwind CSS 3.4.19 PINNED — use CSS vars, NOT hardcoded colors
- Max file size: 5MB per photo, accepted types: JPEG, PNG, WebP

## Files to create

### `src/components/admin/animals/AnimalPhotoUpload.tsx`

```typescript
'use client'

import { useState, useCallback } from 'react'
import Image from 'next/image'
import { createBrowserClient } from '@/lib/supabase/client'
import { updateAnimalPhotos } from '@/actions/animals'

interface UploadedPhoto {
  url: string
  isPrimary: boolean
}

interface AnimalPhotoUploadProps {
  animalId: string
  existingPhotos: string[]
  primaryPhotoUrl: string | null
}

const BUCKET = 'animals-photos'
const MAX_FILE_SIZE_MB = 5
const ACCEPTED_TYPES = ['image/jpeg', 'image/png', 'image/webp']

export function AnimalPhotoUpload({ animalId, existingPhotos, primaryPhotoUrl }: AnimalPhotoUploadProps) {
  const supabase = createBrowserClient()

  const [photos, setPhotos] = useState<UploadedPhoto[]>(
    existingPhotos.map((url) => ({ url, isPrimary: url === primaryPhotoUrl }))
  )
  const [uploading, setUploading] = useState(false)
  const [dragOver, setDragOver] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function uploadFile(file: File): Promise<string | null> {
    if (!ACCEPTED_TYPES.includes(file.type)) {
      setError(`Tipo de archivo no soportado: ${file.type}. Usá JPEG, PNG o WebP.`)
      return null
    }
    if (file.size > MAX_FILE_SIZE_MB * 1024 * 1024) {
      setError(`El archivo supera el límite de ${MAX_FILE_SIZE_MB}MB.`)
      return null
    }

    const ext = file.name.split('.').pop() ?? 'jpg'
    const path = `${animalId}/${crypto.randomUUID()}.${ext}`

    const { error: uploadError } = await supabase.storage
      .from(BUCKET)
      .upload(path, file, { upsert: false })

    if (uploadError) {
      setError(`Error subiendo foto: ${uploadError.message}`)
      return null
    }

    const { data } = supabase.storage.from(BUCKET).getPublicUrl(path)
    return data.publicUrl
  }

  async function handleFiles(files: FileList | File[]) {
    setError(null)
    setUploading(true)
    const newPhotos: UploadedPhoto[] = []

    for (const file of Array.from(files)) {
      const url = await uploadFile(file)
      if (url) {
        newPhotos.push({ url, isPrimary: false })
      }
    }

    const updated = [...photos, ...newPhotos]
    setPhotos(updated)

    // Persist to database
    const primaryUrl = updated.find((p) => p.isPrimary)?.url ?? updated[0]?.url ?? null
    const galleryUrls = updated.filter((p) => !p.isPrimary).map((p) => p.url)
    await updateAnimalPhotos(animalId, primaryUrl, galleryUrls)

    setUploading(false)
  }

  function setPrimary(url: string) {
    const updated = photos.map((p) => ({ ...p, isPrimary: p.url === url }))
    setPhotos(updated)
    const galleryUrls = updated.filter((p) => !p.isPrimary).map((p) => p.url)
    updateAnimalPhotos(animalId, url, galleryUrls)
  }

  async function removePhoto(url: string) {
    // Extract storage path from public URL
    const path = url.split(`${BUCKET}/`)[1]
    if (path) await supabase.storage.from(BUCKET).remove([path])

    const updated = photos.filter((p) => p.url !== url)
    // If we removed the primary, promote the first remaining photo
    if (!updated.some((p) => p.isPrimary) && updated.length > 0) {
      updated[0].isPrimary = true
    }
    setPhotos(updated)
    const primaryUrl = updated.find((p) => p.isPrimary)?.url ?? null
    const galleryUrls = updated.filter((p) => !p.isPrimary).map((p) => p.url)
    await updateAnimalPhotos(animalId, primaryUrl, galleryUrls)
  }

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)
    if (e.dataTransfer.files.length > 0) handleFiles(e.dataTransfer.files)
  }, [photos])

  return (
    <div className="space-y-4">
      {/* Drop zone */}
      <div
        onDrop={onDrop}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
        onDragLeave={() => setDragOver(false)}
        className={`
          border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors
          ${dragOver
            ? 'border-[var(--color-primary)] bg-[var(--bg-hover)]'
            : 'border-[var(--border-subtle)] hover:border-[var(--color-primary)]'
          }
        `}
        onClick={() => document.getElementById('photo-file-input')?.click()}
      >
        <input
          id="photo-file-input"
          type="file"
          accept={ACCEPTED_TYPES.join(',')}
          multiple
          className="hidden"
          onChange={(e) => e.target.files && handleFiles(e.target.files)}
        />
        <p className="text-[var(--text-secondary)]">
          {uploading ? 'Subiendo fotos…' : 'Arrastrá fotos aquí o hacé click para seleccionar'}
        </p>
        <p className="text-xs text-[var(--text-tertiary)] mt-1">
          JPEG, PNG, WebP · máx. {MAX_FILE_SIZE_MB}MB por foto
        </p>
      </div>

      {/* Error */}
      {error && (
        <p className="text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2">{error}</p>
      )}

      {/* Photo grid */}
      {photos.length > 0 && (
        <div className="grid grid-cols-3 gap-3">
          {photos.map((photo) => (
            <div key={photo.url} className="relative group rounded-lg overflow-hidden aspect-square bg-[var(--bg-skeleton)]">
              <Image
                src={photo.url}
                alt="Foto del animal"
                fill
                sizes="(max-width: 768px) 33vw, 200px"
                className="object-cover"
              />
              {/* Primary badge */}
              {photo.isPrimary && (
                <span className="absolute top-1 left-1 text-xs bg-[var(--color-primary)] text-white px-1.5 py-0.5 rounded-full">
                  Principal
                </span>
              )}
              {/* Hover actions */}
              <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
                {!photo.isPrimary && (
                  <button
                    onClick={() => setPrimary(photo.url)}
                    className="text-xs bg-white text-gray-900 px-2 py-1 rounded-md hover:bg-gray-100"
                  >
                    Principal
                  </button>
                )}
                <button
                  onClick={() => removePhoto(photo.url)}
                  className="text-xs bg-red-500 text-white px-2 py-1 rounded-md hover:bg-red-600"
                >
                  Eliminar
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
```

### `src/actions/animals.ts` (partial — add this action)

```typescript
'use server'

import { createServerClient } from '@/lib/supabase/server'
import { revalidatePath } from 'next/cache'

export async function updateAnimalPhotos(
  animalId: string,
  primaryPhotoUrl: string | null,
  galleryUrls: string[]
): Promise<void> {
  const supabase = createServerClient()

  const { error } = await supabase
    .from('animals')
    .update({
      photo_primary_url: primaryPhotoUrl,
      photo_gallery_urls: galleryUrls,
    })
    .eq('id', animalId)

  if (error) throw new Error(`Error actualizando fotos: ${error.message}`)

  revalidatePath(`/animales/${animalId}`)
  revalidatePath('/animales')
}
```

## Acceptance Criteria

- [ ] `AnimalPhotoUpload` is a `'use client'` component
- [ ] Files are uploaded directly to Supabase Storage bucket `animals-photos`
- [ ] Storage path uses `{animalId}/{uuid}.{ext}` format
- [ ] File validation: rejects files > 5MB or non-image MIME types with a visible error message
- [ ] Drag-and-drop works: visual highlight on drag-over, upload on drop
- [ ] "Set as primary" button visible on hover for non-primary photos
- [ ] "Remove" button deletes from Storage and updates DB
- [ ] Removing the current primary photo automatically promotes the next photo
- [ ] `updateAnimalPhotos` Server Action calls `revalidatePath` for both detail and catalog pages
- [ ] TypeScript: no type errors

## Implementation Notes

- Upload is client-side to Supabase Storage using `createBrowserClient()` — no API route needed
- `crypto.randomUUID()` generates unique filenames — available in modern browsers and Node 19+
- `getPublicUrl()` is synchronous (no async) — it constructs the URL without a network call
- `updateAnimalPhotos` is a Server Action marked `'use server'` — can be called directly from Client Components in Next.js 14
- The path extraction in `removePhoto` (`url.split(`${BUCKET}/`)[1]`) assumes Supabase public URL format — verify against actual URL structure in your Supabase project

## Related

- Depends on: S04/T01 (Storage bucket must be configured with public access policy)
- Used by: Admin animal edit form (EPIC-3 staff portal)
- Part of: S04 — Photo Upload and Management
