"""Pydantic schemas for role management endpoints."""

from typing import Literal

from pydantic import BaseModel, Field


class RoleActionRequest(BaseModel):
    """Request body for POST /api/users/roles."""

    role: Literal["adopter", "donor", "volunteer", "foster"] = Field(
        ..., description="Role to add or remove."
    )
    action: Literal["add", "remove"] = Field(
        default="add", description="Whether to add or remove the role."
    )


class RoleActionResponse(BaseModel):
    """Response after a role change."""

    roles: list[str] = Field(..., description="Updated list of all user roles.")
    message: str = Field(..., description="Confirmation message.")


class UserRolesResponse(BaseModel):
    """Response for GET /api/users/roles."""

    roles: list[str]
    available_roles: list[dict] = Field(
        ..., description="Roles available for self-assignment with descriptions."
    )
