---
task: T01
story: S01
epic: EPIC-4
title: Design medical record schema
status: ready
priority: medium
created: 2026-03-25T17:13:26.730102
---

# T01: Design medical record schema

## Description

Design the PostgreSQL schema for all medical/health data in Supabase: `medical_records`, `vaccinations`, `medications`, `treatments`, `veterinarians`, and their relationships to the existing `animals` table. The schema must support the full animal health lifecycle — from intake exam through ongoing care to adoption handover records.

## Acceptance Criteria

- [ ] `medical_records` table created (general health events — exams, diagnoses, notes)
- [ ] `vaccinations` table created with due-date tracking
- [ ] `medications` table created with dosage, frequency, and active/completed status
- [ ] `treatments` table created (surgeries, procedures, therapies)
- [ ] `veterinarians` table created (internal staff + external vets)
- [ ] All tables have `animal_id` FK referencing `animals.id`
- [ ] RLS policies restrict donor/adopter access; staff/admin/vet roles can read all; only staff/admin can write
- [ ] TypeScript types generated from schema
- [ ] Schema reviewed against Paraguayan veterinary record norms

## Implementation Notes

### Table: `veterinarians`

```sql
create table veterinarians (
  id          uuid primary key default gen_random_uuid(),
  full_name   text not null,
  license_number text,                          -- SENACSA license number (Paraguay)
  clinic_name text,
  phone       text,
  email       text,
  is_internal boolean not null default false,   -- true = shelter staff vet
  is_active   boolean not null default true,
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);
```

### Table: `medical_records`

General health events — intake exams, checkups, diagnoses, vet notes.

```sql
create table medical_records (
  id              uuid primary key default gen_random_uuid(),
  animal_id       uuid not null references animals(id) on delete cascade,
  veterinarian_id uuid references veterinarians(id) on delete set null,
  record_type     text not null check (record_type in (
                    'intake_exam', 'checkup', 'diagnosis',
                    'follow_up', 'discharge', 'other'
                  )),
  visit_date      date not null,
  weight_kg       numeric(5, 2),                -- null if not weighed
  temperature_c   numeric(4, 1),                -- null if not measured
  diagnosis       text,                         -- free text diagnosis or findings
  notes           text,
  is_confidential boolean not null default false,  -- hides from adopter view if true
  created_by      uuid not null references auth.users(id),
  created_at      timestamptz not null default now(),
  updated_at      timestamptz not null default now()
);

create index medical_records_animal_id_idx on medical_records(animal_id);
create index medical_records_visit_date_idx on medical_records(visit_date desc);
```

### Table: `vaccinations`

```sql
create table vaccinations (
  id              uuid primary key default gen_random_uuid(),
  animal_id       uuid not null references animals(id) on delete cascade,
  veterinarian_id uuid references veterinarians(id) on delete set null,
  vaccine_name    text not null,                -- e.g. "Rabia", "Parvovirus", "Moquillo"
  batch_number    text,
  administered_at date not null,
  next_due_at     date,                         -- null = single-dose or series complete
  notes           text,
  created_by      uuid not null references auth.users(id),
  created_at      timestamptz not null default now(),
  updated_at      timestamptz not null default now()
);

create index vaccinations_animal_id_idx on vaccinations(animal_id);
create index vaccinations_next_due_at_idx on vaccinations(next_due_at)
  where next_due_at is not null;               -- partial index for reminder queries
```

### Table: `medications`

```sql
create table medications (
  id              uuid primary key default gen_random_uuid(),
  animal_id       uuid not null references animals(id) on delete cascade,
  medical_record_id uuid references medical_records(id) on delete set null,
  veterinarian_id uuid references veterinarians(id) on delete set null,
  medication_name text not null,
  dosage          text not null,                -- e.g. "5mg/kg"
  frequency       text not null,               -- e.g. "twice daily", "every 8 hours"
  route           text not null check (route in (
                    'oral', 'injectable', 'topical', 'inhalation', 'other'
                  )),
  start_date      date not null,
  end_date        date,                         -- null = ongoing
  is_active       boolean not null default true,
  notes           text,
  created_by      uuid not null references auth.users(id),
  created_at      timestamptz not null default now(),
  updated_at      timestamptz not null default now()
);

create index medications_animal_id_idx on medications(animal_id);
create index medications_is_active_idx on medications(animal_id) where is_active = true;
```

### Table: `treatments`

Procedures requiring more detail than a general record — surgeries, sterilizations, dental cleanings, therapies.

