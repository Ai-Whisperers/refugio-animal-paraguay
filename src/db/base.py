"""SQLAlchemy declarative base for Refugio Animal Paraguay ORM models."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models.

    All models inherit from this class to participate in SQLAlchemy's
    metadata registry and relationship resolution.
    """

    pass
