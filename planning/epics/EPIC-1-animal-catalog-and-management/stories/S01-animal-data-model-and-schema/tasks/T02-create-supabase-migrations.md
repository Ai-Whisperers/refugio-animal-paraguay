---
task: T02
story: S01
epic: EPIC-1
title: Set up Supabase migration workflow and seed data
status: ready
priority: high
agent_type: devops
created: 2026-03-25T17:13:26.725653
claimed_by: null
claimed_at: null
branch: null
pr_url: null
---

# T02: Set up Supabase migration workflow and seed data

## Description

Configure the Supabase CLI migration workflow so that schema changes are tracked as SQL files, reviewable in git, and reproducible across development and production environments. Also create seed data so developers can test the animal catalog without manually inserting records.

## Context

- Architecture reference: `docs/ARCHITECTURE.md`
- Supabase CLI docs: `supabase --help` or `npx supabase --help`
- Migrations live in: `supabase/migrations/`
- Seed data lives in: `supabase/seed.sql`
- Local Supabase: started with `supabase start` (requires Docker)

## Tasks to implement

### 1. Supabase CLI setup

Ensure `supabase/config.toml` exists and is configured for the project:

```toml
project_id = "refugio-animal-paraguay"

[db]
port = 54322
shadow_port = 54320
major_version = 15

[api]
port = 54321
schemas = ["public", "storage", "graphql_public"]
extra_search_path = ["public", "extensions"]

[studio]
port = 54323

[auth]
site_url = "http://localhost:3000"
additional_redirect_urls = ["https://localhost:3000"]
```

### 2. Package.json scripts

Add to `package.json`:
```json
{
  "scripts": {
    "db:start": "supabase start",
    "db:stop": "supabase stop",
    "db:reset": "supabase db reset",
    "db:push": "supabase db push",
    "db:diff": "supabase db diff",
    "db:migrate": "supabase db migrate new",
    "db:seed": "supabase db reset --db-url $DATABASE_URL",
    "db:types": "supabase gen types typescript --local > src/types/database.types.ts"
  }
}
```

### 3. Seed data

Create `supabase/seed.sql` with realistic sample animals for local development:

```sql
-- Seed: Sample animals for local development
-- Does not run in production

insert into public.animals (
  name, species, breed, age_years, age_months, gender, size, color,
  description, status, intake_date, intake_type,
  is_vaccinated, is_sterilized, is_microchipped,
  good_with_kids, good_with_dogs, good_with_cats, energy_level
) values
  ('Luna', 'dog', 'Mestizo', 2, 0, 'female', 'medium', 'café y blanco',
   'Luna es una perra cariñosa y juguetona. Se lleva bien con niños y otros perros.',
   'available', '2026-01-15', 'stray',
   true, true, false, true, true, false, 'medium'),

  ('Misi', 'cat', 'Doméstico', 1, 6, 'male', 'small', 'negro',
   'Misi es tranquilo y le encanta estar en interiores. Ideal para apartamento.',
   'available', '2026-02-01', 'surrender',
   true, true, false, true, false, true, 'low'),

  ('Thor', 'dog', 'Labrador mestizo', 3, 0, 'male', 'large', 'amarillo',
   'Thor es activo y necesita espacio para correr. Muy leal y protector.',
   'available', '2026-01-28', 'stray',
   true, false, false, false, true, false, 'high'),

  ('Cleo', 'cat', 'Siamés mestizo', 4, 0, 'female', 'small', 'beige y marrón',
   'Cleo es independiente pero afectuosa con su familia. No se lleva bien con otros gatos.',
   'available', '2026-02-10', 'surrender',
   true, true, true, true, false, false, 'low'),

  ('Max', 'dog', 'Mestizo pequeño', 5, 0, 'male', 'small', 'blanco y negro',
   'Max es un perro mayor tranquilo, perfecto para una familia tranquila.',
   'pending', '2025-12-01', 'stray',
   true, true, true, true, true, true, 'low');
```

### 4. TypeScript type generation

After migrations run, generate TypeScript types:
```bash
npm run db:types
```

This creates `src/types/database.types.ts` — auto-generated, never edit manually.

### 5. .gitignore additions

Ensure `supabase/.branches` and `supabase/.temp` are gitignored:
```
# In .gitignore
supabase/.branches
supabase/.temp
```

## Acceptance Criteria

- [ ] `supabase/config.toml` configured for the project
- [ ] `package.json` has all `db:*` scripts
- [ ] `supabase/seed.sql` contains at least 5 realistic sample animals in Spanish
- [ ] `supabase db reset` runs cleanly (applies migrations + seed without errors)
- [ ] `npm run db:types` generates `src/types/database.types.ts` successfully
- [ ] `.gitignore` excludes Supabase temporary files
- [ ] `supabase/` directory is committed (migrations + config + seed, not temp files)
- [ ] README includes local development database setup instructions

## Implementation Notes

- Seed data uses Spanish descriptions — this is the production language of the platform
- `supabase db reset` drops and recreates the local database — safe locally, never run against production
- `DATABASE_URL` for local dev: `postgresql://postgres:postgres@localhost:54322/postgres`
- TypeScript types are auto-generated — add `src/types/database.types.ts` to `.gitignore` OR commit it (team choice — document the decision)
- Migration filenames are timestamped by the CLI — never rename them after creation

## Related

- EPIC-1 / S01 — Animal data model and schema
- Depends on: T01 (animals table schema must exist before seeding)
- Blocks: S02 (CRUD operations need working local database)
