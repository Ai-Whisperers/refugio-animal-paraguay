"""FastAPI application factory and lifespan.

Entry point for the Refugio Animal Paraguay API. Creates the FastAPI app,
registers routers, configures CORS/rate limiting/error handling, and manages
the database engine lifecycle via lifespan.

Run locally:
    uvicorn src.app:app --reload
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from src.api.admin import router as admin_router
from src.api.admin_campaigns import router as admin_campaigns_router
from src.api.admin_castration_campaigns import router as admin_castration_campaigns_router
from src.api.admin_sse import router as admin_sse_router
from src.api.adopters import router as adopters_router
from src.api.adoption_requests import router as adoption_requests_router
from src.api.adoption_requirements import (
    admin_router as adoption_req_admin_router,
)
from src.api.adoption_requirements import (
    public_router as adoption_req_public_router,
)
from src.api.animal_updates import router as animal_updates_router
from src.api.animals import router as animals_router
from src.api.appointments import router as appointments_router
from src.api.auth import router as auth_router
from src.api.campaign_voucher_integration import router as campaign_voucher_integration_router
from src.api.clinic_redemption import router as clinic_redemption_router
from src.api.clinic_services import router as clinic_services_router
from src.api.consents import router as consents_router
from src.api.diagnoses import diagnosis_router, treatment_router
from src.api.donation_allocations import allocation_router, expense_router
from src.api.donations import router as donations_router
from src.api.donors import router as donors_router
from src.api.email_verification import router as email_verification_router
from src.api.follow_ups import router as follow_ups_router
from src.api.fund_allocations import router as fund_allocations_router
from src.api.gdpr import router as gdpr_router
from src.api.gdpr_export import router as gdpr_export_router
from src.api.google_oauth import router as google_oauth_router
from src.api.health import router as health_router
from src.api.impact_reports import router as impact_reports_router
from src.api.in_kind_donations import router as in_kind_donations_router
from src.api.media_upload import router as media_upload_router
from src.api.medical_documents import router as medical_documents_router
from src.api.medications import router as medications_router
from src.api.notification_preferences import router as notification_preferences_router
from src.api.notifications import router as notifications_router
from src.api.password_reset import router as password_reset_router
from src.api.phone_verification import router as phone_verification_router
from src.api.portal import router as portal_router
from src.api.pre_qualification import router as pre_qualification_router
from src.api.pre_qualification_analytics import router as pre_qual_analytics_router
from src.api.prescriptions import router as prescriptions_router
from src.api.profile import router as profile_router
from src.api.public import router as public_router
from src.api.public_adoption import router as public_adoption_router
from src.api.public_campaigns import router as public_campaigns_router
from src.api.public_contact import router as public_contact_router
from src.api.public_register import router as public_register_router
from src.api.public_statistics import router as public_statistics_router
from src.api.rescuer_profiles import router as rescuer_profiles_router
from src.api.rescuer_vouchers import router as rescuer_vouchers_router
from src.api.sepa import router as sepa_router
from src.api.sessions import router as sessions_router
from src.api.smart_matching import router as smart_matching_router
from src.api.sponsorships import router as sponsorships_router
from src.api.subscriptions import router as subscriptions_router
from src.api.surgeries import surgery_router
from src.api.tigo_money import router as tigo_money_router
from src.api.user_roles import router as user_roles_router
from src.api.vaccinations import vaccination_router, vaccine_type_router
from src.api.vet_clinics import router as vet_clinics_router
from src.api.vet_referrals import referral_router
from src.api.vet_visits import router as vet_visits_router
from src.api.vet_vouchers import router as vet_vouchers_router
from src.api.voucher_expiry import router as voucher_expiry_router
from src.api.webhooks import router as webhooks_router
from src.audit.middleware import AuditMiddleware
from src.config import Settings, get_settings
from src.db.session import dispose_engine, init_engine
from src.events.bus import EventBus
from src.logging_config import configure_logging
from src.middleware.error_handler import register_exception_handlers
from src.middleware.logging_middleware import RequestLoggingMiddleware
from src.middleware.rate_limiter import configure_limiter, limiter
from src.middleware.request_id import RequestIDMiddleware
from src.notifications.donation_sse_handlers import DonationSSEHandlers
from src.notifications.handlers import NotificationHandlers
from src.notifications.in_app_handlers import InAppNotificationHandlers
from src.notifications.service import EmailService
from src.notifications.templates import TemplateRenderer
from src.notifications.whatsapp_handlers import WhatsAppHandlers
from src.notifications.whatsapp_service import WhatsAppService
from src.sentry_config import configure_sentry
from src.services.dunning_service import DunningService
from src.services.sepa_notification_service import SepaNotificationService
from src.services.sse_service import sse_manager


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application lifecycle: DB engine + event bus on startup/shutdown."""
    settings: Settings = get_settings()
    init_engine(settings)

    # Start the event bus and attach to app state for handler access
    event_bus = EventBus()
    application.state.event_bus = event_bus
    await event_bus.start()

    # Register email notification handlers on the event bus
    email_service = EmailService(settings)
    renderer = TemplateRenderer()
    notification_handlers = NotificationHandlers(email_service, renderer)
    notification_handlers.register(event_bus)

    # Register in-app notification handlers on the event bus
    in_app_handlers = InAppNotificationHandlers()
    in_app_handlers.register(event_bus)

    # Register WhatsApp notification handlers on the event bus
    whatsapp_service = WhatsAppService(settings)
    whatsapp_handlers = WhatsAppHandlers(whatsapp_service)
    whatsapp_handlers.register(event_bus)

    # Register SSE handlers for real-time admin dashboard notifications
    donation_sse_handlers = DonationSSEHandlers(sse_manager)
    donation_sse_handlers.register(event_bus)

    # Attach SEPA notification service for webhook handlers
    application.state.sepa_notifier = SepaNotificationService(email_service, renderer)

    # Attach dunning service for recurring payment failure notifications
    application.state.dunning_service = DunningService(email_service, renderer)

    yield

    await event_bus.stop()
    await dispose_engine()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    # Configure structured logging before any logger is used.
    configure_logging(is_dev=settings.app_env == "development")

    # Initialise Sentry before the first request is processed.
    # No-op when sentry_dsn is empty (development default).
    configure_sentry(
        dsn=settings.sentry_dsn,
        environment=settings.app_env,
        traces_sample_rate=settings.sentry_traces_sample_rate,
    )

    application = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        debug=settings.debug,
        lifespan=lifespan,
    )

    # --- Request ID middleware (must be outermost to cover all responses) ---
    application.add_middleware(RequestIDMiddleware)

    # --- Request/response logging (after RequestID so request_id is available) ---
    application.add_middleware(RequestLoggingMiddleware)

    # --- Audit trail middleware (after auth, records successful write ops) ---
    application.add_middleware(AuditMiddleware)

    # --- CORS middleware ---
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- Rate limiting ---
    configure_limiter(enabled=settings.rate_limit_enabled)
    application.state.limiter = limiter
    application.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # --- Exception handlers (overrides default FastAPI handlers) ---
    register_exception_handlers(application)

    # --- Routers ---
    application.include_router(health_router)
    application.include_router(auth_router)
    application.include_router(google_oauth_router)
    application.include_router(password_reset_router)
    application.include_router(email_verification_router)
    application.include_router(phone_verification_router)
    application.include_router(sessions_router)
    application.include_router(animals_router)
    application.include_router(adopters_router)
    application.include_router(adoption_requests_router)
    application.include_router(donors_router)
    application.include_router(donations_router)
    application.include_router(in_kind_donations_router)
    application.include_router(fund_allocations_router)
    application.include_router(admin_router)
    application.include_router(admin_sse_router)
    application.include_router(adoption_req_admin_router)
    application.include_router(adoption_req_public_router)
    application.include_router(public_router)
    application.include_router(public_adoption_router)
    application.include_router(public_campaigns_router)
    application.include_router(public_contact_router)
    application.include_router(public_register_router)
    application.include_router(portal_router)
    application.include_router(sepa_router)
    application.include_router(subscriptions_router)
    application.include_router(tigo_money_router)
    application.include_router(webhooks_router)
    application.include_router(admin_campaigns_router)
    application.include_router(admin_castration_campaigns_router)
    application.include_router(campaign_voucher_integration_router)
    application.include_router(consents_router)
    application.include_router(notifications_router)
    application.include_router(gdpr_export_router)
    application.include_router(notification_preferences_router)
    application.include_router(follow_ups_router)
    application.include_router(gdpr_router)
    application.include_router(impact_reports_router)
    application.include_router(sponsorships_router)
    application.include_router(animal_updates_router)
    application.include_router(vaccine_type_router)
    application.include_router(vaccination_router)
    application.include_router(surgery_router)
    application.include_router(vet_visits_router)
    application.include_router(diagnosis_router)
    application.include_router(treatment_router)
    application.include_router(medications_router)
    application.include_router(medical_documents_router)
    application.include_router(referral_router)
    application.include_router(appointments_router)
    application.include_router(prescriptions_router)
    application.include_router(profile_router)
    application.include_router(vet_clinics_router)
    application.include_router(clinic_services_router)
    application.include_router(vet_vouchers_router)
    application.include_router(rescuer_vouchers_router)
    application.include_router(rescuer_profiles_router)
    application.include_router(clinic_services_router)
    application.include_router(voucher_expiry_router)
    application.include_router(vet_vouchers_router)
    application.include_router(clinic_redemption_router)
    application.include_router(user_roles_router)
    application.include_router(pre_qualification_router)
    application.include_router(smart_matching_router)
    application.include_router(public_statistics_router)
    application.include_router(media_upload_router)
    application.include_router(expense_router)
    application.include_router(allocation_router)
    application.include_router(pre_qual_analytics_router)

    return application


# Module-level app instance — used by uvicorn and test client
app = create_app()
