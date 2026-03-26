---
task: T01
story: S01
epic: EPIC-2
title: Design adoption application form schema
status: ready
priority: high
agent_type: fullstack
created: 2026-03-25T10:00:00Z
---

# T01: Design adoption application form schema

## Description

Define the `adoption_applications` table via a Supabase SQL migration and export the corresponding TypeScript types. The table stores submitted form data as JSONB alongside structured status columns. The TypeScript `AdoptionApplication` type (derived from the Zod schema in T03) is the source of truth for the `data` column shape.

## Context

- Supabase-only backend — NO Prisma, NO ORM
- Next.js 14 App Router with Server Components and Server Actions
- Storage bucket `adoption-documents` holds uploaded identity documents
- `adoption_applications.data` column is JSONB — typed via the Zod schema in T03
- CSS: Tailwind CSS 3.4.19 PINNED — no new UI in this task

## Files to create

### `supabase/migrations/20260325_adoption_applications.sql`

```sql
-- Create enum for application status
CREATE TYPE adoption_application_status AS ENUM (
  'draft',
  'submitted',
  'under_review',
  'approved',
  'rejected',
  'withdrawn'
);

-- Adoption applications table
CREATE TABLE adoption_applications (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  adopter_id        uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  animal_id         uuid REFERENCES animals(id) ON DELETE SET NULL,
  status            adoption_application_status NOT NULL DEFAULT 'draft',
  data              jsonb NOT NULL DEFAULT '{}',
  submitted_at      timestamptz,
  reviewed_at       timestamptz,
  reviewer_id       uuid REFERENCES auth.users(id) ON DELETE SET NULL,
  reviewer_notes    text,
  created_at        timestamptz NOT NULL DEFAULT now(),
  updated_at        timestamptz NOT NULL DEFAULT now()
);

-- Updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER adoption_applications_updated_at
  BEFORE UPDATE ON adoption_applications
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Indexes
CREATE INDEX idx_adoption_applications_adopter_id ON adoption_applications(adopter_id);
CREATE INDEX idx_adoption_applications_animal_id ON adoption_applications(animal_id);
CREATE INDEX idx_adoption_applications_status ON adoption_applications(status);
CREATE INDEX idx_adoption_applications_submitted_at ON adoption_applications(submitted_at DESC)
  WHERE submitted_at IS NOT NULL;

-- Row Level Security
ALTER TABLE adoption_applications ENABLE ROW LEVEL SECURITY;

-- Adopters can only read/write their own applications
CREATE POLICY "adopters_own_applications"
  ON adoption_applications
  FOR ALL
  TO authenticated
  USING (adopter_id = auth.uid())
  WITH CHECK (adopter_id = auth.uid());

-- Staff can read all applications
CREATE POLICY "staff_read_all_applications"
  ON adoption_applications
  FOR SELECT
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM profiles
      WHERE profiles.id = auth.uid()
      AND profiles.role IN ('staff', 'admin')
    )
  );

-- Staff can update status and reviewer fields
CREATE POLICY "staff_update_applications"
  ON adoption_applications
  FOR UPDATE
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM profiles
      WHERE profiles.id = auth.uid()
      AND profiles.role IN ('staff', 'admin')
    )
  )
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM profiles
      WHERE profiles.id = auth.uid()
      AND profiles.role IN ('staff', 'admin')
    )
  );
```

### `supabase/migrations/20260325_adoption_documents_bucket.sql`

