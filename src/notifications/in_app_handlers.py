"""Event bus handlers that create in-app notifications.

Subscribes to domain events and creates persistent Notification records
for relevant staff/admin users. Complements the email notification handlers
by providing in-app awareness of shelter events.

Only creates notifications for users who have the in_app channel enabled for
the given notification type (opt-out model — missing preference rows default
to enabled).

Registration:
    Called from app lifespan via InAppNotificationHandlers.register(event_bus).
"""

import logging
from uuid import UUID

from sqlalchemy import select

from src.db.models.notification import NotificationType
from src.db.models.notification_preference import NotificationChannel
from src.db.models.user import User, UserRole
from src.db.session import get_async_session
from src.events.bus import EventBus
from src.events.types import DomainEvent, EventType
from src.services.notification_preference_service import is_notification_enabled
from src.services.notification_service import create_notification

logger = logging.getLogger(__name__)


class InAppNotificationHandlers:
    """Event handlers that create in-app notifications for staff users.

    Before creating each notification the handler checks whether the target
    user has opted out of the in_app channel for that notification type.
    Missing preference rows are treated as enabled (opt-out model).
    """

    def register(self, bus: EventBus) -> None:
        """Subscribe all in-app notification handlers to the event bus."""
        bus.subscribe(EventType.ADOPTION_REQUEST_CREATED, self.on_adoption_request_created)
        bus.subscribe(EventType.ADOPTION_STATUS_CHANGED, self.on_adoption_status_changed)
        bus.subscribe(EventType.DONATION_RECEIVED, self.on_donation_received)
        bus.subscribe(EventType.ANIMAL_INTAKE_COMPLETED, self.on_animal_intake_completed)
        logger.info("In-app notification handlers registered on event bus")

    async def on_adoption_request_created(self, event: DomainEvent) -> None:
        """Notify staff (who have in_app enabled) when a new adoption request is submitted."""
        try:
            payload = event.payload
            adopter_name = payload.get("adopter_name", "Unknown adopter")
            animal_name = payload.get("animal_name", "an animal")

            await self._notify_all_staff(
                notification_type=NotificationType.ADOPTION_REQUEST_CREATED,
                title="New Adoption Request",
                message=f"{adopter_name} submitted an adoption request for {animal_name}.",
                data={
                    "aggregate_id": str(event.aggregate_id) if event.aggregate_id else None,
                    "adopter_name": adopter_name,
                    "animal_name": animal_name,
                },
            )
        except Exception as exc:
            logger.exception(
                "Failed to create in-app notification for adoption_request_created event_id=%s: %s",
                event.id,
                exc,
            )

    async def on_adoption_status_changed(self, event: DomainEvent) -> None:
        """Notify staff (who have in_app enabled) when an adoption request status changes."""
        try:
            payload = event.payload
            old_status = payload.get("old_status", "unknown")
            new_status = payload.get("new_status", "unknown")

            await self._notify_all_staff(
                notification_type=NotificationType.ADOPTION_STATUS_CHANGED,
                title="Adoption Status Updated",
                message=f"Adoption request status changed from {old_status} to {new_status}.",
                data={
                    "aggregate_id": str(event.aggregate_id) if event.aggregate_id else None,
                    "old_status": old_status,
                    "new_status": new_status,
                },
            )
        except Exception as exc:
            logger.exception(
                "Failed to create in-app notification for adoption_status_changed event_id=%s: %s",
                event.id,
                exc,
            )

    async def on_donation_received(self, event: DomainEvent) -> None:
        """Notify staff (who have in_app enabled) when a donation is received."""
        try:
            payload = event.payload
            amount = payload.get("amount", "0")
            currency = payload.get("currency", "PYG")
            donor_name = payload.get("donor_name", "Anonymous")

            await self._notify_all_staff(
                notification_type=NotificationType.DONATION_RECEIVED,
                title="Donation Received",
                message=f"{donor_name} donated {amount} {currency}.",
                data={
                    "aggregate_id": str(event.aggregate_id) if event.aggregate_id else None,
                    "amount": str(amount),
                    "currency": currency,
                    "donor_name": donor_name,
                },
            )
        except Exception as exc:
            logger.exception(
                "Failed to create in-app notification for donation_received event_id=%s: %s",
                event.id,
                exc,
            )

    async def on_animal_intake_completed(self, event: DomainEvent) -> None:
        """Notify staff (who have in_app enabled) when a new animal is taken in."""
        try:
            payload = event.payload
            animal_name = payload.get("animal_name", "New animal")
            species = payload.get("species", "")

            await self._notify_all_staff(
                notification_type=NotificationType.ANIMAL_INTAKE_COMPLETED,
                title="New Animal Intake",
                message=f"{animal_name} ({species}) has been admitted to the shelter.",
                data={
                    "aggregate_id": str(event.aggregate_id) if event.aggregate_id else None,
                    "animal_name": animal_name,
                    "species": species,
                },
            )
        except Exception as exc:
            logger.exception(
                "Failed to create in-app notification for animal_intake_completed event_id=%s: %s",
                event.id,
                exc,
            )

    async def _notify_all_staff(
        self,
        *,
        notification_type: str,
        title: str,
        message: str,
        data: dict | None = None,
    ) -> None:
        """Create an in-app notification for each active staff/admin user who has opted in.

        Checks the in_app preference for the given notification_type per user.
        Missing preference rows are treated as enabled (opt-out model).
        """
        async with get_async_session() as db:
            stmt = select(User.id).where(
                User.is_active == True,  # noqa: E712
                User.role.in_([UserRole.STAFF.value, UserRole.ADMIN.value]),
            )
            result = await db.execute(stmt)
            user_ids: list[UUID] = list(result.scalars().all())

            for user_id in user_ids:
                enabled = await is_notification_enabled(
                    db,
                    user_id=user_id,
                    notification_type=notification_type,
                    channel=NotificationChannel.IN_APP,
                )
                if not enabled:
                    logger.debug(
                        "Skipping in_app notification type=%s for user_id=%s (opted out)",
                        notification_type,
                        user_id,
                    )
                    continue

                await create_notification(
                    db,
                    user_id=user_id,
                    notification_type=notification_type,
                    title=title,
                    message=message,
                    data=data,
                )
