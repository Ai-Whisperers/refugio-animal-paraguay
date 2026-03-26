---
task: T03
story: S01
epic: EPIC-4
title: Implement audit logging
status: ready
priority: medium
created: 2026-03-25T17:13:26.730220
---

# T03: Implement audit logging

## Description

Implement row-level audit logging for all five medical tables (`veterinarians`, `medical_records`, `vaccinations`, `medications`, `treatments`). Every INSERT, UPDATE, and DELETE must be recorded in an `audit_log` table with who made the change, when, what changed (old vs new row), and from which table. This is required for regulatory compliance (veterinary records must be tamper-evident) and for debugging data quality issues.

## Acceptance Criteria

- [ ] `audit_log` table created to store all change events
- [ ] PostgreSQL trigger function created that captures old and new row data as JSONB
- [ ] Triggers attached to all five medical tables for INSERT, UPDATE, DELETE
- [ ] `audit_log` is append-only — no UPDATE or DELETE policies
- [ ] Only `service_role` can read `audit_log` — no direct user access via RLS
- [ ] Utility function `get_animal_audit_trail(animal_id uuid)` created for admin review
- [ ] Unit tests verify audit entries are created on each mutation

## Implementation Notes

### Table: `audit_log`

```sql
-- supabase/migrations/20260401000007_create_audit_log.sql
-- Rollback: drop table if exists audit_log cascade;

create table audit_log (
  id          bigint generated always as identity primary key,
  table_name  text not null,
  record_id   uuid not null,        -- the primary key of the changed row
  operation   text not null check (operation in ('INSERT', 'UPDATE', 'DELETE')),
  changed_by  uuid,                 -- auth.uid() at time of change; null if service_role
  old_data    jsonb,                -- null for INSERT
  new_data    jsonb,                -- null for DELETE
  changed_at  timestamptz not null default now()
);

-- Partition by month for performance (optional but recommended long-term)
create index audit_log_table_record_idx on audit_log(table_name, record_id);
create index audit_log_changed_at_idx on audit_log(changed_at desc);
create index audit_log_changed_by_idx on audit_log(changed_by) where changed_by is not null;

alter table audit_log enable row level security;

-- Append-only: no UPDATE or DELETE policies exist (absence = blocked by RLS)
-- Service role bypasses RLS entirely — internal admin tools use service_role key
-- No SELECT policy for regular authenticated users — audit log is admin-only
```

### Trigger Function

```sql
-- supabase/migrations/20260401000007_create_audit_log.sql (continued)

create or replace function record_audit_log()
returns trigger as $$
begin
  insert into audit_log (
    table_name,
    record_id,
    operation,
    changed_by,
    old_data,
    new_data
  ) values (
    tg_table_name,
    case
      when tg_op = 'DELETE' then old.id
      else new.id
    end,
    tg_op,
    auth.uid(),          -- null when triggered by service_role migrations
    case when tg_op = 'INSERT' then null else to_jsonb(old) end,
    case when tg_op = 'DELETE' then null else to_jsonb(new) end
  );
  return null;           -- AFTER trigger — return value ignored
end;
$$ language plpgsql security definer;
-- security definer: runs as function owner (postgres), not the calling user
-- Required so the trigger can always insert into audit_log regardless of RLS
```

### Attaching Triggers

```sql
-- supabase/migrations/20260401000008_attach_audit_triggers.sql
-- Rollback: drop trigger if exists audit_veterinarians on veterinarians;
--           drop trigger if exists audit_medical_records on medical_records;
--           drop trigger if exists audit_vaccinations on vaccinations;
--           drop trigger if exists audit_medications on medications;
--           drop trigger if exists audit_treatments on treatments;

create trigger audit_veterinarians
  after insert or update or delete on veterinarians
  for each row execute function record_audit_log();

create trigger audit_medical_records
  after insert or update or delete on medical_records
  for each row execute function record_audit_log();

create trigger audit_vaccinations
  after insert or update or delete on vaccinations
  for each row execute function record_audit_log();

create trigger audit_medications
  after insert or update or delete on medications
  for each row execute function record_audit_log();

create trigger audit_treatments
  after insert or update or delete on treatments
  for each row execute function record_audit_log();
```

### Admin Utility: `get_animal_audit_trail`

```sql
-- Returns the full audit trail for a given animal across all medical tables.
-- Used by admin UI to investigate data changes or suspicious edits.
-- security definer: admin app calls this RPC; RLS would otherwise block audit_log reads.

create or replace function get_animal_audit_trail(p_animal_id uuid)
returns table (
  log_id       bigint,
  table_name   text,
  record_id    uuid,
  operation    text,
  changed_by   uuid,
  changed_at   timestamptz,
  old_data     jsonb,
  new_data     jsonb
)
language sql
security definer
stable
as $$
  select
    al.id,
    al.table_name,
    al.record_id,
    al.operation,
    al.changed_by,
    al.changed_at,
    al.old_data,
    al.new_data
  from audit_log al
  where
    -- Match records that reference this animal
    (al.table_name in ('medical_records', 'vaccinations', 'medications', 'treatments')
     and (
       (al.new_data ->> 'animal_id')::uuid = p_animal_id
       or (al.old_data ->> 'animal_id')::uuid = p_animal_id
     ))
  order by al.changed_at desc;
$$;
```

Call from a Server Component in the admin panel:

