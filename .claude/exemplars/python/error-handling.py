"""
Exemplar: Python Error Handling Patterns

Shows correct (✅) and incorrect (❌) patterns.
This file is for AI calibration — not production code.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


# =============================================================================
# EXCEPTION HIERARCHY
# =============================================================================


class AppError(Exception):
    """Base exception for all application errors."""

    pass


class ValidationError(AppError):
    """Input failed validation rules."""

    pass


class NotFoundError(AppError):
    """Requested resource does not exist."""

    pass


class ExternalServiceError(AppError):
    """Third-party service call failed."""

    pass


# =============================================================================
# ❌ ANTI-PATTERNS — Never do these
# =============================================================================


def bad_silent_swallow(email: str) -> None:
    """❌ WRONG: Silently swallows all exceptions."""
    try:
        send_confirmation_email(email)
    except Exception:
        pass  # BUG: Error disappears. No log. No retry. No alerting.


def bad_comment_only(email: str) -> None:
    """❌ WRONG: Comment explains intent but exception still swallowed."""
    try:
        send_confirmation_email(email)
    except Exception:  # noqa: BLE001 — intentionally bad pattern for exemplar
        # Don't fail if email doesn't send
        pass  # BUG: Still silent. The comment is a lie.


def bad_bare_except() -> None:
    """❌ WRONG: Catches KeyboardInterrupt and SystemExit."""
    try:
        process_donations()
    except:  # noqa: E722 — intentionally bad for exemplar
        handle_error()  # BUG: Catches everything, including Ctrl+C


def bad_generic_message(donor_id: int) -> None:
    """❌ WRONG: Generic error message with no actionable info."""
    try:
        get_donor(donor_id)
    except Exception as e:
        raise ValueError("An error occurred") from e  # BUG: Useless


# =============================================================================
# ✅ CORRECT PATTERNS
# =============================================================================


def good_specific_catch_log_continue(email: str) -> None:
    """
    ✅ CORRECT: Specific exception, logged with context, continues gracefully.

    Use when: notification failure is non-critical and should not block the user.
    """
    try:
        send_confirmation_email(email)
    except EmailDeliveryError as e:
        # Log with enough context to diagnose without re-running
        logger.warning(
            "Adoption confirmation email failed — adopter will not be notified automatically",
            extra={"email": email, "error": str(e), "error_type": type(e).__name__},
        )
        # Caller doesn't need to know — this is a background notification


def good_critical_reraise(donor_id: int, amount_eur: float) -> dict:
    """
    ✅ CORRECT: Critical operation re-raises after logging.

    Use when: failure must propagate to the caller (payment, data integrity).
    """
    try:
        result = process_payment(donor_id, amount_eur)
        return result
    except PaymentGatewayError as e:
        logger.error(
            "Donation payment failed — donor will not be charged",
            extra={"donor_id": donor_id, "amount_eur": amount_eur, "error": str(e)},
        )
        raise  # Re-raise original exception with full traceback


def good_structured_error_return(animal_id: int) -> Optional[dict]:
    """
    ✅ CORRECT: Returns None for expected not-found case.

    Use when: absence is a valid state (not an error).
    """
    try:
        return get_animal(animal_id)
    except NotFoundError:
        return None  # Caller handles None — this is expected


def good_convert_and_raise(animal_id: int, new_status: str) -> None:
    """
    ✅ CORRECT: Converts low-level exception to domain exception.

    Use when: hiding infrastructure details from the domain layer.
    """
    try:
        db_update_animal_status(animal_id, new_status)
    except DatabaseConnectionError as e:
        # Wrap in domain exception — caller doesn't need to know about DB
        raise ExternalServiceError(
            f"Could not update status for animal {animal_id}: database unavailable"
        ) from e  # 'from e' preserves original traceback


def good_multiple_specific_exceptions(donor_id: int) -> dict:
    """
    ✅ CORRECT: Different handling for different exception types.

    Use when: different failures require different responses.
    """
    try:
        return fetch_donor_from_eu_api(donor_id)
    except NotFoundError:
        raise  # Let caller handle missing donor
    except RateLimitError as e:
        logger.warning("EU API rate limit hit", extra={"donor_id": donor_id})
        raise ExternalServiceError("EU donor API temporarily unavailable") from e
    except ExternalServiceError:
        raise  # Already the right type
    except Exception as e:
        # Unexpected — log full exception for investigation
        logger.exception(
            "Unexpected error fetching EU donor", extra={"donor_id": donor_id}
        )
        raise ExternalServiceError(f"Unexpected error for donor {donor_id}") from e


# =============================================================================
# Stub functions (for exemplar completeness — not real implementations)
# =============================================================================
class EmailDeliveryError(Exception):
    pass


class PaymentGatewayError(Exception):
    pass


class DatabaseConnectionError(Exception):
    pass


class RateLimitError(Exception):
    pass


def send_confirmation_email(email: str) -> None:
    """Stub — not a real implementation."""
    _ = email


def process_donations() -> None:
    """Stub."""


def handle_error() -> None:
    """Stub."""


def get_donor(donor_id: int) -> dict:
    """Stub."""
    return {"id": donor_id}


def process_payment(donor_id: int, amount_eur: float) -> dict:
    """Stub."""
    return {"donor_id": donor_id, "amount": amount_eur}


def get_animal(animal_id: int) -> dict:
    """Stub."""
    return {"id": animal_id}


def db_update_animal_status(animal_id: int, status: str) -> None:
    """Stub."""
    _ = animal_id, status


def fetch_donor_from_eu_api(donor_id: int) -> dict:
    """Stub."""
    return {"id": donor_id}
