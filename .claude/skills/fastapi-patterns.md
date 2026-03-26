---
name: fastapi-patterns
description: Refugio-specific FastAPI structure, project layout, and dependency wiring — NOT generic FastAPI docs
load-when: Building FastAPI routes, dependency injection, lifespan events, or background tasks FOR THIS PROJECT
not-when: General Python questions, schema design, database queries, payment logic — use domain skills instead
project-specific: src/ layout, lifespan DB pool setup, pagination cursor pattern, error response schema
---

# Skill: FastAPI Patterns
**Load when**: Building REST API endpoints, writing route handlers, dependency injection, request/response schemas, background tasks.

---

## Project Structure

```
src/
├── main.py                  ← App factory, router mounting, lifespan
├── api/
│   ├── deps.py              ← Shared dependencies (db session, current user)
│   ├── v1/
│   │   ├── router.py        ← APIRouter aggregating all v1 routes
│   │   ├── adoptions.py     ← Adoption endpoints
│   │   ├── animals.py       ← Animal endpoints
│   │   ├── donations.py     ← Donation endpoints
│   │   └── auth.py          ← Auth endpoints
├── models/                  ← SQLAlchemy ORM models
├── schemas/                 ← Pydantic request/response schemas
├── services/                ← Business logic (no FastAPI imports here)
├── repositories/            ← Database access layer
└── core/
    ├── config.py            ← Settings via pydantic-settings
    ├── security.py          ← Password hashing, JWT
    └── database.py          ← Engine, SessionLocal, Base
```

---

## App Factory Pattern

```python
# src/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.v1.router import api_router
from src.core.config import settings
from src.core.database import engine, Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown
    await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix="/api/v1")
    return app


app = create_app()
```

---

## Schemas (Pydantic v2)

Separate input schemas from output schemas. Never expose ORM models directly.

```python
# src/schemas/animal.py
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from datetime import datetime
from enum import Enum


class AnimalStatus(str, Enum):
    AVAILABLE = "available"
    RESERVED = "reserved"
    ADOPTED = "adopted"


class AnimalBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    species: str
    breed: str | None = None
    age_months: int | None = Field(None, ge=0, le=240)
    status: AnimalStatus = AnimalStatus.AVAILABLE


class AnimalCreate(AnimalBase):
    """Input: creating a new animal record."""
    pass


class AnimalUpdate(BaseModel):
    """Input: partial update — all fields optional."""
    name: str | None = Field(None, min_length=1, max_length=100)
    status: AnimalStatus | None = None
    age_months: int | None = None


class AnimalResponse(AnimalBase):
    """Output: returned to API consumers."""
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)  # ORM mode
```

---

## Dependency Injection

```python
# src/api/deps.py
from typing import AsyncGenerator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import SessionLocal
from src.core.security import verify_token
from src.models.user import User
from src.repositories.user import UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Database session dependency — auto-closes on request end."""
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Verify JWT and return the authenticated user."""
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = await UserRepository(db).get_by_id(payload["sub"])
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


async def get_current_staff(
    current_user: User = Depends(get_current_user),
) -> User:
    """Require staff role — compose dependencies for role-based access."""
    if not current_user.is_staff:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Staff access required")
    return current_user
```

---

## Router Pattern

```python
# src/api/v1/animals.py
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_db, get_current_staff
from src.schemas.animal import AnimalCreate, AnimalUpdate, AnimalResponse
from src.schemas.pagination import PaginatedResponse
from src.services.animal import AnimalService

router = APIRouter(prefix="/animals", tags=["animals"])


@router.get("/", response_model=PaginatedResponse[AnimalResponse])
async def list_animals(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[AnimalResponse]:
    service = AnimalService(db)
    return await service.list(page=page, page_size=page_size, status_filter=status)


@router.get("/{animal_id}", response_model=AnimalResponse)
async def get_animal(
    animal_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> AnimalResponse:
    service = AnimalService(db)
    animal = await service.get_by_id(animal_id)
    if animal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Animal not found")
    return animal


@router.post("/", response_model=AnimalResponse, status_code=status.HTTP_201_CREATED)
async def create_animal(
    payload: AnimalCreate,
    db: AsyncSession = Depends(get_db),
    _: object = Depends(get_current_staff),  # staff-only
) -> AnimalResponse:
    service = AnimalService(db)
    return await service.create(payload)


@router.patch("/{animal_id}", response_model=AnimalResponse)
async def update_animal(
    animal_id: UUID,
    payload: AnimalUpdate,
    db: AsyncSession = Depends(get_db),
    _: object = Depends(get_current_staff),
) -> AnimalResponse:
    service = AnimalService(db)
    animal = await service.update(animal_id, payload)
    if animal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Animal not found")
    return animal
```

---

## Pagination Schema

```python
# src/schemas/pagination.py
from typing import Generic, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    pages: int

    @classmethod
    def create(cls, items: list[T], total: int, page: int, page_size: int) -> "PaginatedResponse[T]":
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=(total + page_size - 1) // page_size,
        )
```

---

## Error Handling

```python
# src/core/exceptions.py
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Return structured validation errors matching the WHAT+WHY+HOW diagnostic format."""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
        })
    return JSONResponse(
        status_code=422,
        content={"detail": "Validation failed", "errors": errors},
    )


# Register in main.py:
# app.add_exception_handler(RequestValidationError, validation_exception_handler)
```

---

## Background Tasks

```python
# For non-blocking operations (email, webhooks) — fire-and-forget
from fastapi import BackgroundTasks

@router.post("/adoptions/", response_model=AdoptionResponse, status_code=201)
async def submit_adoption(
    payload: AdoptionCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> AdoptionResponse:
    service = AdoptionService(db)
    adoption = await service.create(payload)
    # Queue notification without blocking the response
    background_tasks.add_task(send_adoption_confirmation_email, adoption.id)
    return adoption
```

---

## Settings (pydantic-settings)

```python
# src/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import PostgresDsn


class Settings(BaseSettings):
    PROJECT_NAME: str = "Refugio Animal Paraguay API"
    VERSION: str = "0.1.0"
    DATABASE_URL: PostgresDsn
    SECRET_KEY: str
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000"]
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24h

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


settings = Settings()
```

---

## Testing FastAPI

```python
# tests/conftest.py
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from src.main import app
from src.core.database import Base

TEST_DATABASE_URL = "postgresql+asyncpg://test:test@localhost/refugio_test"


@pytest.fixture
async def db() -> AsyncSession:
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSession(engine) as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def client(db: AsyncSession) -> AsyncClient:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
```

---

## Key Libraries

```
fastapi>=0.111
uvicorn[standard]
pydantic>=2.0
pydantic-settings
sqlalchemy[asyncio]>=2.0
asyncpg          ← PostgreSQL async driver
alembic          ← Migrations
httpx            ← Test client
pytest-asyncio
```
