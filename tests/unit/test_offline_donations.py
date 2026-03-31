"""Unit tests for RAP-599: Offline donation forms with IndexedDB.

Tests cover:
- IndexedDB queue module (offlineDonationQueue.ts)
- Network status hook (useNetworkStatus.ts)
- OfflineDonationManager component
- Queued donations API endpoint
"""

from pathlib import Path

import pytest
from fastapi import status
from fastapi.testclient import TestClient

# Resolve project root reliably
PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIR = PROJECT_ROOT / "frontend"
SRC_DIR = PROJECT_ROOT / "src"


# ---------------------------------------------------------------------------
# IndexedDB Queue Module Tests
# ---------------------------------------------------------------------------


class TestOfflineDonationQueue:
    """Tests for frontend/src/lib/offlineDonationQueue.ts."""

    @pytest.fixture(autouse=True)
    def _load_source(self) -> None:
        self.source = (FRONTEND_DIR / "src" / "lib" / "offlineDonationQueue.ts").read_text()

    def test_file_exists(self) -> None:
        assert (FRONTEND_DIR / "src" / "lib" / "offlineDonationQueue.ts").exists()

    def test_db_name_is_refugio(self) -> None:
        assert 'DB_NAME = "refugio"' in self.source

    def test_store_name_is_queued_donations(self) -> None:
        assert 'STORE_NAME = "queuedDonations"' in self.source

    def test_max_queued_is_five(self) -> None:
        assert "MAX_QUEUED = 5" in self.source

    def test_max_retries_is_three(self) -> None:
        assert "MAX_RETRIES = 3" in self.source

    def test_backoff_base_ms(self) -> None:
        assert "BACKOFF_BASE_MS = 1000" in self.source

    def test_stale_days_cleanup(self) -> None:
        assert "STALE_DAYS = 7" in self.source

    def test_queue_schema_fields(self) -> None:
        for field in ["amount", "currency", "name", "email", "message", "timestamp", "retries"]:
            assert field in self.source

    def test_exports_add_to_queue(self) -> None:
        assert "export async function addToQueue" in self.source

    def test_exports_remove_from_queue(self) -> None:
        assert "export async function removeFromQueue" in self.source

    def test_exports_get_queued_donations(self) -> None:
        assert "export async function getQueuedDonations" in self.source

    def test_exports_process_queue(self) -> None:
        assert "export async function processQueue" in self.source

    def test_exports_clear_stale_entries(self) -> None:
        assert "export async function clearStaleEntries" in self.source

    def test_max_queue_full_message_spanish(self) -> None:
        assert "Maximo 5 donaciones en cola" in self.source

    def test_offline_saved_message_spanish(self) -> None:
        assert "Donacion guardada sin conexion" in self.source

    def test_exponential_backoff_formula(self) -> None:
        assert "Math.pow(2," in self.source

    def test_indexeddb_open_db(self) -> None:
        assert "indexedDB.open" in self.source

    def test_auto_increment_key(self) -> None:
        assert "autoIncrement: true" in self.source

    def test_update_retries_function(self) -> None:
        assert "export async function updateRetries" in self.source

    def test_get_queue_count(self) -> None:
        assert "export async function getQueueCount" in self.source


# ---------------------------------------------------------------------------
# Network Status Hook Tests
# ---------------------------------------------------------------------------


class TestNetworkStatusHook:
    """Tests for frontend/src/lib/useNetworkStatus.ts."""

    @pytest.fixture(autouse=True)
    def _load_source(self) -> None:
        self.source = (FRONTEND_DIR / "src" / "lib" / "useNetworkStatus.ts").read_text()

    def test_file_exists(self) -> None:
        assert (FRONTEND_DIR / "src" / "lib" / "useNetworkStatus.ts").exists()

    def test_is_client_component(self) -> None:
        assert '"use client"' in self.source

    def test_exports_use_network_status(self) -> None:
        assert "export function useNetworkStatus" in self.source

    def test_returns_is_online(self) -> None:
        assert "isOnline" in self.source

    def test_returns_was_offline(self) -> None:
        assert "wasOffline" in self.source

    def test_listens_online_event(self) -> None:
        assert '"online"' in self.source

    def test_listens_offline_event(self) -> None:
        assert '"offline"' in self.source

    def test_uses_navigator_online(self) -> None:
        assert "navigator.onLine" in self.source

    def test_cleans_up_listeners(self) -> None:
        assert "removeEventListener" in self.source


# ---------------------------------------------------------------------------
# OfflineDonationManager Component Tests
# ---------------------------------------------------------------------------


