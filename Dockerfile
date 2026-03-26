# syntax=docker/dockerfile:1
# ---------------------------------------------------------------------------
# Stage 1: builder — install dependencies into /install
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS builder

WORKDIR /app

# Install build deps needed by some packages (psycopg2, cryptography)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
# Install runtime deps only (no [dev] extras)
RUN pip install --no-cache-dir --prefix=/install ".[dev]" \
    && pip install --no-cache-dir --prefix=/install .

# ---------------------------------------------------------------------------
# Stage 2: runtime — lean image, no build tools
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

# Runtime system lib: libpq for asyncpg/psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /install /usr/local

WORKDIR /app

# Copy application source
COPY src/ ./src/
COPY alembic.ini ./

# Entrypoint script that runs migrations then starts the server
COPY docker/entrypoint.sh ./entrypoint.sh
RUN chmod +x ./entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
