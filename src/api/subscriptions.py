"""Recurring donation subscription management endpoints.

Endpoints:
  POST   /subscriptions                   -- create a new recurring donation subscription
  GET    /subscriptions                   -- list subscriptions (staff only, paginated)
  GET    /subscriptions/stats             -- aggregated subscription statistics (staff only)
  GET    /subscriptions/{id}              -- get subscription details
  GET    /subscriptions/donor/{donor_id}  -- list subscriptions for a specific donor
  POST   /subscriptions/{id}/cancel       -- cancel a subscription
  POST   /subscriptions/{id}/pause        -- pause a subscription
  POST   /subscriptions/{id}/resume       -- resume a paused subscription
  PATCH  /subscriptions/{id}              -- update subscription (amount, payment method)
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.donation import Donor
from src.db.models.subscription import Subscription, SubscriptionStatus
from src.db.session import get_db
from src.schemas.subscription import (
    SubscriptionCancelRequest,
    SubscriptionCreateRequest,
    SubscriptionDetailResponse,
    SubscriptionListResponse,
    SubscriptionStatsResponse,
    SubscriptionUpdateRequest,
)
from src.services import subscription_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


@router.post(
    "",
    response_model=SubscriptionDetailResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_subscription(
    payload: SubscriptionCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> SubscriptionDetailResponse:
    """Create a new recurring donation subscription.

    Sets up a Stripe subscription with the specified interval and payment method.
    The donor must exist and the payment method must be valid (card or SEPA).
    """
    donor = await db.get(Donor, payload.donor_id)
    if donor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Donor not found",
        )

    try:
        subscription = await subscription_service.create_subscription(
            db=db,
            donor=donor,
            amount_cents=payload.amount_cents,
            currency=payload.currency.value,
            interval=payload.interval.value,
            payment_method_id=payload.payment_method_id,
            notes=payload.notes,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception("Failed to create subscription for donor %s", payload.donor_id)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Payment gateway error: {exc}",
        ) from exc

    return SubscriptionDetailResponse.model_validate(subscription)


@router.get(
    "/stats",
    response_model=SubscriptionStatsResponse,
)
async def get_stats(
    db: AsyncSession = Depends(get_db),
) -> SubscriptionStatsResponse:
    """Get aggregated subscription statistics for the staff dashboard."""
    stats = await subscription_service.get_subscription_stats(db)
    return SubscriptionStatsResponse(**stats)


@router.get(
    "",
    response_model=SubscriptionListResponse,
)
async def list_subscriptions(
    db: AsyncSession = Depends(get_db),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    status_filter: str | None = Query(default=None, alias="status"),
    donor_id: UUID | None = Query(default=None),
) -> SubscriptionListResponse:
    """List subscriptions with optional filters (staff only).

    Supports filtering by status and donor_id, with pagination.
    """
    stmt = select(Subscription)
    count_stmt = select(func.count(Subscription.id))

    if status_filter:
        stmt = stmt.where(Subscription.status == status_filter)
        count_stmt = count_stmt.where(Subscription.status == status_filter)

    if donor_id:
        stmt = stmt.where(Subscription.donor_id == donor_id)
        count_stmt = count_stmt.where(Subscription.donor_id == donor_id)

    # Get total count
    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0

    # Get paginated results
    offset = (page - 1) * per_page
    stmt = stmt.order_by(Subscription.created_at.desc()).offset(offset).limit(per_page)
    result = await db.execute(stmt)
    subscriptions = list(result.scalars().all())

    return SubscriptionListResponse(
        items=[SubscriptionDetailResponse.model_validate(s) for s in subscriptions],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get(
    "/donor/{donor_id}",
    response_model=list[SubscriptionDetailResponse],
)
async def list_donor_subscriptions(
    donor_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> list[SubscriptionDetailResponse]:
    """List all subscriptions for a specific donor."""
    donor = await db.get(Donor, donor_id)
    if donor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Donor not found",
        )

    stmt = (
        select(Subscription)
        .where(Subscription.donor_id == donor_id)
        .order_by(Subscription.created_at.desc())
    )
    result = await db.execute(stmt)
    subscriptions = list(result.scalars().all())

    return [SubscriptionDetailResponse.model_validate(s) for s in subscriptions]


@router.get(
    "/{subscription_id}",
    response_model=SubscriptionDetailResponse,
)
async def get_subscription(
    subscription_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> SubscriptionDetailResponse:
    """Get subscription details by ID."""
    subscription = await db.get(Subscription, subscription_id)
    if subscription is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found",
        )
    return SubscriptionDetailResponse.model_validate(subscription)


@router.post(
    "/{subscription_id}/cancel",
    response_model=SubscriptionDetailResponse,
)
async def cancel_subscription_endpoint(
    subscription_id: UUID,
    payload: SubscriptionCancelRequest,
    db: AsyncSession = Depends(get_db),
) -> SubscriptionDetailResponse:
    """Cancel a subscription.

    By default, cancels at the end of the current billing period.
    Set cancel_immediately=true to cancel right away.
    """
    subscription = await db.get(Subscription, subscription_id)
    if subscription is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found",
        )

    if subscription.status == SubscriptionStatus.CANCELED.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Subscription is already canceled",
        )

    try:
        updated = await subscription_service.cancel_subscription(
            db=db,
            subscription=subscription,
            cancel_immediately=payload.cancel_immediately,
            reason=payload.reason,
        )
    except Exception as exc:
        logger.exception("Failed to cancel subscription %s", subscription_id)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Payment gateway error: {exc}",
        ) from exc

    return SubscriptionDetailResponse.model_validate(updated)


@router.post(
    "/{subscription_id}/pause",
    response_model=SubscriptionDetailResponse,
)
async def pause_subscription_endpoint(
    subscription_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> SubscriptionDetailResponse:
    """Pause an active subscription.

    Invoices will not be generated while paused. Use /resume to reactivate.
    """
    subscription = await db.get(Subscription, subscription_id)
    if subscription is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found",
        )

    if subscription.status != SubscriptionStatus.ACTIVE.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot pause subscription with status '{subscription.status}'",
        )

    try:
        updated = await subscription_service.pause_subscription(db, subscription)
    except Exception as exc:
        logger.exception("Failed to pause subscription %s", subscription_id)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Payment gateway error: {exc}",
        ) from exc

    return SubscriptionDetailResponse.model_validate(updated)


@router.post(
    "/{subscription_id}/resume",
    response_model=SubscriptionDetailResponse,
)
async def resume_subscription_endpoint(
    subscription_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> SubscriptionDetailResponse:
    """Resume a paused subscription."""
    subscription = await db.get(Subscription, subscription_id)
    if subscription is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found",
        )

    if subscription.status != SubscriptionStatus.PAUSED.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot resume subscription with status '{subscription.status}'",
        )

    try:
        updated = await subscription_service.resume_subscription(db, subscription)
    except Exception as exc:
        logger.exception("Failed to resume subscription %s", subscription_id)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Payment gateway error: {exc}",
        ) from exc

    return SubscriptionDetailResponse.model_validate(updated)


@router.patch(
    "/{subscription_id}",
    response_model=SubscriptionDetailResponse,
)
async def update_subscription(
    subscription_id: UUID,
    payload: SubscriptionUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> SubscriptionDetailResponse:
    """Update a subscription (amount, payment method, notes)."""
    subscription = await db.get(Subscription, subscription_id)
    if subscription is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found",
        )

    if subscription.status not in (
        SubscriptionStatus.ACTIVE.value,
        SubscriptionStatus.PAST_DUE.value,
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot update subscription with status '{subscription.status}'",
        )

    try:
        if payload.amount_cents is not None:
            subscription = await subscription_service.update_subscription_amount(
                db, subscription, payload.amount_cents
            )

        if payload.payment_method_id is not None:
            import stripe

            stripe.api_key = subscription_service._get_stripe_key()
            stripe.PaymentMethod.attach(
                payload.payment_method_id,
                customer=subscription.stripe_customer_id,
            )
            stripe.Subscription.modify(
                subscription.stripe_subscription_id,
                default_payment_method=payload.payment_method_id,
            )
            subscription.stripe_payment_method_id = payload.payment_method_id
            await db.flush()

        if payload.notes is not None:
            subscription.notes = payload.notes
            await db.flush()

        await db.refresh(subscription)

    except Exception as exc:
        logger.exception("Failed to update subscription %s", subscription_id)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Payment gateway error: {exc}",
        ) from exc

    return SubscriptionDetailResponse.model_validate(subscription)
