"""Structured logging configuration using structlog.

Configures both structlog and the stdlib logging module so that:
- All existing ``logging.getLogger(__name__)`` calls in the codebase are
  automatically captured and formatted through structlog processors.
- New code can use ``structlog.get_logger()`` for native structured logging
  with key-value context binding.

Environments:
- Development: human-readable console output with colours and pretty-printed
  key-value pairs (structlog ConsoleRenderer).
- Production / staging: one JSON object per line — ready for log aggregators
  such as Grafana Loki, Datadog, or AWS CloudWatch.

Usage::

    from src.logging_config import configure_logging
    configure_logging(is_dev=settings.app_env == "development")
"""

import logging
import sys

import structlog

# Common processors applied to both stdlib-bridged and native structlog calls
_SHARED_PROCESSORS: list[structlog.types.Processor] = [
    structlog.contextvars.merge_contextvars,
    structlog.stdlib.add_log_level,
    structlog.stdlib.add_logger_name,
    structlog.processors.TimeStamper(fmt="iso", utc=True),
    structlog.processors.StackInfoRenderer(),
]


def configure_logging(*, is_dev: bool, log_level: str = "INFO") -> None:
    """Configure structlog and stdlib logging for the application.

    Call this once at application startup before any loggers are used.

    Args:
        is_dev: When True, use the human-readable console renderer.
                When False (staging/production), output newline-delimited JSON.
        log_level: Root log level string, e.g. ``"DEBUG"`` or ``"WARNING"``.
    """
    # The final renderer differs by environment.
    if is_dev:
        final_renderer: structlog.types.Processor = structlog.dev.ConsoleRenderer(
            colors=True,
        )
    else:
        final_renderer = structlog.processors.JSONRenderer()

    # Configure structlog itself.
    structlog.configure(
        processors=[
            *_SHARED_PROCESSORS,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Build the formatter that stdlib handlers will use so that all
    # ``logging.getLogger(__name__)`` calls also flow through structlog.
    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            final_renderer,
        ],
        foreign_pre_chain=_SHARED_PROCESSORS,
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    # Apply to the root logger so every named logger inherits the config.
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Silence noisy third-party libraries to WARNING unless in debug.
    if not is_dev:
        for noisy in ("uvicorn.access", "sqlalchemy.engine", "httpx"):
            logging.getLogger(noisy).setLevel(logging.WARNING)


__all__ = ["configure_logging"]
