.PHONY: help dev test lint type-check format security migrate seed docker-up docker-down clean all-checks

PYTHON := python3
PYTEST := $(PYTHON) -m pytest
RUFF := $(PYTHON) -m ruff
BLACK := $(PYTHON) -m black
PYRIGHT := $(PYTHON) -m pyright
BANDIT := $(PYTHON) -m bandit

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ── Development ───────────────────────────────────────────

dev: ## Start development server with auto-reload
	PYTHONPATH=. $(PYTHON) -m uvicorn src.app:app --reload --host 0.0.0.0 --port 8000

install: ## Install all dependencies (including dev)
	pip install -e ".[dev]" --break-system-packages

# ── Quality Gates ─────────────────────────────────────────

test: ## Run all tests with coverage
	PYTHONPATH=. $(PYTEST) --tb=short --cov=src --cov-report=term-missing --cov-fail-under=80

test-unit: ## Run unit tests only
	PYTHONPATH=. $(PYTEST) tests/unit/ --tb=short -v

test-integration: ## Run integration tests only
	PYTHONPATH=. $(PYTEST) tests/integration/ --tb=short -v

lint: ## Run linter (ruff)
	$(RUFF) check src/ tests/

lint-fix: ## Auto-fix lint issues
	$(RUFF) check src/ tests/ --fix

type-check: ## Run type checker (pyright)
	PYTHONPATH=. $(PYRIGHT) src/

format: ## Check code formatting (black)
	$(BLACK) --check src/ tests/

format-fix: ## Auto-format code (black)
	$(BLACK) src/ tests/

security: ## Run security scan (bandit)
	$(BANDIT) -r src/ -q

all-checks: lint type-check format test security ## Run ALL quality gates (pre-commit)
	@echo "All checks passed."

# ── Database ──────────────────────────────────────────────

migrate: ## Run database migrations
	PYTHONPATH=. $(PYTHON) -m alembic upgrade head

migrate-new: ## Create new migration (usage: make migrate-new MSG="description")
	PYTHONPATH=. $(PYTHON) -m alembic revision --autogenerate -m "$(MSG)"

migrate-history: ## Show migration history
	PYTHONPATH=. $(PYTHON) -m alembic history --verbose

# ── Docker ────────────────────────────────────────────────

docker-up: ## Start all services (API + DB)
	docker compose up -d

docker-down: ## Stop all services
	docker compose down

docker-build: ## Rebuild Docker image
	docker compose build

docker-logs: ## Follow container logs
	docker compose logs -f api

# ── Cleanup ───────────────────────────────────────────────

clean: ## Remove cache files
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
