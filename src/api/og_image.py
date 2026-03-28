"""Open Graph image generation API.

Generates dynamic PNG cards for social media unfurling.
GET /og-image/{type}/{id} returns a 1200x630 PNG with Cache-Control headers.
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_async_session
from src.services.og_image_service import (
    CardData,
    InvalidCardTypeError,
    OGImageError,
    generate_og_image,
    generate_placeholder,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/og-image", tags=["og-image"])

CACHE_MAX_AGE = 3600  # 1 hour


@router.get("/{card_type}/{entity_id}")
async def get_og_image(
    card_type: str,
    entity_id: UUID,
    db: AsyncSession = Depends(get_async_session),
) -> Response:
    """Generate and return an OG image for the given entity.

    Returns a PNG image with appropriate caching headers.
    Falls back to a placeholder on error.
    """
    try:
        data = await _resolve_card_data(card_type, entity_id, db)
        png_bytes = generate_og_image(card_type, data)
    except InvalidCardTypeError:
        png_bytes = generate_placeholder()
    except OGImageError:
        png_bytes = generate_placeholder()
    except Exception:
        logger.exception("Unexpected error generating OG image: %s/%s", card_type, entity_id)
        png_bytes = generate_placeholder()

    return Response(
        content=png_bytes,
        media_type="image/png",
        headers={
            "Cache-Control": f"public, max-age={CACHE_MAX_AGE}",
        },
    )


async def _resolve_card_data(
    card_type: str,
    entity_id: UUID,
    db: AsyncSession,
) -> CardData:
    """Look up entity data and build a CardData for the given type.

    For animal/campaign/story/blog, queries the respective table.
    Falls back to generic card if the entity is not found.
    """
    if card_type == "animal":
        return await _resolve_animal(entity_id, db)
    if card_type == "campaign":
        return await _resolve_campaign(entity_id, db)
    if card_type == "story":
        return await _resolve_story(entity_id, db)
    if card_type == "blog":
        return await _resolve_blog(entity_id, db)

    # Unknown type — will be caught by generate_og_image
    return CardData(title="Refugio Animal Paraguay")


async def _resolve_animal(entity_id: UUID, db: AsyncSession) -> CardData:
    """Resolve animal data for OG card."""
    from src.db.models.animal import Animal

    result = await db.execute(select(Animal).where(Animal.id == entity_id))
    animal = result.scalar_one_or_none()
    if animal is None:
        return CardData(title="Animal not found", cta_text="Visit Refugio")
    return CardData(
        title=animal.name or "Unknown",
        subtitle=f"{animal.species} - {animal.breed}" if animal.breed else animal.species,
        cta_text="Adoptame!",
    )


async def _resolve_campaign(entity_id: UUID, db: AsyncSession) -> CardData:
    """Resolve campaign data for OG card."""
    from src.db.models.campaign import Campaign

    result = await db.execute(select(Campaign).where(Campaign.id == entity_id))
    campaign = result.scalar_one_or_none()
    if campaign is None:
        return CardData(title="Campaign not found", cta_text="Visit Refugio")

    goal = float(campaign.goal_amount) if campaign.goal_amount else 0
    raised = float(campaign.raised_amount) if campaign.raised_amount else 0
    pct = (raised / goal * 100) if goal > 0 else 0.0

    return CardData(
        title=campaign.title or "Campaign",
        subtitle=campaign.description[:100] if campaign.description else None,
        cta_text="Donate!",
        progress_pct=round(pct, 1),
        progress_text=f"${raised:,.0f} / ${goal:,.0f} ({pct:.0f}%)",
    )


async def _resolve_story(entity_id: UUID, db: AsyncSession) -> CardData:
    """Resolve CMS story content for OG card."""
    from src.db.models.cms_content import CMSContent

    result = await db.execute(select(CMSContent).where(CMSContent.id == entity_id))
    content = result.scalar_one_or_none()
    if content is None:
        return CardData(title="Story not found", cta_text="Visit Refugio")
    return CardData(
        title=content.title or "Story",
        subtitle=content.meta_description if hasattr(content, "meta_description") else None,
        cta_text="Read Story",
    )


async def _resolve_blog(entity_id: UUID, db: AsyncSession) -> CardData:
    """Resolve CMS blog content for OG card."""
    from src.db.models.cms_content import CMSContent

    result = await db.execute(select(CMSContent).where(CMSContent.id == entity_id))
    content = result.scalar_one_or_none()
    if content is None:
        return CardData(title="Blog post not found")

    date_text = content.published_at.strftime("%B %d, %Y") if content.published_at else None
    return CardData(
        title=content.title or "Blog Post",
        author=content.author if hasattr(content, "author") else None,
        date_text=date_text,
    )
