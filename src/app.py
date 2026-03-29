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
from src.api.admin_fund_dashboard import router as admin_fund_dashboard_router
from src.api.admin_moderation import router as admin_moderation_router
from src.api.admin_sse import router as admin_sse_router
from src.api.admin_voucher_finance import router as admin_voucher_finance_router
from src.api.adopters import router as adopters_router
from src.api.adoption_requests import router as adoption_requests_router
from src.api.adoption_requirements import (
    admin_router as adoption_req_admin_router,
)
from src.api.adoption_requirements import (
    public_router as adoption_req_public_router,
)
from src.api.adoption_success import router as adoption_success_router
from src.api.anbi_compliance import router as anbi_compliance_router
from src.api.animal_intake_outcome import router as animal_intake_outcome_router
from src.api.animal_updates import router as animal_updates_router
from src.api.animals import router as animals_router
from src.api.annual_reports import router as annual_reports_router
from src.api.appointments import router as appointments_router
from src.api.article_editor import admin_router as article_editor_admin_router
from src.api.article_editor import public_router as article_editor_public_router
from src.api.auth import router as auth_router
from src.api.batch_receipts import router as batch_receipts_router
from src.api.blog_posts import admin_router as blog_admin_router
from src.api.blog_posts import public_router as blog_public_router
from src.api.campaign_finance import router as campaign_finance_router
from src.api.campaign_voucher_integration import router as campaign_voucher_integration_router
from src.api.castration_drives import admin_router as castration_drives_admin_router
from src.api.castration_drives import public_router as castration_drives_public_router
from src.api.castration_photos import admin_router as castration_photos_admin_router
from src.api.castration_photos import public_router as castration_photos_public_router
from src.api.castration_report import admin_router as castration_report_admin_router
from src.api.castration_report import public_router as castration_report_public_router
from src.api.clinic_redemption import router as clinic_redemption_router
from src.api.clinic_services import router as clinic_services_router
from src.api.cms import public_router as cms_public_router
from src.api.cms import router as cms_router
from src.api.community_engagement_analytics import router as community_engagement_analytics_router
from src.api.community_feed import router as community_feed_router
from src.api.community_needs import (
    public_router as community_needs_public_router,
)
from src.api.community_needs import (
    rescuer_router as community_needs_rescuer_router,
)
from src.api.consents import router as consents_router
from src.api.diagnoses import diagnosis_router, treatment_router
from src.api.donation_allocations import allocation_router, expense_router
from src.api.donation_analytics import router as donation_analytics_router
from src.api.donations import router as donations_router
from src.api.donor_impact import router as donor_impact_router
from src.api.donor_leaderboard import router as donor_leaderboard_router
from src.api.donor_retention_analytics import router as donor_retention_analytics_router
from src.api.donor_tax_id import router as donor_tax_id_router
from src.api.donors import router as donors_router
from src.api.driver_reimbursement import router as driver_reimbursement_router
from src.api.educational_article import admin_router as article_admin_router
from src.api.educational_article import public_router as article_public_router
from src.api.email_verification import router as email_verification_router
from src.api.emergencies import router as emergencies_router
from src.api.emergency_donations import router as emergency_donations_router
from src.api.executive_kpi_dashboard import router as executive_kpi_dashboard_router
from src.api.expense_approval import router as expense_approval_router
from src.api.expense_crud import router as expense_crud_router
from src.api.feature_requests import router as feature_requests_router
from src.api.financial_stats import router as financial_stats_router
from src.api.follow_ups import router as follow_ups_router
from src.api.followup_automation import admin_router as followup_auto_admin_router
from src.api.followup_automation import public_router as followup_auto_public_router
from src.api.foster import public_router as foster_public_router
from src.api.foster import staff_router as foster_staff_router
from src.api.fund_allocations import router as fund_allocations_router
from src.api.gdpr import router as gdpr_router
from src.api.gdpr_export import router as gdpr_export_router
from src.api.google_oauth import router as google_oauth_router
from src.api.health import router as health_router
from src.api.home_visits import admin_router as home_visits_admin_router
from src.api.home_visits import public_router as home_visits_public_router
from src.api.homepage_content import router as homepage_content_router
from src.api.impact_emails import router as impact_emails_router
from src.api.impact_reports import router as impact_reports_router
from src.api.in_kind_donations import router as in_kind_donations_router
from src.api.media_serve import router as media_serve_router
from src.api.media_upload import router as media_upload_router
from src.api.medical_documents import router as medical_documents_router
from src.api.medications import router as medications_router
from src.api.notification_preferences import router as notification_preferences_router
from src.api.notifications import router as notifications_router
from src.api.og_image import router as og_image_router
from src.api.password_reset import router as password_reset_router
from src.api.phone_verification import router as phone_verification_router
from src.api.pipeline_tracking import router as pipeline_tracking_router
from src.api.portal import router as portal_router
from src.api.pre_adoption_reading import router as pre_adoption_reading_router
from src.api.pre_qualification import router as pre_qualification_router
from src.api.pre_qualification_analytics import router as pre_qual_analytics_router
from src.api.predictive_analytics import router as predictive_analytics_router
from src.api.prescriptions import router as prescriptions_router
from src.api.profile import router as profile_router
from src.api.public import router as public_router
from src.api.public_adoption import router as public_adoption_router
from src.api.public_campaigns import router as public_campaigns_router
from src.api.public_castration_campaigns import router as public_castration_campaigns_router
from src.api.public_clinic_fund import router as public_clinic_fund_router
from src.api.public_contact import router as public_contact_router
from src.api.public_emergencies import router as public_emergencies_router
from src.api.public_impact import router as public_impact_router
from src.api.public_register import router as public_register_router
from src.api.public_rescuer_support import router as public_rescuer_support_router
from src.api.public_sponsorships import router as public_sponsorships_router
from src.api.public_statistics import router as public_statistics_router
from src.api.public_survey import router as public_survey_router
from src.api.public_voucher_stats import router as public_voucher_stats_router
from src.api.push_subscriptions import router as push_subscriptions_router
from src.api.queued_donations import router as queued_donations_router
from src.api.referral_tracking import admin_router as referral_tracking_admin_router
from src.api.referral_tracking import public_router as referral_tracking_public_router
from src.api.report_export import router as report_export_router
from src.api.request_matching import router as request_matching_router
from src.api.rescuer_animals import (
    portal_router as rescuer_animals_portal_router,
)
from src.api.rescuer_animals import (
    public_router as rescuer_animals_public_router,
)
from src.api.rescuer_campaigns import portal_router as rescuer_campaigns_portal_router
from src.api.rescuer_campaigns import public_router as rescuer_campaigns_public_router
from src.api.rescuer_directory import router as rescuer_directory_router
from src.api.rescuer_emergencies import router as rescuer_emergencies_router
from src.api.rescuer_profile import router as rescuer_profile_router
from src.api.rescuer_profiles import router as rescuer_profiles_router
from src.api.rescuer_verification import router as rescuer_verification_router
from src.api.rescuer_voucher_integration import router as rescuer_voucher_integration_router
from src.api.rescuer_vouchers import router as rescuer_vouchers_router
from src.api.sepa import router as sepa_router
from src.api.sessions import router as sessions_router
from src.api.share_tracking import admin_router as share_admin_router
from src.api.share_tracking import public_router as share_public_router
from src.api.shift_reminders import router as shift_reminders_router
from src.api.shifts import public_router as shifts_public_router
from src.api.shifts import staff_router as shifts_staff_router
from src.api.smart_matching import router as smart_matching_router
from src.api.sponsorships import router as sponsorships_router
from src.api.subscriptions import router as subscriptions_router
from src.api.success_stories import admin_router as stories_admin_router
from src.api.success_stories import public_router as stories_public_router
from src.api.surgeries import surgery_router
from src.api.survey_admin import router as survey_admin_router
from src.api.survey_analytics import router as survey_analytics_router
from src.api.survey_distribution import router as survey_distribution_router
from src.api.tasks import public_router as tasks_public_router
from src.api.tasks import staff_router as tasks_staff_router
from src.api.tigo_money import router as tigo_money_router
from src.api.transport import router as transport_router
from src.api.transport_request import router as transport_request_router
from src.api.trial_periods import admin_router as trial_admin_router
from src.api.trial_periods import public_router as trial_public_router
from src.api.trip_tracking import router as trip_tracking_router
from src.api.user_roles import router as user_roles_router
from src.api.vaccinations import vaccination_router, vaccine_type_router
from src.api.vet_analytics import router as vet_analytics_router
from src.api.vet_clinics import router as vet_clinics_router
from src.api.vet_documents import router as vet_documents_router
from src.api.vet_referrals import referral_router
from src.api.vet_transport import router as vet_transport_router
from src.api.vet_visits import router as vet_visits_router
from src.api.vet_vouchers import router as vet_vouchers_router
from src.api.volunteer import public_router as volunteer_public_router
from src.api.volunteer import staff_router as volunteer_staff_router
from src.api.volunteer_certificates import router as volunteer_certificates_router
from src.api.volunteer_driver import router as volunteer_driver_router
from src.api.volunteer_impact import router as volunteer_impact_router
from src.api.volunteer_hours import public_router as volunteer_hours_public_router
from src.api.volunteer_hours import staff_router as volunteer_hours_staff_router
from src.api.voucher_expiry import router as voucher_expiry_router
from src.api.voucher_notifications import router as voucher_notifications_router
from src.api.voucher_purchase import router as voucher_purchase_router
from src.api.webhooks import router as webhooks_router
from src.api.whatsapp_templates import router as whatsapp_templates_router
from src.api.whatsapp_webhook import router as whatsapp_webhook_router
from src.audit.middleware import AuditMiddleware
from src.config import Settings, get_settings
from src.db.session import dispose_engine, init_engine
from src.events.bus import EventBus
from src.logging_config import configure_logging
from src.middleware.error_handler import register_exception_handlers
from src.middleware.logging_middleware import RequestLoggingMiddleware
from src.middleware.rate_limiter import configure_limiter, limiter
from src.middleware.request_id import RequestIDMiddleware
from src.notifications.activity_sse_handlers import ActivitySSEHandlers
from src.notifications.donation_sse_handlers import DonationSSEHandlers
from src.notifications.handlers import NotificationHandlers
from src.notifications.in_app_handlers import InAppNotificationHandlers
from src.notifications.service import EmailService
from src.notifications.templates import TemplateRenderer
from src.notifications.meta_whatsapp_adoption_handler import MetaWhatsAppAdoptionHandler
from src.notifications.meta_whatsapp_service import MetaWhatsAppService
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

    # Register WhatsApp notification handlers on the event bus (Twilio — volunteer shifts)
    whatsapp_service = WhatsAppService(settings)
    whatsapp_handlers = WhatsAppHandlers(whatsapp_service)
    whatsapp_handlers.register(event_bus)

    # Register Meta Cloud WhatsApp adoption notification handler (RAP-202)
    meta_whatsapp_service = MetaWhatsAppService(settings)
    meta_whatsapp_adoption_handler = MetaWhatsAppAdoptionHandler(meta_whatsapp_service)
    meta_whatsapp_adoption_handler.register(event_bus)

    # Register SSE handlers for real-time admin dashboard notifications
    donation_sse_handlers = DonationSSEHandlers(sse_manager)
    donation_sse_handlers.register(event_bus)

    # Register activity feed SSE handlers (broadcasts all events to admin feed)
    activity_sse_handlers = ActivitySSEHandlers(sse_manager)
    activity_sse_handlers.register(event_bus)

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
    application.include_router(blog_admin_router)
    application.include_router(blog_public_router)
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
    application.include_router(public_castration_campaigns_router)
    application.include_router(public_contact_router)
    application.include_router(public_register_router)
    application.include_router(portal_router)
    application.include_router(sepa_router)
    application.include_router(subscriptions_router)
    application.include_router(tigo_money_router)
    application.include_router(webhooks_router)
    application.include_router(push_subscriptions_router)
    application.include_router(admin_campaigns_router)
    application.include_router(admin_fund_dashboard_router)
    application.include_router(admin_castration_campaigns_router)
    application.include_router(admin_voucher_finance_router)
    application.include_router(donor_tax_id_router)
    application.include_router(batch_receipts_router)
    application.include_router(campaign_finance_router)
    application.include_router(campaign_voucher_integration_router)
    application.include_router(consents_router)
    application.include_router(notifications_router)
    application.include_router(gdpr_export_router)
    application.include_router(notification_preferences_router)
    application.include_router(financial_stats_router)
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
    application.include_router(voucher_purchase_router)
    application.include_router(voucher_notifications_router)
    application.include_router(rescuer_verification_router)
    application.include_router(rescuer_voucher_integration_router)
    application.include_router(user_roles_router)
    application.include_router(pre_qualification_router)
    application.include_router(smart_matching_router)
    application.include_router(public_statistics_router)
    application.include_router(public_survey_router)
    application.include_router(public_clinic_fund_router)
    application.include_router(public_rescuer_support_router)
    application.include_router(public_sponsorships_router)
    application.include_router(public_impact_router)
    application.include_router(public_voucher_stats_router)
    application.include_router(queued_donations_router)
    application.include_router(media_upload_router)
    application.include_router(expense_router)
    application.include_router(expense_approval_router)
    application.include_router(annual_reports_router)
    application.include_router(anbi_compliance_router)
    application.include_router(allocation_router)
    application.include_router(expense_crud_router)
    application.include_router(pre_qual_analytics_router)
    application.include_router(vet_documents_router)
    application.include_router(media_serve_router)
    application.include_router(cms_router)
    application.include_router(cms_public_router)
    application.include_router(share_public_router)
    application.include_router(share_admin_router)

    application.include_router(og_image_router)
    application.include_router(referral_tracking_public_router)
    application.include_router(referral_tracking_admin_router)
    application.include_router(emergencies_router)
    application.include_router(emergency_donations_router)
    application.include_router(feature_requests_router)
    application.include_router(pipeline_tracking_router)
    application.include_router(transport_router)
    application.include_router(followup_auto_admin_router)
    application.include_router(followup_auto_public_router)
    application.include_router(adoption_success_router)
    application.include_router(transport_router)

    application.include_router(stories_admin_router)
    application.include_router(stories_public_router)
    application.include_router(survey_analytics_router)
    application.include_router(survey_admin_router)
    application.include_router(survey_distribution_router)
    application.include_router(impact_emails_router)
    application.include_router(vet_transport_router)
    application.include_router(driver_reimbursement_router)
    application.include_router(article_admin_router)
    application.include_router(article_public_router)
    application.include_router(castration_drives_admin_router)
    application.include_router(castration_drives_public_router)
    application.include_router(castration_photos_admin_router)
    application.include_router(castration_photos_public_router)
    application.include_router(donor_impact_router)
    application.include_router(donor_leaderboard_router)
    application.include_router(castration_report_admin_router)
    application.include_router(castration_report_public_router)
    application.include_router(community_needs_public_router)
    application.include_router(community_feed_router)
    application.include_router(homepage_content_router)
    application.include_router(rescuer_campaigns_portal_router)
    application.include_router(rescuer_campaigns_public_router)
    application.include_router(rescuer_emergencies_router)
    application.include_router(public_emergencies_router)
    application.include_router(trial_admin_router)
    application.include_router(trial_public_router)
    application.include_router(home_visits_admin_router)
    application.include_router(home_visits_public_router)
    application.include_router(pre_adoption_reading_router)
    application.include_router(article_editor_admin_router)
    application.include_router(article_editor_public_router)
    application.include_router(trip_tracking_router)
    application.include_router(vet_analytics_router)
    application.include_router(report_export_router)
    application.include_router(donation_analytics_router)
    application.include_router(donor_retention_analytics_router)
    application.include_router(transport_request_router)
    application.include_router(predictive_analytics_router)
    application.include_router(request_matching_router)
    application.include_router(animal_intake_outcome_router)
    application.include_router(executive_kpi_dashboard_router)
    application.include_router(community_needs_public_router)
    application.include_router(community_needs_rescuer_router)
    application.include_router(rescuer_directory_router)
    application.include_router(admin_moderation_router)
    application.include_router(rescuer_profile_router)
    application.include_router(rescuer_animals_portal_router)
    application.include_router(rescuer_animals_public_router)

    application.include_router(community_engagement_analytics_router)
    application.include_router(shifts_public_router)
    application.include_router(shifts_staff_router)
    application.include_router(shift_reminders_router)
    application.include_router(foster_public_router)
    application.include_router(foster_staff_router)
    application.include_router(tasks_public_router)
    application.include_router(tasks_staff_router)
    application.include_router(volunteer_public_router)
    application.include_router(volunteer_staff_router)
    application.include_router(volunteer_certificates_router)
    application.include_router(volunteer_driver_router)
    application.include_router(volunteer_impact_router)
    application.include_router(volunteer_hours_public_router)
    application.include_router(volunteer_hours_staff_router)
    application.include_router(whatsapp_templates_router)
    application.include_router(whatsapp_webhook_router)  # RAP-204: two-way WhatsApp
    return application


# Module-level app instance — used by uvicorn and test client
app = create_app()