```sql
-- Create storage bucket for adoption documents (identity docs, home photos)
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
  'adoption-documents',
  'adoption-documents',
  false,
  5242880,  -- 5 MB per file
  ARRAY['image/jpeg', 'image/png', 'image/webp', 'application/pdf']
);

-- Authenticated users can upload to their own folder
CREATE POLICY "users_upload_own_documents"
  ON storage.objects
  FOR INSERT
  TO authenticated
  WITH CHECK (
    bucket_id = 'adoption-documents'
    AND (storage.foldername(name))[1] = auth.uid()::text
  );

-- Users can read their own documents
CREATE POLICY "users_read_own_documents"
  ON storage.objects
  FOR SELECT
  TO authenticated
  USING (
    bucket_id = 'adoption-documents'
    AND (storage.foldername(name))[1] = auth.uid()::text
  );

-- Staff can read all documents
CREATE POLICY "staff_read_all_documents"
  ON storage.objects
  FOR SELECT
  TO authenticated
  USING (
    bucket_id = 'adoption-documents'
    AND EXISTS (
      SELECT 1 FROM profiles
      WHERE profiles.id = auth.uid()
      AND profiles.role IN ('staff', 'admin')
    )
  );
```

### `src/types/adoption.ts` (new file — shared types)

```typescript
export type AdoptionApplicationStatus =
  | 'draft'
  | 'submitted'
  | 'under_review'
  | 'approved'
  | 'rejected'
  | 'withdrawn'

export interface AdoptionApplicationRow {
  id: string
  adopter_id: string
  animal_id: string | null
  status: AdoptionApplicationStatus
  data: AdoptionApplicationData
  submitted_at: string | null
  reviewed_at: string | null
  reviewer_id: string | null
  reviewer_notes: string | null
  created_at: string
  updated_at: string
}

// Shape of the JSONB `data` column — mirrors the Zod schema in src/lib/validation/adoption-schema.ts
export interface AdoptionApplicationData {
  adopter: {
    fullName: string
    email: string
    phone: string
    identityType: 'cedula' | 'pasaporte' | 'otro'
    identityNumber: string
  }
  address: {
    street: string
    city: string
    department: string
    postalCode?: string
    country: 'PY'
  }
  household: {
    residentsCount: number
    childrenAges?: number[]
    otherPets?: Array<{ type: string; name: string; age: number }>
    livingType: 'casa' | 'apartamento' | 'chacra'
  }
  animalPreferences: {
    species: 'perro' | 'gato' | 'otro'
    sizePreference?: 'pequeño' | 'mediano' | 'grande'
    agePreference?: 'cachorro' | 'adulto' | 'senior'
    specialNeeds: boolean
  }
  experience: {
    hasOwnedPets: boolean
    experienceYears: number
    veterinaryPlans: string
    timeCommitment: number
    trainingExperience: string
  }
  agreements: {
    termsAccepted: boolean
    privacyAccepted: boolean
    homeVisitConsent: boolean
    followUpContact: boolean
  }
}
```

## Acceptance Criteria

- [ ] Migration creates `adoption_applications` table with all columns
- [ ] `adoption_application_status` enum defined with 6 values
- [ ] `updated_at` trigger fires on every UPDATE
- [ ] Indexes on `adopter_id`, `animal_id`, `status`, `submitted_at`
- [ ] RLS enabled — adopters can only access their own rows
- [ ] Staff/admin can read all applications and update status fields
- [ ] Storage bucket `adoption-documents` created, non-public, 5 MB limit
- [ ] Storage policies: users upload/read their own folder, staff read all
- [ ] `AdoptionApplicationData.experience.veterinaryPlans` spelled correctly (no typo)
- [ ] TypeScript: no type errors in `src/types/adoption.ts`

## Implementation Notes

- `data jsonb NOT NULL DEFAULT '{}'` — allows draft saves before all fields are filled
- `animal_id` is nullable: adopters can apply without specifying a particular animal (general interest)
- Storage path convention: `{adopter_id}/{application_id}/{filename}` — enforced by the upload policy folder check
- `profiles.role` column is assumed to exist from EPIC-0 auth setup; adjust the policy if the column name differs
- The `veterinaryPlans` field corrects the typo `veterinayPlans` that appeared in the original placeholder

## Related

- Used by: S01/T02 (form components), S01/T03 (Server Action), S02 (review dashboard)
- Part of: S01 — Adoption Application Form
