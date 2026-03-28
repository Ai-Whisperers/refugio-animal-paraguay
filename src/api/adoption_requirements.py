"""Admin endpoints for configurable adoption requirements.

Endpoints:
    POST   /admin/adoption-requirements           -- create global requirement
    POST   /admin/animals/{animal_id}/requirements -- create animal-specific requirement
    GET    /admin/animals/{animal_id}/requirements -- list merged requirements
    PUT    /admin/animals/{animal_id}/requirements/{req_id} -- update requirement
    DELETE /admin/animals/{animal_id}/requirements/{req_id} -- soft-delete
    GET    /api/animals/{animal_id}/pre-qualify    -- pre-qualification questions
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_admin, require_staff
from src.db.models.user import User
from src.db.session import get_db
from src.schemas.error import RESOURCE_RESPONSES
from src.services.adoption_requirement_service import (
    InvalidRequirementValueError,
    RequirementNotFoundError,
    create_requirement,
    get_animal_requirements,
    get_pre_qualification_questions,
    soft_delete_requirement,
    update_requirement,
)

logger = logging.getLogger(__name__)

admin_router = APIRouter(
    prefix="/admin",
    tags=["adoption-requirements"],
    responses=RESOURCE_RESPONSES,
)

public_router = APIRouter(
    prefix="/api/animals",
    tags=["adoption-pre-qualify"],
    responses=RESOURCE_RESPONSES,
)


# --- Schemas ---


class CreateRequirementRequest(BaseModel):
    """Request to create an adoption requirement."""

    requirement_type: str
    value: dict
    is_mandatory: bool = True


class UpdateRequirementRequest(BaseModel):
    """Request to update an adoption requirement."""

    value: dict | None = None
    is_mandatory: bool | None = None


class RequirementResponse(BaseModel):
    """Single adoption requirement."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    animal_id: UUID | None = None
    requirement_type: str
    value: dict
    is_mandatory: bool
    active: bool
    created_at: str
    updated_at: str


class RequirementListResponse(BaseModel):
    """List of adoption requirements."""

    items: list[RequirementResponse]
    total: int


class PreQualifyQuestionResponse(BaseModel):
    """Pre-qualification question for an adopter."""

    id: str
    requirement_type: str
    value: dict
    is_mandatory: bool
    animal_id: str | None = None
    human_readable_description: str


class PreQualifyResponse(BaseModel):
    """Pre-qualification questions for an animal."""

    animal_id: UUID
    questions: list[PreQualifyQuestionResponse]


# --- Admin Endpoints ---


@admin_router.post(
    "/adoption-requirements",
    response_model=RequirementResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_global_requirement(
    body: CreateRequirementRequest,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_admin),
) -> RequirementResponse:
    """Create a global adoption requirement (applies to all animals)."""
    try:
        requirement = await create_requirement(
            db,
            requirement_type=body.requirement_type,
            value=body.value,
            is_mandatory=body.is_mandatory,
            animal_id=None,
        )
    except InvalidRequirementValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=exc.message,
        ) from None

    await db.commit()
    return RequirementResponse.model_validate(requirement)


@admin_router.post(
    "/animals/{animal_id}/requirements",
    response_model=RequirementResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_animal_requirement(
    animal_id: UUID,
    body: CreateRequirementRequest,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_admin),
) -> RequirementResponse:
    """Create an animal-specific adoption requirement."""
    try:
        requirement = await create_requirement(
            db,
            requirement_type=body.requirement_type,
            value=body.value,
            is_mandatory=body.is_mandatory,
            animal_id=animal_id,
        )
    except InvalidRequirementValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=exc.message,
        ) from None

    await db.commit()
    return RequirementResponse.model_validate(requirement)


@admin_router.get(
    "/animals/{animal_id}/requirements",
    response_model=RequirementListResponse,
)
async def list_animal_requirements(
    animal_id: UUID,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_admin),
) -> RequirementListResponse:
    """List all requirements for an animal (global + specific, merged)."""
    requirements = await get_animal_requirements(db, animal_id)
    return RequirementListResponse(
        items=[RequirementResponse.model_validate(r) for r in requirements],
        total=len(requirements),
    )


@admin_router.put(
    "/animals/{animal_id}/requirements/{requirement_id}",
    response_model=RequirementResponse,
)
async def update_animal_requirement(
    animal_id: UUID,
    requirement_id: UUID,
    body: UpdateRequirementRequest,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_admin),
) -> RequirementResponse:
    """Update an adoption requirement's value or mandatory flag."""
    try:
        requirement = await update_requirement(
            db,
            requirement_id,
            value=body.value,
            is_mandatory=body.is_mandatory,
        )
    except RequirementNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Requirement {requirement_id} not found.",
        ) from None
    except InvalidRequirementValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=exc.message,
        ) from None

    await db.commit()
    return RequirementResponse.model_validate(requirement)


@admin_router.delete(
    "/animals/{animal_id}/requirements/{requirement_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_animal_requirement(
    animal_id: UUID,
    requirement_id: UUID,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_admin),
) -> None:
    """Soft-delete an adoption requirement (sets active=false)."""
    try:
        await soft_delete_requirement(db, requirement_id)
    except RequirementNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Requirement {requirement_id} not found.",
        ) from None

    await db.commit()


# --- Public Endpoint ---


@public_router.get(
    "/{animal_id}/pre-qualify",
    response_model=PreQualifyResponse,
)
async def get_pre_qualify_questions(
    animal_id: UUID,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_staff),
) -> PreQualifyResponse:
    """Get pre-qualification questions for an animal based on its requirements."""
    questions = await get_pre_qualification_questions(db, animal_id)
    return PreQualifyResponse(
        animal_id=animal_id,
        questions=[PreQualifyQuestionResponse(**q) for q in questions],
    )
