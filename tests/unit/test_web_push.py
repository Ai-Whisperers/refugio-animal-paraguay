"""Tests for RAP-600: Web push notifications."""

from __future__ import annotations

from pathlib import Path

FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"


class TestPushSubscriptionComponent:
    """Verify push notification subscription frontend component."""

    def test_component_exists(self) -> None:
        assert (FRONTEND_DIR / "src" / "components" / "PushNotificationSubscription.tsx").exists()

    def test_is_client_component(self) -> None:
        text = (
            FRONTEND_DIR / "src" / "components" / "PushNotificationSubscription.tsx"
        ).read_text()
        assert '"use client"' in text

    def test_checks_push_api_support(self) -> None:
        text = (
            FRONTEND_DIR / "src" / "components" / "PushNotificationSubscription.tsx"
        ).read_text()
        assert '"PushManager" in window' in text

    def test_checks_service_worker_support(self) -> None:
        text = (
            FRONTEND_DIR / "src" / "components" / "PushNotificationSubscription.tsx"
        ).read_text()
        assert '"serviceWorker" in navigator' in text

    def test_vapid_key_usage(self) -> None:
        text = (
            FRONTEND_DIR / "src" / "components" / "PushNotificationSubscription.tsx"
        ).read_text()
        assert "VAPID_PUBLIC_KEY" in text
        assert "urlBase64ToUint8Array" in text

    def test_subscribe_sends_to_server(self) -> None:
        text = (
            FRONTEND_DIR / "src" / "components" / "PushNotificationSubscription.tsx"
        ).read_text()
        assert "/api/push-subscriptions" in text
        assert '"POST"' in text

    def test_unsubscribe_notifies_server(self) -> None:
        text = (
            FRONTEND_DIR / "src" / "components" / "PushNotificationSubscription.tsx"
        ).read_text()
        assert '"DELETE"' in text

    def test_permission_states(self) -> None:
        text = (
            FRONTEND_DIR / "src" / "components" / "PushNotificationSubscription.tsx"
        ).read_text()
        assert '"default"' in text
        assert '"granted"' in text
        assert '"denied"' in text
        assert '"unsupported"' in text

    def test_spanish_labels(self) -> None:
        text = (
            FRONTEND_DIR / "src" / "components" / "PushNotificationSubscription.tsx"
        ).read_text()
        assert "Activar notificaciones" in text
        assert "Desactivar notificaciones" in text
        assert "Notificaciones bloqueadas" in text

    def test_graceful_degradation(self) -> None:
        """Component should return null when push is unsupported."""
        text = (
            FRONTEND_DIR / "src" / "components" / "PushNotificationSubscription.tsx"
        ).read_text()
        assert 'permission === "unsupported"' in text
        assert "return null" in text


class TestPushSubscriptionAPI:
    """Verify push subscription backend API."""

    def test_api_module_exists(self) -> None:
        api_path = Path(__file__).resolve().parents[2] / "src" / "api" / "push_subscriptions.py"
        assert api_path.exists()

    def test_api_has_create_endpoint(self) -> None:
        api_text = (
            Path(__file__).resolve().parents[2] / "src" / "api" / "push_subscriptions.py"
        ).read_text()
        assert "create_push_subscription" in api_text
        assert "HTTP_201_CREATED" in api_text

    def test_api_has_delete_endpoint(self) -> None:
        api_text = (
            Path(__file__).resolve().parents[2] / "src" / "api" / "push_subscriptions.py"
        ).read_text()
        assert "delete_push_subscription" in api_text
        assert "HTTP_204_NO_CONTENT" in api_text

    def test_api_has_list_endpoint(self) -> None:
        api_text = (
            Path(__file__).resolve().parents[2] / "src" / "api" / "push_subscriptions.py"
        ).read_text()
        assert "list_push_subscriptions" in api_text

    def test_api_requires_endpoint_url(self) -> None:
        api_text = (
            Path(__file__).resolve().parents[2] / "src" / "api" / "push_subscriptions.py"
        ).read_text()
        assert "endpoint: str" in api_text

    def test_api_requires_push_keys(self) -> None:
        api_text = (
            Path(__file__).resolve().parents[2] / "src" / "api" / "push_subscriptions.py"
        ).read_text()
        assert "p256dh" in api_text
        assert "auth" in api_text

    def test_api_registered_in_app(self) -> None:
        app_text = (Path(__file__).resolve().parents[2] / "src" / "app.py").read_text()
        assert "push_subscriptions_router" in app_text


class TestPushSubscriptionSchemas:
    """Verify push subscription Pydantic schemas."""

    def test_create_schema(self) -> None:
        from src.api.push_subscriptions import PushSubscriptionCreate

        sub = PushSubscriptionCreate(
            endpoint="https://fcm.googleapis.com/fcm/send/test",
            keys={"p256dh": "test-key", "auth": "test-auth"},
        )
        assert sub.endpoint == "https://fcm.googleapis.com/fcm/send/test"
        assert sub.keys.p256dh == "test-key"

    def test_delete_schema(self) -> None:
        from src.api.push_subscriptions import PushSubscriptionDelete

        sub = PushSubscriptionDelete(endpoint="https://fcm.googleapis.com/fcm/send/test")
        assert sub.endpoint == "https://fcm.googleapis.com/fcm/send/test"

    def test_response_schema(self) -> None:
        from src.api.push_subscriptions import PushSubscriptionResponse

        resp = PushSubscriptionResponse(
            id="test-id",
            endpoint="https://example.com",
            created_at="2026-01-01T00:00:00Z",
        )
        assert resp.id == "test-id"
