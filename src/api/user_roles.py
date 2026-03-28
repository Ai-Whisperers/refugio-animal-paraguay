"""User role management API endpoints.

Endpoints:
  GET  /api/users/roles  - List current user roles + available roles
  POST /api/users/roles  - Add or remove a role
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import _get_current_user
from src.db.models.user import User
from src.db.session import get_db
from src.schemas.error import COMMON_RESPONSES
from src.schemas.user_role import RoleActionRequest, RoleActionResponse, UserRolesResponse
from src.services.user_role_service import (
    ROLE_DESCRIPTIONS,
    ROLE_WELCOME_MESSAGES,
    SELF_ASSIGNABLE_ROLES,
    InvalidRoleError,
    LastRoleError,
    RoleAlreadyAssignedError,
    add_role,
    get_user_roles,
    remove_role,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/users",
    tags=["user-roles"],
    responses=COMMON_RESPONSES,
)


def _build_available_roles(current_roles: list[str]) -> list[dict]:
    """Build the available roles list with descriptions and assignment state."""
    return [
        {
            "role": role,
            "label": role.capitalize(),
            "description": ROLE_DESCRIPTIONS.get(role, ""),
            "assigned": role in current_roles,
        }
        for role in sorted(SELF_ASSIGNABLE_ROLES)
    ]


@router.get("/roles", response_model=UserRolesResponse)
async def list_user_roles(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user),
) -> UserRolesResponse:
    """List all roles assigned to the current user and available roles."""
    roles = await get_user_roles(db, str(current_user.id))
    return UserRolesResponse(
        roles=roles,
        available_roles=_build_available_roles(roles),
    )


@router.post("/roles", response_model=RoleActionResponse)
async def modify_user_role(
    body: RoleActionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user),
) -> RoleActionResponse:
    """Add or remove a role from the current user.

    Users must always have at least one role.
    """
    user_id = str(current_user.id)

    try:
        if body.action == "add":
            roles = await add_role(db, user_id, body.role)
            message = ROLE_WELCOME_MESSAGES.get(
                body.role, f"Role '{body.role}' added."
            )
        else:
            roles = await remove_role(db, user_id, body.role)
            message = f"Role '{body.role}' removed."
    except RoleAlreadyAssignedError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=exc.message,
        ) from exc
    except LastRoleError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.message,
        ) from exc
    except InvalidRoleError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.message,
        ) from exc

    return RoleActionResponse(roles=roles, message=message)