class TestOfflineDonationManager:
    """Tests for frontend/src/components/OfflineDonationManager.tsx."""

    @pytest.fixture(autouse=True)
    def _load_source(self) -> None:
        self.source = (
            FRONTEND_DIR / "src" / "components" / "OfflineDonationManager.tsx"
        ).read_text()

    def test_file_exists(self) -> None:
        assert (FRONTEND_DIR / "src" / "components" / "OfflineDonationManager.tsx").exists()

    def test_is_client_component(self) -> None:
        assert '"use client"' in self.source

    def test_imports_network_status_hook(self) -> None:
        assert "useNetworkStatus" in self.source

    def test_imports_queue_functions(self) -> None:
        assert "addToQueue" in self.source
        assert "getQueuedDonations" in self.source
        assert "removeFromQueue" in self.source
        assert "processQueue" in self.source

    def test_connection_toast_restored(self) -> None:
        assert "Conexion restaurada" in self.source

    def test_connection_toast_offline(self) -> None:
        assert "Sin conexion a internet" in self.source

    def test_pending_donations_count_label(self) -> None:
        assert "pendiente" in self.source

    def test_delete_button_exists(self) -> None:
        assert "Eliminar donacion" in self.source

    def test_retrying_message(self) -> None:
        assert "Reintentando" in self.source

    def test_success_message(self) -> None:
        assert "enviada" in self.source and "exitosamente" in self.source

    def test_uses_wifi_icons(self) -> None:
        assert "Wifi" in self.source
        assert "WifiOff" in self.source

    def test_renders_children_function(self) -> None:
        assert "children" in self.source
        assert "handleSubmit" in self.source

    def test_auto_process_on_reconnect(self) -> None:
        assert "processQueuedDonations" in self.source

    def test_feedback_banner_types(self) -> None:
        for feedback_type in ["success", "offline", "error", "retrying", "queue-full"]:
            assert feedback_type in self.source

    def test_wcag_touch_targets(self) -> None:
        assert "min-h-[44px]" in self.source
        assert "min-w-[44px]" in self.source

    def test_aria_live_regions(self) -> None:
        assert 'aria-live="polite"' in self.source
        assert 'aria-live="assertive"' in self.source

    def test_queue_list_role(self) -> None:
        assert 'role="list"' in self.source
        assert "Donaciones en cola" in self.source


# ---------------------------------------------------------------------------
# Queued Donations API Tests
# ---------------------------------------------------------------------------


class TestQueuedDonationsAPI:
    """Tests for src/api/queued_donations.py."""

    def test_module_exists(self) -> None:
        assert (SRC_DIR / "api" / "queued_donations.py").exists()

    def test_router_prefix(self) -> None:
        source = (SRC_DIR / "api" / "queued_donations.py").read_text()
        assert "/api/queued-donations" in source

    def test_submit_endpoint_exists(self) -> None:
        source = (SRC_DIR / "api" / "queued_donations.py").read_text()
        assert "submit_queued_donation" in source

    def test_schema_has_required_fields(self) -> None:
        source = (SRC_DIR / "api" / "queued_donations.py").read_text()
        for field in ["amount", "currency", "donor_name", "donor_email", "queued_at"]:
            assert field in source

    def test_currency_validation(self) -> None:
        source = (SRC_DIR / "api" / "queued_donations.py").read_text()
        assert "PYG" in source
        assert "EUR" in source
        assert "USD" in source

    def test_returns_201_created(self) -> None:
        source = (SRC_DIR / "api" / "queued_donations.py").read_text()
        assert "HTTP_201_CREATED" in source

    def test_response_schema(self) -> None:
        source = (SRC_DIR / "api" / "queued_donations.py").read_text()
        assert "QueuedDonationResponse" in source
        assert "success" in source
        assert "donation_id" in source
        assert "processed_at" in source

    def test_registered_in_app(self) -> None:
        app_source = (SRC_DIR / "app.py").read_text()
        assert "queued_donations_router" in app_source


# ---------------------------------------------------------------------------
# API Integration-style Tests (using TestClient)
# ---------------------------------------------------------------------------


class TestQueuedDonationsEndpoint:
    """Integration-style tests for the queued donations endpoint."""

    @pytest.fixture()
    def client(self) -> TestClient:
        from src.app import create_app

        app = create_app()
        return TestClient(app)

    def test_submit_valid_donation(self, client: TestClient) -> None:
        payload = {
            "amount": 50000,
            "currency": "PYG",
            "donor_name": "Test Donor",
            "donor_email": "test@example.com",
            "message": "For the animals",
            "queued_at": "2026-03-28T10:00:00.000Z",
        }
        response = client.post("/api/queued-donations", json=payload)
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["success"] is True
        assert "Donacion recibida" in data["message"]

    def test_submit_eur_donation(self, client: TestClient) -> None:
        payload = {
            "amount": 25.50,
            "currency": "EUR",
            "donor_name": "EU Donor",
            "donor_email": "eu@example.com",
            "message": "",
            "queued_at": "2026-03-28T10:00:00.000Z",
        }
        response = client.post("/api/queued-donations", json=payload)
        assert response.status_code == status.HTTP_201_CREATED

    def test_reject_invalid_currency(self, client: TestClient) -> None:
        payload = {
            "amount": 100,
            "currency": "GBP",
            "donor_name": "Test",
            "donor_email": "test@example.com",
            "message": "",
            "queued_at": "2026-03-28T10:00:00.000Z",
        }
        response = client.post("/api/queued-donations", json=payload)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_reject_zero_amount(self, client: TestClient) -> None:
        payload = {
            "amount": 0,
            "currency": "PYG",
            "donor_name": "Test",
            "donor_email": "test@example.com",
            "message": "",
            "queued_at": "2026-03-28T10:00:00.000Z",
        }
        response = client.post("/api/queued-donations", json=payload)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_reject_negative_amount(self, client: TestClient) -> None:
        payload = {
            "amount": -10,
            "currency": "PYG",
            "donor_name": "Test",
            "donor_email": "test@example.com",
            "message": "",
            "queued_at": "2026-03-28T10:00:00.000Z",
        }
        response = client.post("/api/queued-donations", json=payload)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_reject_invalid_email(self, client: TestClient) -> None:
        payload = {
            "amount": 100,
            "currency": "PYG",
            "donor_name": "Test",
            "donor_email": "not-an-email",
            "message": "",
            "queued_at": "2026-03-28T10:00:00.000Z",
        }
        response = client.post("/api/queued-donations", json=payload)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
