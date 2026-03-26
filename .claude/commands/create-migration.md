---
name: create-migration
description: Create a database migration script from schema change description
allowed-tools: Bash, Read, Write, Glob, Grep
---

@.claude/rules/quality-standards.md

Create a versioned, reversible database migration script from a description of the schema change.

## Steps

**Step 1** — Understand the schema change:
- If argument provided: use that as the change description
- Otherwise: ask what change is needed before proceeding

**Step 2** — Inspect existing migration state:
```bash
# Find existing migrations (common patterns)
ls -la migrations/ 2>/dev/null || \
ls -la db/migrations/ 2>/dev/null || \
ls -la alembic/versions/ 2>/dev/null || \
echo "No migrations directory found"

# Find current schema if exists
find . -name "*.sql" -path "*/schema*" 2>/dev/null | head -5
find . -name "models.py" -o -name "schema.py" 2>/dev/null | head -5
```

**Step 3** — Determine migration framework:
- Check for: Alembic (`alembic.ini`), Django (`manage.py`), Flyway (`flyway.conf`), raw SQL
- If Alembic: use `alembic revision --autogenerate -m "description"` workflow
- If Django: use `python manage.py makemigrations` workflow
- If raw SQL: generate numbered file (e.g. `V003__add_donor_gdpr_fields.sql`)

**Step 4** — Generate the migration:

For **raw SQL** (Flyway-style versioning):
```sql
-- File: migrations/V[N]__[description].sql
-- Description: [what this migration does]
-- Author: [ticket ID]
-- Date: YYYY-MM-DD

-- ==== UP ====

ALTER TABLE [table] ADD COLUMN [column] [type] [constraints];

CREATE INDEX CONCURRENTLY [idx_name] ON [table]([column]);

-- ==== DOWN (rollback) ====
-- To roll back: psql -f migrations/undo/V[N]__[description]_undo.sql

ALTER TABLE [table] DROP COLUMN [column];
DROP INDEX IF EXISTS [idx_name];
```

For **Alembic**:
```python
"""[description]

Revision ID: [auto-generated]
Revises: [previous revision]
Create Date: YYYY-MM-DD
"""
from alembic import op
import sqlalchemy as sa


def upgrade() -> None:
    op.add_column('[table]',
        sa.Column('[column]', sa.String(255), nullable=True)
    )
    op.create_index('[idx_name]', '[table]', ['[column]'])


def downgrade() -> None:
    op.drop_index('[idx_name]', table_name='[table]')
    op.drop_column('[table]', '[column]')
```

**Step 5** — Safety checklist before writing file:

- [ ] Migration is reversible (downgrade/rollback exists)
- [ ] No data loss in upgrade path (column drops are in downgrade only)
- [ ] Indexes use `CONCURRENTLY` for large tables (avoids table lock)
- [ ] NOT NULL columns have a DEFAULT or are added nullable first
- [ ] Filename follows existing numbering convention

**Step 6** — Write the migration file and summarize:

```markdown
## Migration Created

File: migrations/[filename]
Change: [what it does]
Tables affected: [list]
Reversible: Yes — run [undo command]

To apply:
  [exact command to run]

To roll back:
  [exact command to roll back]
```

## Rules

- Always include a rollback / downgrade path — never one-way migrations
- Never DROP columns in the upgrade — add nullable first, backfill, then drop in a follow-up
- Large table indexes must be `CREATE INDEX CONCURRENTLY`
- NOT NULL constraints on existing tables require a DEFAULT or a two-phase migration
- Never modify existing migration files — always create new ones
- Include ticket ID in migration description/comment
