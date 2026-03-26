---
task: T01
story: S01
epic: EPIC-1
title: Define Supabase schema for animals table
status: ready
priority: high
agent_type: code
created: 2026-03-25T17:13:26.725560
claimed_by: null
claimed_at: null
branch: null
pr_url: null
---

# T01: Define Supabase schema for animals table

## Description

Write the SQL migration that creates the `animals` table in Supabase with all required columns, constraints, indexes, and Row Level Security policies. This is the foundational schema that every other EPIC-1 story depends on.

## Context

- Architecture reference: `docs/ARCHITECTURE.md` — Supabase Schema section
- Migration location: `supabase/migrations/`
- Supabase project: configured via `NEXT_PUBLIC_SUPABASE_URL` + `SUPABASE_SERVICE_ROLE_KEY` in `.env.local`
- Run migrations with: `supabase db push` (local) or via Supabase dashboard (remote)

## Schema to implement

```sql
-- Enable UUID extension (if not already enabled)
create extension if not exists "uuid-ossp";

create table public.animals (
  id              uuid primary key default uuid_generate_v4(),
  name            text not null,
  species         text not null check (species in ('dog', 'cat', 'rabbit', 'bird', 'other')),
  breed           text,
  age_years       integer check (age_years >= 0),
  age_months      integer check (age_months >= 0 and age_months < 12),
  gender          text not null check (gender in ('male', 'female', 'unknown')),
  size            text check (size in ('small', 'medium', 'large', 'extra_large')),
  color           text,
  description     text,
  status          text not null default 'available'
                    check (status in ('available', 'pending', 'adopted', 'foster', 'medical_hold', 'deceased')),
  intake_date     date not null default current_date,
  intake_type     text check (intake_type in ('stray', 'surrender', 'transfer', 'born_in_shelter')),
  microchip_id    text unique,
  is_vaccinated   boolean not null default false,
  is_sterilized   boolean not null default false,
  is_microchipped boolean not null default false,
  special_needs   text,
  good_with_kids  boolean,
  good_with_dogs  boolean,
  good_with_cats  boolean,
  energy_level    text check (energy_level in ('low', 'medium', 'high')),
  shelter_id      uuid references public.shelters(id) on delete restrict,
  created_at      timestamptz not null default now(),
  updated_at      timestamptz not null default now()
);

-- Auto-update updated_at
create or replace function public.handle_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create trigger animals_updated_at
  before update on public.animals
  for each row execute procedure public.handle_updated_at();

-- Indexes for common query patterns
create index animals_status_idx on public.animals(status);
create index animals_species_idx on public.animals(species);
create index animals_shelter_id_idx on public.animals(shelter_id);
create index animals_intake_date_idx on public.animals(intake_date desc);

-- Row Level Security
alter table public.animals enable row level security;

-- Public read for available animals (adoption catalog is public)
create policy "Anyone can view available animals"
  on public.animals for select
  using (status = 'available');

-- Staff can read all animals
create policy "Staff can view all animals"
  on public.animals for select
  using (auth.jwt() ->> 'role' in ('staff', 'admin'));

-- Staff can insert
create policy "Staff can insert animals"
  on public.animals for insert
  with check (auth.jwt() ->> 'role' in ('staff', 'admin'));

-- Staff can update
create policy "Staff can update animals"
  on public.animals for update
  using (auth.jwt() ->> 'role' in ('staff', 'admin'));

-- Only admin can delete (soft delete preferred via status)
create policy "Admin can delete animals"
  on public.animals for delete
  using (auth.jwt() ->> 'role' = 'admin');
```

## Acceptance Criteria

- [ ] Migration file created at `supabase/migrations/YYYYMMDDHHMMSS_create_animals_table.sql`
- [ ] All columns defined with correct types and constraints
- [ ] `updated_at` trigger implemented and working
- [ ] All 4 indexes created
- [ ] RLS enabled with 5 policies (public read available, staff read all, staff insert, staff update, admin delete)
- [ ] Migration applies cleanly via `supabase db push` with no errors
- [ ] `supabase db diff` shows no unexpected drift after applying

## Implementation Notes

- Do NOT use Prisma — all schema changes go through Supabase SQL migrations
- Migration filename must be timestamped: `supabase db migrate new create_animals_table` generates the file
- The `shelters` table may not exist yet — handle with a conditional or create a minimal shelters table in the same migration
- `species` enum uses a check constraint (not a PostgreSQL ENUM type) to allow easier future expansion without `ALTER TYPE`
- `status` field uses soft deletes — prefer updating status to 'deceased' over hard DELETE

## Related

- EPIC-1 / S01 — Animal data model and schema
- Blocked by: none
- Blocks: T02 (migrations), S02 (CRUD operations), S03 (adoption request), S04 (photo upload — needs animal record to exist)
