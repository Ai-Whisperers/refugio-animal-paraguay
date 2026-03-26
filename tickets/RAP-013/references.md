# RAP-013 References

## Story
- `planning/epics/EPIC-0-cross-cutting/stories/S01-cors-rate-limiting-errors/STORY.md`

## Files to Create
- `src/schemas/error.py` — ErrorResponse, ValidationErrorDetail
- `src/middleware/__init__.py` — package init
- `src/middleware/error_handler.py` — exception handlers
- `src/middleware/rate_limit.py` — slowapi limiter
- `src/middleware/request_id.py` — request ID middleware
- `tests/unit/test_error_schema.py`
- `tests/integration/test_cors_rate_limit.py`

## Files to Modify
- `src/config.py` — add ALLOWED_ORIGINS, RATE_LIMIT_ENABLED
- `src/app.py` — register middleware and handlers
- `pyproject.toml` — add slowapi dependency