```sql
create table treatments (
  id              uuid primary key default gen_random_uuid(),
  animal_id       uuid not null references animals(id) on delete cascade,
  medical_record_id uuid references medical_records(id) on delete set null,
  veterinarian_id uuid references veterinarians(id) on delete set null,
  treatment_type  text not null check (treatment_type in (
                    'surgery', 'sterilization', 'dental', 'wound_care',
                    'physical_therapy', 'deworming', 'parasite_treatment', 'other'
                  )),
  treatment_date  date not null,
  outcome         text check (outcome in ('successful', 'ongoing', 'failed', 'pending')),
  duration_minutes int,
  anesthesia_used boolean not null default false,
  notes           text,
  created_by      uuid not null references auth.users(id),
  created_at      timestamptz not null default now(),
  updated_at      timestamptz not null default now()
);

create index treatments_animal_id_idx on treatments(animal_id);
create index treatments_treatment_date_idx on treatments(treatment_date desc);
```

### RLS Policies

All four medical tables use the same pattern. Example for `medical_records`:

```sql
-- Staff and admin can read all records
create policy "staff_admin_read_medical_records"
  on medical_records for select
  using (
    exists (
      select 1 from profiles
      where profiles.id = auth.uid()
        and profiles.role in ('staff', 'admin', 'vet')
    )
  );

-- Adopters can read non-confidential records for animals they are adopting
-- (join against adoption_requests for their animal_id)
create policy "adopter_read_non_confidential_medical_records"
  on medical_records for select
  using (
    is_confidential = false
    and exists (
      select 1 from adoption_requests ar
      join profiles p on p.id = auth.uid()
      where ar.animal_id = medical_records.animal_id
        and ar.adopter_user_id = auth.uid()
        and ar.status in ('approved', 'completed')
        and p.role = 'adopter'
    )
  );

-- Only staff/admin can write
create policy "staff_admin_write_medical_records"
  on medical_records for insert
  with check (
    exists (
      select 1 from profiles
      where profiles.id = auth.uid()
        and profiles.role in ('staff', 'admin', 'vet')
    )
  );

create policy "staff_admin_update_medical_records"
  on medical_records for update
  using (
    exists (
      select 1 from profiles
      where profiles.id = auth.uid()
        and profiles.role in ('staff', 'admin', 'vet')
    )
  );
```

Apply equivalent policies to `vaccinations`, `medications`, `treatments`.
`veterinarians` table is read-only for all authenticated users; write requires staff/admin.

### TypeScript Types

Generate via Supabase CLI after migrations run:

```bash
npx supabase gen types typescript --local > src/types/supabase.ts
```

Then define domain types in `src/types/medical.ts`:

```typescript
export type MedicalRecordType =
  | 'intake_exam'
  | 'checkup'
  | 'diagnosis'
  | 'follow_up'
  | 'discharge'
  | 'other'

export type MedicationRoute = 'oral' | 'injectable' | 'topical' | 'inhalation' | 'other'

export type TreatmentType =
  | 'surgery'
  | 'sterilization'
  | 'dental'
  | 'wound_care'
  | 'physical_therapy'
  | 'deworming'
  | 'parasite_treatment'
  | 'other'

export type TreatmentOutcome = 'successful' | 'ongoing' | 'failed' | 'pending'

// Derived from Supabase-generated types — add display helpers here
export interface MedicalRecordWithVet {
  id: string
  animal_id: string
  veterinarian: Pick<Veterinarian, 'id' | 'full_name' | 'clinic_name'> | null
  record_type: MedicalRecordType
  visit_date: string        // ISO date string (YYYY-MM-DD)
  weight_kg: number | null
  temperature_c: number | null
  diagnosis: string | null
  notes: string | null
  is_confidential: boolean
  created_at: string
}
```

### Design Decisions

- `is_confidential` on `medical_records` hides sensitive diagnoses (e.g. FIV status) from adopter view while still visible to staff — intentional, not a bug in RLS.
- `veterinarian_id` is nullable with `on delete set null` — records must not be deleted if a vet leaves. Historical records remain intact.
- `medical_record_id` on `medications` and `treatments` is optional — allows recording ongoing medications not tied to a specific visit.
- Paraguayan vaccine naming: Vaccines are stored as free text (`vaccine_name`) rather than an enum because SENACSA-approved vaccine brands change and the shelter may use generic names.
- No decimal currency in this table — medical costs are tracked separately in a future billing epic, not in medical records.

## Related Issues

- EPIC-4
- S01
- T02 (migrations implement this schema)
- T03 (audit logging wraps these tables)