```typescript
// src/app/admin/animals/[id]/audit/page.tsx
import { createServerComponentClient } from '@supabase/auth-helpers-nextjs'
import { cookies } from 'next/headers'

export default async function AnimalAuditPage({ params }: { params: { id: string } }) {
  const supabase = createServerComponentClient({ cookies })

  // Auth guard: admin only
  const { data: { user } } = await supabase.auth.getUser()
  if (!user) redirect('/login')
  const { data: profile } = await supabase
    .from('profiles')
    .select('role')
    .eq('id', user.id)
    .single()
  if (profile?.role !== 'admin') redirect('/')

  const { data: auditEntries, error } = await supabase.rpc('get_animal_audit_trail', {
    p_animal_id: params.id,
  })

  if (error) throw error

  return <AuditTrailTable entries={auditEntries ?? []} />
}
```

### Unit Tests

```typescript
// src/lib/__tests__/audit-log.test.ts
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!  // service role bypasses RLS for test assertions
)

describe('audit log triggers', () => {
  let animalId: string
  let vetId: string

  beforeAll(async () => {
    // Insert test animal + vet using service role
    const { data: animal } = await supabase.from('animals').insert({ name: 'Test Dog' }).select().single()
    animalId = animal!.id
    const { data: vet } = await supabase.from('veterinarians').insert({ full_name: 'Dr. Test' }).select().single()
    vetId = vet!.id
  })

  it('creates INSERT audit entry when medical record is created', async () => {
    const { data: record } = await supabase
      .from('medical_records')
      .insert({
        animal_id: animalId,
        veterinarian_id: vetId,
        record_type: 'checkup',
        visit_date: '2026-04-01',
        created_by: '00000000-0000-0000-0000-000000000000',  // service role
      })
      .select()
      .single()

    const { data: logs } = await supabase
      .from('audit_log')
      .select()
      .eq('table_name', 'medical_records')
      .eq('record_id', record!.id)
      .eq('operation', 'INSERT')

    expect(logs).toHaveLength(1)
    expect(logs![0].old_data).toBeNull()
    expect(logs![0].new_data).toMatchObject({ record_type: 'checkup' })
  })

  it('creates UPDATE audit entry with old and new data', async () => {
    const { data: record } = await supabase
      .from('medical_records')
      .insert({
        animal_id: animalId,
        record_type: 'intake_exam',
        visit_date: '2026-04-01',
        created_by: '00000000-0000-0000-0000-000000000000',
      })
      .select()
      .single()

    await supabase
      .from('medical_records')
      .update({ notes: 'Updated notes' })
      .eq('id', record!.id)

    const { data: logs } = await supabase
      .from('audit_log')
      .select()
      .eq('table_name', 'medical_records')
      .eq('record_id', record!.id)
      .eq('operation', 'UPDATE')

    expect(logs).toHaveLength(1)
    expect(logs![0].old_data).toMatchObject({ notes: null })
    expect(logs![0].new_data).toMatchObject({ notes: 'Updated notes' })
  })

  it('creates DELETE audit entry with old data preserved', async () => {
    const { data: record } = await supabase
      .from('medical_records')
      .insert({
        animal_id: animalId,
        record_type: 'checkup',
        visit_date: '2026-04-02',
        created_by: '00000000-0000-0000-0000-000000000000',
      })
      .select()
      .single()

    await supabase.from('medical_records').delete().eq('id', record!.id)

    const { data: logs } = await supabase
      .from('audit_log')
      .select()
      .eq('table_name', 'medical_records')
      .eq('record_id', record!.id)
      .eq('operation', 'DELETE')

    expect(logs).toHaveLength(1)
    expect(logs![0].old_data).toMatchObject({ record_type: 'checkup' })
    expect(logs![0].new_data).toBeNull()
  })

  it('audit_log cannot be deleted or updated by authenticated user', async () => {
    // Using anon key here — represents a logged-in user with no special role
    const anonClient = createClient(process.env.SUPABASE_URL!, process.env.SUPABASE_ANON_KEY!)

    const { error: deleteError } = await anonClient.from('audit_log').delete().eq('id', 1)
    expect(deleteError).not.toBeNull()  // RLS blocks delete

    const { error: updateError } = await anonClient
      .from('audit_log')
      .update({ operation: 'INSERT' })
      .eq('id', 1)
    expect(updateError).not.toBeNull()  // RLS blocks update
  })
})
```

### Important Design Notes

- **`security definer` on the trigger function**: The trigger must always be able to write to `audit_log` regardless of who triggered it. Without `security definer`, the trigger runs as the calling user whose RLS may not allow inserting into `audit_log`.
- **Append-only by policy absence**: RLS does not need an explicit DENY policy. Since no UPDATE or DELETE policy exists on `audit_log`, those operations are blocked for all non-service-role connections.
- **JSONB `old_data`/`new_data`**: Captures entire row state — future schema changes to medical tables will still produce valid audit entries without modifying the trigger.
- **`changed_by` null for migrations**: When migrations or seed scripts run as `service_role` or `postgres`, `auth.uid()` returns null. This is expected and not an error.
- **No audit log for `audit_log` itself**: Circular trigger would cause infinite recursion. The trigger is intentionally not applied to `audit_log`.

## Related Issues

- EPIC-4
- S01
- T01 (schema design)
- T02 (migrations create the tables this audit log wraps)
