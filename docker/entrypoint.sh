#!/bin/sh
# Entrypoint for the Refugio Animal Paraguay API container.
# Runs Alembic migrations before starting uvicorn.
#
# Alembic uses SQLAlchemy sync engine, so the +asyncpg driver prefix must be
# stripped from DATABASE_URL before passing it to alembic upgrade.
set -e

# Convert asyncpg URL → sync psycopg2 URL for Alembic
# Use sed (POSIX sh compatible) — bash ${var/find/replace} does not work in dash
ALEMBIC_DATABASE_URL=$(echo "${DATABASE_URL}" | sed 's/+asyncpg//')

echo "Running database migrations..."
DATABASE_URL="${ALEMBIC_DATABASE_URL}" alembic upgrade head

echo "Starting API server..."
exec uvicorn src.app:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers "${UVICORN_WORKERS:-1}"
