---
task: T02
story: S01
epic: EPIC-4
title: Create database migrations
status: ready
priority: medium
created: 2026-03-25T17:13:26.730162
---

# T02: Create database migrations

## Description

Write and apply Supabase migrations for all medical record tables defined in T01. Each table gets its own timestamped migration file. Migrations must be idempotent, apply cleanly from a fresh database, and include rollback SQL in comments.

## Acceptance Criteria

- [ ] Migration files created in `supabase/migrations/` with correct timestamps
- [ ] `veterinarians` table migration runs first (referenced by FK in other tables)
- [ ] `medical_records`, `vaccinations`, `medications`, `treatments` migrations created
- [ ] All indexes from T01 schema included
- [ ] RLS enabled on all four medical tables
- [ ] `updated_at` trigger applied to all five tables (veterinarians + 4 medical)
- [ ] Migrations apply cleanly with `supabase db reset`
- [ ] Rollback SQL documented in each migration file

## Implementation Notes

### Migration Order

Migrations must be ordered so FK dependencies are satisfied:

```
20260401000001_create_veterinarians.sql
20260401000002_create_medical_records.sql
20260401000003_create_vaccinations.sql
20260401000004_create_medications.sql
20260401000005_create_treatments.sql
20260401000006_medical_records_rls_policies.sql
```

### `updated_at` Trigger Function

Create once, reuse for all tables. Add to the earliest migration or a shared utility migration:

```sql
-- supabase/migrations/20260401000001_create_veterinarians.sql

-- Shared trigger function for updated_at (idempotent)
create or replace function set_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;
```

Then attach in each table migration:

```sql
create trigger set_veterinarians_updated_at
  before update on veterinarians
  for each row execute function set_updated_at();
```

### Full Migration: `20260401000001_create_veterinarians.sql`

```sql
-- Create veterinarians table
-- Rollback: drop table if exists veterinarians cascade;

create table veterinarians (
  id             uuid primary key default gen_random_uuid(),
  full_name      text not null,
  license_number text,
  clinic_name    text,
  phone          text,
  email          text,
  is_internal    boolean not null default false,
  is_active      boolean not null default true,
  created_at     timestamptz not null default now(),
  updated_at     timestamptz not null default now()
);

create or replace function set_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

create trigger set_veterinarians_updated_at
  before update on veterinarians
  for each row execute function set_updated_at();

alter table veterinarians enable row level security;

-- All authenticated users can read veterinarians
create policy "authenticated_read_veterinarians"
  on veterinarians for select
  to authenticated
  using (true);

-- Only staff/admin can write
create policy "staff_admin_insert_veterinarians"
  on veterinarians for insert
  with check (
    exists (
      select 1 from profiles
      where profiles.id = auth.uid()
        and profiles.role in ('staff', 'admin')
    )
  );

create policy "staff_admin_update_veterinarians"
  on veterinarians for update
  using (
    exists (
      select 1 from profiles
      where profiles.id = auth.uid()
        and profiles.role in ('staff', 'admin')
    )
  );
```

### Full Migration: `20260401000002_create_medical_records.sql`

```sql
-- Create medical_records table
-- Rollback: drop table if exists medical_records cascade;

create table medical_records (
  id              uuid primary key default gen_random_uuid(),
  animal_id       uuid not null references animals(id) on delete cascade,
  veterinarian_id uuid references veterinarians(id) on delete set null,
  record_type     text not null check (record_type in (
                    'intake_exam', 'checkup', 'diagnosis',
                    'follow_up', 'discharge', 'other'
                  )),
  visit_date      date not null,
  weight_kg       numeric(5, 2),
  temperature_c   numeric(4, 1),
  diagnosis       text,
  notes           text,
  is_confidential boolean not null default false,
  created_by      uuid not null references auth.users(id),
  created_at      timestamptz not null default now(),
  updated_at      timestamptz not null default now()
);

create index medical_records_animal_id_idx on medical_records(animal_id);
create index medical_records_visit_date_idx on medical_records(visit_date desc);

create trigger set_medical_records_updated_at
  before update on medical_records
  for each row execute function set_updated_at();

alter table medical_records enable row level security;
```

