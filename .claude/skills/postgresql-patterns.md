---
name: postgresql-patterns
description: PostgreSQL schema design, indexing strategy, migration patterns, query optimization, and common pitfalls
load-when: Schema design, writing migrations, Alembic, indexes, SQL queries, N+1 prevention FOR THIS PROJECT
not-when: FastAPI code, Python logic, payment processing — use domain-specific skills for those
project-specific: Refugio table naming, UUID PKs required, TIMESTAMPTZ always, animal status EXCLUDE constraint
---

# PostgreSQL Patterns

Load this skill when designing schemas, writing migrations, or optimizing queries.

## Schema Design Conventions

### Table Naming

```sql
-- ✅ Lowercase, plural, snake_case, no Hungarian notation
CREATE TABLE animals (...);
CREATE TABLE adoption_requests (...);
CREATE TABLE donor_transactions (...);

-- ❌ Mixed case, singular, abbreviations
CREATE TABLE Animal (...);
CREATE TABLE tbl_AdoptReq (...);
```

### Column Conventions

```sql
CREATE TABLE animals (
    -- Primary key: always 'id', UUID preferred for external-facing resources
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Foreign keys: {referenced_table_singular}_id
    shelter_id  UUID NOT NULL REFERENCES shelters(id),
    species_id  UUID REFERENCES species(id),   -- nullable if optional

    -- Timestamps: always include both, use timezone-aware
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Soft delete: prefer status enum over deleted_at
    status      TEXT NOT NULL DEFAULT 'available'
                CHECK (status IN ('available', 'reserved', 'adopted', 'deceased')),

    -- Boolean: explicit NOT NULL + default
    is_neutered BOOLEAN NOT NULL DEFAULT FALSE,
    is_vaccinated BOOLEAN NOT NULL DEFAULT FALSE
);
```

### UUID vs Serial

| Use | Primary Key Type |
|-----|-----------------|
| Externally-visible IDs (API responses, URLs) | `UUID` — prevents enumeration attacks |
| Internal join tables, audit logs | `BIGINT GENERATED ALWAYS AS IDENTITY` — smaller, faster |
| Existing tables | Don't change — migration risk not worth it |

---

## Indexing Strategy

### When to Add Indexes

```sql
-- ✅ Foreign keys (always index)
CREATE INDEX idx_adoption_requests_animal_id ON adoption_requests(animal_id);
CREATE INDEX idx_adoption_requests_adopter_id ON adoption_requests(adopter_id);

-- ✅ Columns used in WHERE clauses frequently
CREATE INDEX idx_animals_status ON animals(status);
CREATE INDEX idx_animals_shelter_id_status ON animals(shelter_id, status);  -- composite

-- ✅ Columns used in ORDER BY on large tables
CREATE INDEX idx_donations_created_at ON donations(created_at DESC);

-- ✅ Unique constraints (creates index automatically)
ALTER TABLE donors ADD CONSTRAINT uq_donors_email UNIQUE (email);

-- ✅ Partial index for common filtered queries
CREATE INDEX idx_animals_available
    ON animals(shelter_id, created_at)
    WHERE status = 'available';

-- ✅ Full text search
CREATE INDEX idx_animals_name_fts ON animals USING GIN(to_tsvector('english', name));
```

### When NOT to Add Indexes

```sql
-- ❌ Low-cardinality boolean columns (rarely selective enough)
-- Don't index: is_neutered, is_vaccinated

-- ❌ Columns never queried in WHERE/ORDER/JOIN
-- Don't index: notes TEXT, internal_remarks TEXT

-- ❌ Very small tables (<1000 rows) — full scan is faster
```

### Index Maintenance

```sql
-- Check index usage (find unused indexes)
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
WHERE idx_scan = 0
ORDER BY schemaname, tablename;

-- Check table bloat
SELECT relname, n_live_tup, n_dead_tup, last_vacuum, last_autovacuum
FROM pg_stat_user_tables
ORDER BY n_dead_tup DESC;
```

---

## Migration Patterns

### Safe Column Addition

```sql
-- ✅ Always add nullable first, then backfill, then add NOT NULL
-- Step 1: Add nullable
ALTER TABLE donors ADD COLUMN gdpr_consent_at TIMESTAMPTZ;

-- Step 2: Backfill existing rows (run as separate migration)
UPDATE donors SET gdpr_consent_at = created_at WHERE gdpr_consent_at IS NULL;

-- Step 3: Add NOT NULL constraint (only after backfill verified)
ALTER TABLE donors ALTER COLUMN gdpr_consent_at SET NOT NULL;
```

### Safe Index Creation

```sql
-- ✅ Always CONCURRENTLY on production tables (no table lock)
CREATE INDEX CONCURRENTLY idx_donors_email ON donors(email);

-- ❌ Without CONCURRENTLY — locks entire table during creation
CREATE INDEX idx_donors_email ON donors(email);
```

### Renaming Columns Safely

```sql
-- Never rename directly — breaks existing queries/code in-flight
-- Safe approach: add new column, dual-write, migrate, drop old

-- Step 1: Add new column
ALTER TABLE donors ADD COLUMN full_name TEXT;

-- Step 2: Copy data
UPDATE donors SET full_name = name;

-- Step 3: (After code deployed to use full_name) Drop old column
ALTER TABLE donors DROP COLUMN name;
```

### Migration File Template

```sql
-- migrations/0042_add_gdpr_consent_to_donors.sql
-- Up migration

BEGIN;

ALTER TABLE donors
    ADD COLUMN gdpr_consent_given BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN gdpr_consent_at TIMESTAMPTZ;

COMMENT ON COLUMN donors.gdpr_consent_given
    IS 'EU GDPR: explicit consent to receive marketing communications';
COMMENT ON COLUMN donors.gdpr_consent_at
    IS 'Timestamp when GDPR consent was given or revoked';

COMMIT;

-- Down migration (keep in same file or separate rollback file)
-- BEGIN;
-- ALTER TABLE donors DROP COLUMN gdpr_consent_given, DROP COLUMN gdpr_consent_at;
-- COMMIT;
```

