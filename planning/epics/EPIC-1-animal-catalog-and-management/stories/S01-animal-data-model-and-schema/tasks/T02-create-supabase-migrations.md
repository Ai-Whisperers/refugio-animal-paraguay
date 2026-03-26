---
epic: EPIC-1
story: S01
task: T02
title: Configure Alembic Migration Workflow and Database Management Commands
status: pending
effort_hours: 2
priority: high
dependencies:
  - T01-define-supabase-schema-for-animals-table
---

## Overview

Establish the Alembic migration workflow as the single authoritative mechanism for all PostgreSQL schema changes. This task configures alembic.ini and alembic/env.py to connect to the correct database, documents the standard commands developers use to create, apply, and roll back migrations, and establishes the convention for running Alembic in both local development and CI/CD environments.

## Why This Matters

Without a documented migration workflow, developers apply schema changes ad hoc — some directly in psql, some by editing the database container, and some by running Alembic. This divergence makes it impossible to replay the schema creation reliably, breaks staging and production deployments, and causes test failures when the test database schema diverges from what the application expects. Establishing Alembic as the single path for all schema changes means any developer can clone the repository, run one command, and have a fully initialized database matching the current codebase state.

## Context

The project uses Alembic with SQLAlchemy 2.x. Alembic uses the same DATABASE_URL environment variable that FastAPI uses for its connection pool. The development database runs in Docker; the test database is a separate PostgreSQL database that the pytest fixtures connect to. The alembic/env.py file must import all SQLAlchemy models so that --autogenerate can detect model changes. This is a common footgun: if a model is not imported in env.py, Alembic does not see it and will not generate a migration for it.

## Implementation Steps

### Step 1: Configure alembic.ini

The alembic.ini file at the repository root contains the script_location key pointing to the alembic/ directory. The sqlalchemy.url key in alembic.ini should be set to a placeholder value that is overridden at runtime by the env.py file reading the DATABASE_URL environment variable. Never hardcode the actual database credentials into alembic.ini, as that file is committed to version control.

### Step 2: Configure alembic/env.py

The env.py file is the entry point Alembic uses to establish the database connection and discover models. At the top of env.py, import all SQLAlchemy model classes: at minimum, import Animal from src.models.animal and Base from src.database. Set target_metadata to Base.metadata after all model imports are complete. This is what enables --autogenerate to produce accurate migrations.

In the run_migrations_online function, read the DATABASE_URL from the environment using os.environ and pass it to create_engine rather than reading it from alembic.ini. This ensures that the same env.py works in local development (where DATABASE_URL points to the Docker container), in CI/CD (where it points to the GitHub Actions PostgreSQL service), and in production (where it reads from a secrets manager or environment injection).

### Step 3: Define Standard Development Commands

Document the following commands as the standard workflow for all schema work. These should be written into the project README and referenced in any onboarding documentation.

To apply all pending migrations and bring the database to the current head state, run alembic upgrade head. This is the command that the application startup sequence should call automatically via a startup event in src/main.py, so that the database schema is always current when the FastAPI application starts. Alternatively, run it as a separate step before starting the application.

To generate a new migration after modifying a SQLAlchemy model, run alembic revision with the --autogenerate flag and a descriptive message using the --message flag. The message should describe what changed, such as "add microchip number to animals table" or "create adoption requests table." Alembic generates a timestamped migration file in alembic/versions/. Always review the generated file before committing it — autogenerate is helpful but not infallible, especially for index changes and server defaults.

To roll back the most recent migration, run alembic downgrade minus one. To roll back to a specific migration, run alembic downgrade followed by the migration's revision identifier, which is the alphanumeric prefix in the migration filename.

To inspect the current migration state of the database, run alembic current. This shows the revision identifier of the most recently applied migration. To see the full migration history, run alembic history with the --verbose flag.

To reset the development database completely (drop all tables and re-apply migrations from scratch), drop the database manually in psql and re-run alembic upgrade head. There is no single Alembic command for a full reset — this is intentional, as destructive operations on a database should require explicit human action rather than a one-liner script.

### Step 4: Handle the Test Database

The pytest test suite uses a separate database named after the main database with a test_ prefix, or a dedicated test database URL configured in the TEST_DATABASE_URL environment variable. The test database must have migrations applied before the test suite runs. The conftest.py file at the repository root includes a session-scoped fixture that runs alembic upgrade head against the test database URL at the start of each pytest session and, optionally, alembic downgrade base at the end to leave the database clean.

This ensures that the test database schema always matches the current migration head, even after developers add new migrations. There is no separate mechanism for initializing the test schema — Alembic is the single source of truth for both development and test databases.

### Step 5: Seed Data Separation

Migration files in alembic/versions/ should contain only schema changes — CREATE TABLE, CREATE INDEX, ALTER TABLE, CREATE TYPE, and their inverses. Seed data (representative test animals, default shelter records) must not live in migration files, because migrations must be reversible and seed data complicates rollbacks. Seed data lives in a dedicated file, described in T03.

The one exception is default configuration values for shelter settings that the application cannot function without. If the application requires a row in a settings table to start correctly, that INSERT can live in its own migration file clearly labeled as data migration. Document this clearly in the migration's docstring.

## Acceptance Criteria

- alembic/env.py imports all model classes and sets target_metadata to Base.metadata
- alembic/env.py reads DATABASE_URL from the environment, not from alembic.ini
- alembic upgrade head applies all existing migrations without error against a fresh database
- alembic downgrade minus one reverses the most recent migration without error
- alembic revision --autogenerate detects changes when a model column is added
- The test database setup in conftest.py applies migrations before the test session begins
- No credentials are hardcoded in alembic.ini or env.py

## Common Issues and Solutions

If alembic revision --autogenerate produces an empty migration (no detected changes), a model file is not imported in env.py. Add the missing import and re-run autogenerate.

If alembic upgrade head fails with a table already exists error, the database was initialized by some mechanism other than Alembic. The cleanest resolution is to stamp the database with the correct revision using alembic stamp followed by the head revision identifier, which tells Alembic the schema is already current without re-applying migrations.

If the test database migration fixture runs but tests still fail with missing table errors, the session fixture may be scoped incorrectly. Ensure the migration fixture uses session scope (runs once per pytest session) rather than function scope (which would try to apply migrations before every test function and fail on the second run because the table already exists).

## Related Tasks

- S01/T01: Define SQLAlchemy Animal model — creates the model that this workflow manages
- S01/T03: Implement seed data for testing — the seed mechanism that runs after migrations initialize the schema
- EPIC-9/S02: CI/CD pipeline configuration — wires alembic upgrade head into the deployment pipeline