### Full Migration: `20260401000003_create_vaccinations.sql`

```sql
-- Rollback: drop table if exists vaccinations cascade;

create table vaccinations (
  id              uuid primary key default gen_random_uuid(),
  animal_id       uuid not null references animals(id) on delete cascade,
  veterinarian_id uuid references veterinarians(id) on delete set null,
  vaccine_name    text not null,
  batch_number    text,
  administered_at date not null,
  next_due_at     date,
  notes           text,
  created_by      uuid not null references auth.users(id),
  created_at      timestamptz not null default now(),
  updated_at      timestamptz not null default now()
);

create index vaccinations_animal_id_idx on vaccinations(animal_id);
create index vaccinations_next_due_at_idx on vaccinations(next_due_at)
  where next_due_at is not null;

create trigger set_vaccinations_updated_at
  before update on vaccinations
  for each row execute function set_updated_at();

alter table vaccinations enable row level security;
```

### Full Migration: `20260401000004_create_medications.sql`

```sql
-- Rollback: drop table if exists medications cascade;

create table medications (
  id                uuid primary key default gen_random_uuid(),
  animal_id         uuid not null references animals(id) on delete cascade,
  medical_record_id uuid references medical_records(id) on delete set null,
  veterinarian_id   uuid references veterinarians(id) on delete set null,
  medication_name   text not null,
  dosage            text not null,
  frequency         text not null,
  route             text not null check (route in (
                      'oral', 'injectable', 'topical', 'inhalation', 'other'
                    )),
  start_date        date not null,
  end_date          date,
  is_active         boolean not null default true,
  notes             text,
  created_by        uuid not null references auth.users(id),
  created_at        timestamptz not null default now(),
  updated_at        timestamptz not null default now()
);

create index medications_animal_id_idx on medications(animal_id);
create index medications_is_active_idx on medications(animal_id) where is_active = true;

create trigger set_medications_updated_at
  before update on medications
  for each row execute function set_updated_at();

alter table medications enable row level security;
```

### Full Migration: `20260401000005_create_treatments.sql`

```sql
-- Rollback: drop table if exists treatments cascade;

create table treatments (
  id                uuid primary key default gen_random_uuid(),
  animal_id         uuid not null references animals(id) on delete cascade,
  medical_record_id uuid references medical_records(id) on delete set null,
  veterinarian_id   uuid references veterinarians(id) on delete set null,
  treatment_type    text not null check (treatment_type in (
                      'surgery', 'sterilization', 'dental', 'wound_care',
                      'physical_therapy', 'deworming', 'parasite_treatment', 'other'
                    )),
  treatment_date    date not null,
  outcome           text check (outcome in ('successful', 'ongoing', 'failed', 'pending')),
  duration_minutes  int,
  anesthesia_used   boolean not null default false,
  notes             text,
  created_by        uuid not null references auth.users(id),
  created_at        timestamptz not null default now(),
  updated_at        timestamptz not null default now()
);

create index treatments_animal_id_idx on treatments(animal_id);
create index treatments_treatment_date_idx on treatments(treatment_date desc);

create trigger set_treatments_updated_at
  before update on treatments
  for each row execute function set_updated_at();

alter table treatments enable row level security;
```

### Full Migration: `20260401000006_medical_records_rls_policies.sql`

Apply RLS policies to all four medical tables. Split into its own migration to keep table-creation migrations clean.

