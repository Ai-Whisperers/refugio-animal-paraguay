"""User role management service: add, remove, and list roles.

Supports multi-role users where each user can have any combination of
public roles (adopter, donor, volunteer, foster). Users must always have
at least one role.
"""

import logging

from sqlalchemy import and_, delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.user import User
from src.db.models.user_role import UserRoleAssignment

logger = logging.getLogger(__name__)

# Roles that can be self-assigned by public users
SELF_ASSIGNABLE_ROLES = frozenset({"adopter", "donor", "volunteer", "foster"})

# Role descriptions (Spanish) for UI display
ROLE_DESCRIPTIONS = {
    "adopter": "Adoptar animales del refugio",
    "donor": "Apoyar a los animales con donaciones",
    "volunteer": "Ayudar con el cuidado, transporte y eventos",
    "foster": "Cuidar temporalmente animales en tu hogar",
}

ROLE_WELCOME_MESSAGES = {
    "adopter": "Ahora puedes buscar y adoptar animales.",
    "donor": "Ahora puedes realizar donaciones y ver tu historial.",
    "volunteer": "Ahora puedes ver oportunidades de voluntariado.",
    "foster": "Ahora puedes ver animales disponibles para hogar transitorio.",
}


class RoleError(Exception):
    """Base error for role operations."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class InvalidRoleError(RoleError):
    """Raised when a role value is not valid."""

    pass


class RoleAlreadyAssignedError(RoleError):
    """Raised when trying to add a role the user already has."""

    pass


class LastRoleError(RoleError):
    """Raised when trying to remove the user's only remaining role."""

    pass


async def get_user_roles(db: AsyncSession, user_id: str) -> list[str]:
    """Get all roles assigned to a user.

    Returns a list of role strings. Includes the primary role from users.role
    and any additional roles from user_roles table.
    """
    result = await db.execute(
        select(UserRoleAssignment.role)
        .where(UserRoleAssignment.user_id == user_id)
        .order_by(UserRoleAssignment.created_at)
    )
    roles = [row[0] for row in result.all()]

    # If no roles in junction table, fall back to primary role
    if not roles:
        user = await db.get(User, user_id)
        if user is not None:
            return [user.role]

    return roles


async def add_role(db: AsyncSession, user_id: str, role: str) -> list[str]:
    """Add a role to a user. Returns the updated list of roles.

    Raises InvalidRoleError if role is not self-assignable.
    Raises RoleAlreadyAssignedError if user already has this role.
    """
    if role not in SELF_ASSIGNABLE_ROLES:
        raise InvalidRoleError(f"Role '{role}' is not available for self-assignment.")

    # Check if already assigned
    existing = await db.execute(
        select(UserRoleAssignment).where(
            and_(
                UserRoleAssignment.user_id == user_id,
                UserRoleAssignment.role == role,
            )
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise RoleAlreadyAssignedError(f"You already have the '{role}' role.")

    # Ensure user has at least their primary role in the junction table
    await _ensure_primary_role_synced(db, user_id)

    # Add the new role
    assignment = UserRoleAssignment(user_id=user_id, role=role)
    db.add(assignment)
    await db.flush()

    return await get_user_roles(db, user_id)


async def remove_role(db: AsyncSession, user_id: str, role: str) -> list[str]:
    """Remove a role from a user. Returns the updated list of roles.

    Raises InvalidRoleError if role is not valid.
    Raises LastRoleError if this is the user's only role.
    """
    if role not in SELF_ASSIGNABLE_ROLES:
        raise InvalidRoleError(f"Role '{role}' cannot be removed.")

    # Get current role count
    current_roles = await get_user_roles(db, user_id)
    if len(current_roles) <= 1:
        raise LastRoleError("You must have at least one role.")

    if role not in current_roles:
        raise InvalidRoleError(f"You don't have the '{role}' role.")

    # Remove the role
    await db.execute(
        delete(UserRoleAssignment).where(
            and_(
                UserRoleAssignment.user_id == user_id,
                UserRoleAssignment.role == role,
            )
        )
    )
    await db.flush()

    # If we removed the primary role, update users.role to first remaining
    user = await db.get(User, user_id)
    if user is not None and user.role == role:
        remaining = await get_user_roles(db, user_id)
        if remaining:
            user.role = remaining[0]
            await db.flush()

    return await get_user_roles(db, user_id)


async def _ensure_primary_role_synced(db: AsyncSession, user_id: str) -> None:
    """Ensure the user's primary role exists in the user_roles junction table."""
    user = await db.get(User, user_id)
    if user is None:
        return

    existing = await db.execute(
        select(UserRoleAssignment).where(
            and_(
                UserRoleAssignment.user_id == user_id,
                UserRoleAssignment.role == user.role,
            )
        )
    )
    if existing.scalar_one_or_none() is None:
        assignment = UserRoleAssignment(user_id=user_id, role=user.role)
        db.add(assignment)
        await db.flush()