---

## Common Query Patterns

### Pagination — Keyset (cursor-based)

```sql
-- More efficient than OFFSET for large tables
-- Request: "give me 20 animals after cursor id=abc"

SELECT id, name, status, created_at
FROM animals
WHERE shelter_id = $1
  AND status = 'available'
  AND (created_at, id) < ($cursor_created_at, $cursor_id)   -- cursor condition
ORDER BY created_at DESC, id DESC
LIMIT 20;
```

### Upsert

```sql
-- Insert or update on conflict
INSERT INTO animal_vaccinations (animal_id, vaccine_type, administered_at)
VALUES ($1, $2, $3)
ON CONFLICT (animal_id, vaccine_type)
DO UPDATE SET
    administered_at = EXCLUDED.administered_at,
    updated_at = NOW()
WHERE animal_vaccinations.administered_at < EXCLUDED.administered_at;
```

### Aggregation with Window Functions

```sql
-- Running total of donations per donor
SELECT
    donor_id,
    amount,
    currency,
    created_at,
    SUM(amount_eur) OVER (
        PARTITION BY donor_id
        ORDER BY created_at
        ROWS UNBOUNDED PRECEDING
    ) AS cumulative_donated_eur
FROM donations
WHERE status = 'completed'
ORDER BY donor_id, created_at;
```

### Soft Delete Pattern

```sql
-- Prefer status enum over deleted_at
-- deleted_at requires IS NULL in every query — easy to forget

-- ✅ Status-based
WHERE status != 'deleted'

-- Or use Row-Level Security to exclude deleted rows automatically
CREATE POLICY hide_deleted_animals ON animals
    USING (status != 'deleted');
```

### JSONB for Flexible Attributes

```sql
-- Store flexible metadata without schema changes
ALTER TABLE animals ADD COLUMN attributes JSONB NOT NULL DEFAULT '{}';

-- Query JSONB
SELECT * FROM animals
WHERE attributes->>'breed' = 'Labrador'
  AND (attributes->>'weight_kg')::numeric > 20;

-- Index specific JSONB key
CREATE INDEX idx_animals_breed ON animals ((attributes->>'breed'));

-- Full JSONB index (larger, use for multi-key queries)
CREATE INDEX idx_animals_attributes ON animals USING GIN(attributes);
```

---

## Performance Patterns

### EXPLAIN ANALYZE

```sql
-- Always use EXPLAIN ANALYZE BUFFERS for real execution stats
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT a.*, ar.status as request_status
FROM animals a
JOIN adoption_requests ar ON ar.animal_id = a.id
WHERE a.shelter_id = 'uuid-here'
  AND a.status = 'available';
```

Key things to look for:
- `Seq Scan` on large tables → missing index
- `Hash Join` vs `Nested Loop` → hash joins are efficient for large sets
- High `Buffers: shared hit=0, read=N` → cold cache or missing index
- `rows=1000 (actual rows=1)` → stale statistics, run `ANALYZE`

### N+1 Query Prevention

```sql
-- ❌ N+1: Loading animals then querying vaccinations one-by-one

-- ✅ Single query with LEFT JOIN
SELECT
    a.id,
    a.name,
    a.status,
    COALESCE(
        JSON_AGG(
            JSON_BUILD_OBJECT(
                'vaccine', v.vaccine_type,
                'date', v.administered_at
            ) ORDER BY v.administered_at DESC
        ) FILTER (WHERE v.id IS NOT NULL),
        '[]'
    ) AS vaccinations
FROM animals a
LEFT JOIN animal_vaccinations v ON v.animal_id = a.id
WHERE a.shelter_id = $1
GROUP BY a.id;
```

---

## Constraints and Data Integrity

```sql
-- Always enforce at database level, not just application level
CREATE TABLE adoption_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    animal_id UUID NOT NULL REFERENCES animals(id) ON DELETE RESTRICT,
    adopter_id UUID NOT NULL REFERENCES adopters(id) ON DELETE RESTRICT,
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'approved', 'rejected', 'completed', 'cancelled')),

    -- Business rule: one active request per animal
    CONSTRAINT uq_one_active_request_per_animal
        EXCLUDE USING btree (animal_id WITH =)
        WHERE (status IN ('pending', 'approved')),

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### Updated_at Auto-Update Trigger

```sql
-- Reusable trigger function
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to table
CREATE TRIGGER trg_animals_updated_at
    BEFORE UPDATE ON animals
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();
```

---

## Common Anti-Patterns

```sql
-- ❌ SELECT * in application code (returns unused columns, breaks on schema change)
SELECT * FROM animals;

-- ✅ Explicit column list
SELECT id, name, status, photo_url FROM animals;

-- ❌ NOT IN with subquery (breaks if subquery returns NULL)
SELECT * FROM animals WHERE id NOT IN (SELECT animal_id FROM adoption_requests);

-- ✅ NOT EXISTS
SELECT * FROM animals a
WHERE NOT EXISTS (
    SELECT 1 FROM adoption_requests ar WHERE ar.animal_id = a.id
);

-- ❌ OR conditions that prevent index use
WHERE status = 'available' OR status = 'reserved'

-- ✅ IN (uses index)
WHERE status IN ('available', 'reserved')

-- ❌ Function wrapping indexed column (defeats index)
WHERE DATE(created_at) = '2026-03-25'

-- ✅ Range condition (uses index)
WHERE created_at >= '2026-03-25' AND created_at < '2026-03-26'
```
