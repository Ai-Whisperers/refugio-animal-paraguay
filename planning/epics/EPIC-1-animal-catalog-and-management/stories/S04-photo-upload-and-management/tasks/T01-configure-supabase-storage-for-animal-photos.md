---
task: T01
story: S04
epic: EPIC-1
title: Configure Supabase Storage for animal photos
status: ready
priority: high
agent_type: devops
created: 2026-03-25T17:13:26.726769
claimed_by: null
claimed_at: null
branch: null
pr_url: null
---

# T01: Configure Supabase Storage for animal photos

## Description

Set up Supabase Storage buckets for animal photo management. This replaces any Cloudinary integration — all media storage goes through Supabase Storage. Configure buckets, access policies, and the service layer that the upload component (T02) will use.

## Context

- Architecture reference: `docs/ARCHITECTURE.md` — Storage Buckets section
- Do NOT use Cloudinary, S3, or any third-party CDN — Supabase Storage only
- Public bucket for serving animal photos to unauthenticated visitors (adoption catalog)
- Supabase Storage uses the same RLS policy system as the database

## Bucket structure to implement

```
animals-photos/           ← Public bucket (adoption catalog photos)
  {animal_id}/
    primary.webp          ← Main photo (required)
    gallery/
      {uuid}.webp         ← Additional photos
      {uuid}.webp

adoption-documents/       ← Private bucket (adoption paperwork)
  {adoption_id}/
    application.pdf
    id_copy.pdf

medical-documents/        ← Private bucket (vet records)
  {animal_id}/
    {date}-{type}.pdf
```

## SQL migration to create buckets and policies

Create `supabase/migrations/YYYYMMDDHHMMSS_create_storage_buckets.sql`:

```sql
-- Create storage buckets
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values
  ('animals-photos', 'animals-photos', true, 5242880,  -- 5MB limit
   array['image/jpeg', 'image/png', 'image/webp']),

  ('adoption-documents', 'adoption-documents', false, 10485760,  -- 10MB limit
   array['application/pdf', 'image/jpeg', 'image/png']),

  ('medical-documents', 'medical-documents', false, 10485760,  -- 10MB limit
   array['application/pdf', 'image/jpeg', 'image/png'])
on conflict (id) do nothing;

-- animals-photos: public read (anyone can view adoption catalog photos)
create policy "Public read for animal photos"
  on storage.objects for select
  using (bucket_id = 'animals-photos');

-- animals-photos: staff can upload/update
create policy "Staff can upload animal photos"
  on storage.objects for insert
  with check (
    bucket_id = 'animals-photos'
    and auth.jwt() ->> 'role' in ('staff', 'admin')
  );

create policy "Staff can update animal photos"
  on storage.objects for update
  using (
    bucket_id = 'animals-photos'
    and auth.jwt() ->> 'role' in ('staff', 'admin')
  );

create policy "Staff can delete animal photos"
  on storage.objects for delete
  using (
    bucket_id = 'animals-photos'
    and auth.jwt() ->> 'role' in ('staff', 'admin')
  );

-- adoption-documents: staff read all, adopter reads own
create policy "Staff can access adoption documents"
  on storage.objects for select
  using (
    bucket_id = 'adoption-documents'
    and auth.jwt() ->> 'role' in ('staff', 'admin')
  );

create policy "Staff can upload adoption documents"
  on storage.objects for insert
  with check (
    bucket_id = 'adoption-documents'
    and auth.jwt() ->> 'role' in ('staff', 'admin')
  );

-- medical-documents: staff only
create policy "Staff can access medical documents"
  on storage.objects for select
  using (
    bucket_id = 'medical-documents'
    and auth.jwt() ->> 'role' in ('staff', 'admin', 'vet')
  );

create policy "Staff can upload medical documents"
  on storage.objects for insert
  with check (
    bucket_id = 'medical-documents'
    and auth.jwt() ->> 'role' in ('staff', 'admin', 'vet')
  );
```

