"""Integration tests for email notification system.

Tests verify:
  - App starts successfully with notification handlers configured
  - Email service defaults to disabled in test environment
  - Notification infrastructure does not break existing endpoints
"""

import pytest
from httpx import AsyncClient
from src.config import get_settings
from src.notifications.handlers import NotificationHandlers
from src.notifications.service import EmailService
from src.notifications.templates import TemplateRenderer


@pytest.mark.asyncio
@pytest.mark.integration
async def test_email_service_disabled_in_test_env(client: AsyncClient) -> None:
    """Verify email sending is disabled by default in test environment.

    The SMTP_ENABLED env var defaults to False, so no real SMTP connections
    are made during testing.
    """
    settings = get_settings()
    assert (
        settings.smtp_enabled is False
    ), "SMTP should be disabled in test environment (set SMTP_ENABLED=false)"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_app_starts_with_notification_handlers(client: AsyncClient) -> None:
    """Verify the app starts and health endpoint works with notification code loaded.

    This confirms the notification module imports and initialization
    don't break app startup.
    """
    response = await client.get("/health")
    assert response.status_code == 200


@pytest.mark.asyncio
@pytest.mark.integration
async def test_email_service_construction_with_settings() -> None:
    """Verify EmailService can be constructed from real Settings."""
    settings = get_settings()
    service = EmailService(settings)
    assert service.is_enabled is False  # Default: disabled


@pytest.mark.asyncio
@pytest.mark.integration
async def test_notification_handlers_can_register_on_bus() -> None:
    """Verify NotificationHandlers registers without error on a fresh bus."""
    from src.events.bus import EventBus

    settings = get_settings()
    email_service = EmailService(settings)
    renderer = TemplateRenderer()
    handlers = NotificationHandlers(email_service, renderer)

    bus = EventBus()
    handlers.register(bus)

    assert bus.subscriber_count == 2  # adoption + donation handlers


@pytest.mark.asyncio
@pytest.mark.integration
async def test_template_renderer_loads_all_templates() -> None:
    """Verify all expected templates can be loaded from disk."""
    renderer = TemplateRenderer()
    assert renderer.has_template("base")
    assert renderer.has_template("adoption_status_changed")
    assert renderer.has_template("donation_received")
    assert renderer.has_template("welcome")