```sql
-- medical_records RLS
create policy "staff_admin_vet_read_medical_records"
  on medical_records for select
  using (
    exists (
      select 1 from profiles
      where profiles.id = auth.uid()
        and profiles.role in ('staff', 'admin', 'vet')
    )
  );

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

create policy "staff_admin_vet_insert_medical_records"
  on medical_records for insert
  with check (
    exists (
      select 1 from profiles
      where profiles.id = auth.uid()
        and profiles.role in ('staff', 'admin', 'vet')
    )
  );

create policy "staff_admin_vet_update_medical_records"
  on medical_records for update
  using (
    exists (
      select 1 from profiles
      where profiles.id = auth.uid()
        and profiles.role in ('staff', 'admin', 'vet')
    )
  );

-- Repeat equivalent policies for vaccinations, medications, treatments
-- (same pattern: staff/admin/vet read+write; adopter read non-confidential where applicable)

-- vaccinations: adopters with approved/completed adoption can read all vaccination records
-- (vaccinations have no is_confidential flag — all vaccination records visible to adopters)
create policy "staff_admin_vet_read_vaccinations"
  on vaccinations for select
  using (
    exists (
      select 1 from profiles
      where profiles.id = auth.uid()
        and profiles.role in ('staff', 'admin', 'vet')
    )
  );

create policy "adopter_read_vaccinations"
  on vaccinations for select
  using (
    exists (
      select 1 from adoption_requests ar
      join profiles p on p.id = auth.uid()
      where ar.animal_id = vaccinations.animal_id
        and ar.adopter_user_id = auth.uid()
        and ar.status in ('approved', 'completed')
        and p.role = 'adopter'
    )
  );

create policy "staff_admin_vet_insert_vaccinations"
  on vaccinations for insert
  with check (
    exists (
      select 1 from profiles
      where profiles.id = auth.uid()
        and profiles.role in ('staff', 'admin', 'vet')
    )
  );

create policy "staff_admin_vet_update_vaccinations"
  on vaccinations for update
  using (
    exists (
      select 1 from profiles
      where profiles.id = auth.uid()
        and profiles.role in ('staff', 'admin', 'vet')
    )
  );

-- medications and treatments: staff/admin/vet only (no adopter access — clinical detail)
create policy "staff_admin_vet_read_medications"
  on medications for select
  using (
    exists (
      select 1 from profiles
      where profiles.id = auth.uid()
        and profiles.role in ('staff', 'admin', 'vet')
    )
  );

create policy "staff_admin_vet_insert_medications"
  on medications for insert
  with check (
    exists (
      select 1 from profiles
      where profiles.id = auth.uid()
        and profiles.role in ('staff', 'admin', 'vet')
    )
  );

create policy "staff_admin_vet_update_medications"
  on medications for update
  using (
    exists (
      select 1 from profiles
      where profiles.id = auth.uid()
        and profiles.role in ('staff', 'admin', 'vet')
    )
  );

create policy "staff_admin_vet_read_treatments"
  on treatments for select
  using (
    exists (
      select 1 from profiles
      where profiles.id = auth.uid()
        and profiles.role in ('staff', 'admin', 'vet')
    )
  );

create policy "staff_admin_vet_insert_treatments"
  on treatments for insert
  with check (
    exists (
      select 1 from profiles
      where profiles.id = auth.uid()
        and profiles.role in ('staff', 'admin', 'vet')
    )
  );

create policy "staff_admin_vet_update_treatments"
  on treatments for update
  using (
    exists (
      select 1 from profiles
      where profiles.id = auth.uid()
        and profiles.role in ('staff', 'admin', 'vet')
    )
  );
```

### Applying Migrations

```bash
# Apply to local Supabase
npx supabase db reset

# Verify tables exist
npx supabase db diff

# Regenerate TypeScript types after migration
npx supabase gen types typescript --local > src/types/supabase.ts
```

### Verifying RLS

```sql
-- Test as a staff user (run in Supabase Studio SQL editor with a staff user's JWT)
set local role authenticated;
set local request.jwt.claims '{"sub": "<staff-user-uuid>"}';
select count(*) from medical_records;  -- should return row count

-- Test as an unauthenticated user
set local role anon;
select count(*) from medical_records;  -- should return 0 rows (RLS blocks)
```

## Related Issues

- EPIC-4
- S01
- T01 (schema design this migration implements)
- T03 (audit logging added after these tables exist)