## StorageService implementation

Create `src/services/storage-service.ts`:

```typescript
import { createServerClient } from '@/lib/supabase/server'
import { BaseService, ServiceResult } from './base-service'

const ANIMAL_PHOTOS_BUCKET = 'animals-photos'
const MAX_PHOTO_SIZE_MB = 5
const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/webp']

export interface UploadPhotoResult {
  path: string
  publicUrl: string
}

export class StorageService extends BaseService {
  async uploadAnimalPhoto(
    animalId: string,
    file: File,
    slot: 'primary' | 'gallery'
  ): Promise<ServiceResult<UploadPhotoResult>> {
    return this.handleError(async () => {
      // Validate file type and size
      if (!ALLOWED_TYPES.includes(file.type)) {
        throw new Error(`File type not allowed. Use: ${ALLOWED_TYPES.join(', ')}`)
      }
      if (file.size > MAX_PHOTO_SIZE_MB * 1024 * 1024) {
        throw new Error(`File exceeds ${MAX_PHOTO_SIZE_MB}MB limit`)
      }

      const ext = file.name.split('.').pop() ?? 'jpg'
      const path =
        slot === 'primary'
          ? `${animalId}/primary.${ext}`
          : `${animalId}/gallery/${crypto.randomUUID()}.${ext}`

      const { data, error } = await this.supabase.storage
        .from(ANIMAL_PHOTOS_BUCKET)
        .upload(path, file, { upsert: slot === 'primary' })

      if (error) throw error

      const { data: urlData } = this.supabase.storage
        .from(ANIMAL_PHOTOS_BUCKET)
        .getPublicUrl(data.path)

      return { path: data.path, publicUrl: urlData.publicUrl }
    }, 'Failed to upload animal photo')
  }

  async deleteAnimalPhoto(path: string): Promise<ServiceResult<void>> {
    return this.handleError(async () => {
      const { error } = await this.supabase.storage
        .from(ANIMAL_PHOTOS_BUCKET)
        .remove([path])
      if (error) throw error
    }, 'Failed to delete animal photo')
  }

  getPublicUrl(path: string): string {
    const { data } = this.supabase.storage
      .from(ANIMAL_PHOTOS_BUCKET)
      .getPublicUrl(path)
    return data.publicUrl
  }
}
```

## Acceptance Criteria

- [ ] Migration file creates all 3 buckets with correct `public`, size limit, and mime type settings
- [ ] RLS policies applied: `animals-photos` public read, staff write; `adoption-documents` staff only; `medical-documents` staff+vet only
- [ ] `src/services/storage-service.ts` created extending `BaseService`
- [ ] `StorageService.uploadAnimalPhoto()` validates file type and size before upload
- [ ] `StorageService.uploadAnimalPhoto()` returns `ServiceResult<UploadPhotoResult>` (never throws)
- [ ] `StorageService.deleteAnimalPhoto()` implemented
- [ ] `StorageService.getPublicUrl()` implemented as a synchronous helper
- [ ] Migration applies cleanly via `supabase db push`
- [ ] Storage bucket visible in local Supabase Studio at http://localhost:54323

## Implementation Notes

- Do NOT install or use the Cloudinary SDK, Cloudinary Node.js package, or any `cloudinary.*` references
- Public URLs for `animals-photos` are permanent and can be cached by the browser/CDN — no signed URLs needed for animal photos
- `adoption-documents` and `medical-documents` require signed URLs (temporary, expire) — implement in a follow-up task if needed
- WebP is the preferred output format for photos — the upload component (T02) will handle conversion client-side before sending
- The `primary.{ext}` path uses `upsert: true` so replacing the primary photo doesn't leave orphan files

## Related

- EPIC-1 / S04 — Photo upload and management
- Depends on: T01 in S01 (animals table must exist for animal_id references)
- Blocks: T02 (upload component needs the StorageService to be ready)
- Architecture: `docs/ARCHITECTURE.md` — Storage Buckets section
