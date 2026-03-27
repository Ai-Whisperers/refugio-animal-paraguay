"""Unit tests for structured logging configuration (structlog).

Tests cover:
- configure_logging does not raise in dev or production mode
- stdlib logging calls are captured (root logger handler set)
- structlog is configured (bound logger is a structlog BoundLogger)
- Custom log level is respected
- Multiple calls to configure_logging are idempotent (no duplicate handlers)
"""

from __future__ import annotations

import logging

import structlog
from src.logging_config import configure_logging


class TestConfigureLoggingDev:
    """configure_logging in development mode."""

    def test_does_not_raise(self) -> None:
        configure_logging(is_dev=True)

    def test_root_logger_has_exactly_one_handler_after_call(self) -> None:
        configure_logging(is_dev=True)
        root = logging.getLogger()
        assert len(root.handlers) == 1

    def test_calling_twice_does_not_add_duplicate_handler(self) -> None:
        configure_logging(is_dev=True)
        configure_logging(is_dev=True)
        root = logging.getLogger()
        assert len(root.handlers) == 1

    def test_handler_uses_processor_formatter(self) -> None:
        configure_logging(is_dev=True)
        root = logging.getLogger()
        handler = root.handlers[0]
        assert isinstance(handler.formatter, structlog.stdlib.ProcessorFormatter)

    def test_default_log_level_is_info(self) -> None:
        configure_logging(is_dev=True)
        root = logging.getLogger()
        assert root.level == logging.INFO

    def test_structlog_wrapper_class_is_bound_logger(self) -> None:
        configure_logging(is_dev=True)
        # After configure_logging the wrapper class must be BoundLogger.
        config = structlog.get_config()
        assert config["wrapper_class"] is structlog.stdlib.BoundLogger


class TestConfigureLoggingProd:
    """configure_logging in production (JSON) mode."""

    def test_does_not_raise(self) -> None:
        configure_logging(is_dev=False)

    def test_root_logger_has_exactly_one_handler_after_call(self) -> None:
        configure_logging(is_dev=False)
        root = logging.getLogger()
        assert len(root.handlers) == 1

    def test_handler_uses_processor_formatter(self) -> None:
        configure_logging(is_dev=False)
        root = logging.getLogger()
        handler = root.handlers[0]
        assert isinstance(handler.formatter, structlog.stdlib.ProcessorFormatter)

    def test_noisy_loggers_set_to_warning(self) -> None:
        configure_logging(is_dev=False)
        assert logging.getLogger("uvicorn.access").level == logging.WARNING
        assert logging.getLogger("sqlalchemy.engine").level == logging.WARNING
        assert logging.getLogger("httpx").level == logging.WARNING

    def test_noisy_loggers_not_silenced_in_dev(self) -> None:
        # Reset noisy logger levels before calling dev configure so the test
        # is not affected by run order (prod test may set WARNING first).
        for name in ("uvicorn.access", "sqlalchemy.engine", "httpx"):
            logging.getLogger(name).setLevel(logging.NOTSET)
        configure_logging(is_dev=True)
        # In dev mode, noisy loggers are left at NOTSET (inherit from root).
        assert logging.getLogger("uvicorn.access").level == logging.NOTSET


class TestConfigureLoggingLogLevel:
    """Custom log level parameter."""

    def test_debug_level_is_applied(self) -> None:
        configure_logging(is_dev=True, log_level="DEBUG")
        assert logging.getLogger().level == logging.DEBUG

    def test_warning_level_is_applied(self) -> None:
        configure_logging(is_dev=False, log_level="WARNING")
        assert logging.getLogger().level == logging.WARNING

    def test_invalid_level_falls_back_to_info(self) -> None:
        # getattr with default INFO means unknown string → INFO
        configure_logging(is_dev=True, log_level="NOTAREALEVEL")
        assert logging.getLogger().level == logging.INFO
