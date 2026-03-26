---
epic: EPIC-1
story: S01
task: T01
title: Define SQLAlchemy Animal Model and Alembic Migration
status: pending
effort_hours: 3
priority: high
dependencies: []
---

## Overview

Define the Animal SQLAlchemy model in the backend source code and create the corresponding Alembic migration that produces the animals table in PostgreSQL. This task establishes the canonical data structure for all animal records in the system. Every subsequent feature — the catalog API, adoption workflow, photo management, and veterinary records — depends on this model being complete and correct before any other data work begins.

## Why This Matters

The Animal model is the central entity in the entire platform. Its column definitions, enum constraints, and relationships determine how animal data flows through every layer of the application. Defining the model correctly now prevents costly migration churn later. The enum types for status, species, and gender must be defined as both Python enums (for type safety in business logic) and as PostgreSQL enum types (for database-level constraint enforcement). The indexes defined here directly affect query performance on the public catalog endpoint, which is the most frequently accessed route in the entire system.

## Context

The project uses SQLAlchemy 2.x with the declarative base pattern and Pydantic v2 for request and response schemas. Access control is enforced entirely at the FastAPI layer using JWT dependencies — there are no PostgreSQL Row Level Security policies in this system. Staff and admin roles are determined from JWT token claims and enforced by FastAPI dependency injection before any SQLAlchemy query executes. Alembic manages all schema changes. No table is ever created or modified directly against the database. Every schema change must have a corresponding Alembic migration file that can be applied with alembic upgrade head and rolled back cleanly with alembic downgrade.

## Implementation Steps

### Step 1: Define Python Enums for Animal Attributes

In src/models/animal.py, define three Python enums using the standard library enum module. The AnimalStatus enum covers the lifecycle states an animal can be in: available (ready for adoption inquiry), reserved (an adoption application is under review), adopted (adoption completed), medical_hold (receiving veterinary treatment and not currently available for adoption), and deceased. The AnimalSpecies enum covers the main species the shelter handles: dog, cat, rabbit, bird, and other. The AnimalGender enum has values male and female.

Each enum class should inherit from both str and Enum so that values serialize naturally as strings in JSON responses without requiring custom serializers. This inheritance pattern integrates cleanly with Pydantic v2 schemas and avoids the need for explicit json_encoders configuration.

### Step 2: Define the Animal SQLAlchemy Model

In the same file src/models/animal.py, define the Animal class inheriting from the SQLAlchemy declarative Base imported from src/database.py. The table name is animals.

The primary key is an integer column named id with autoincrement set to True. Using an integer primary key rather than a UUID simplifies join queries, improves index performance, and makes API URLs more readable.

The remaining columns are as follows. The name column is a String type, non-nullable, and holds the animal's given name at the shelter. The species column is a SQLAlchemy Enum type constructed from the AnimalSpecies Python enum, non-nullable. The breed column is a String type, nullable, for the specific breed within the species — many rescued animals have unknown breed. The gender column is a SQLAlchemy Enum type constructed from AnimalGender, non-nullable. The approximate_age_months column is an Integer type, nullable, because age is often unknown for rescued animals. The weight_kg column is a Numeric type with precision 5 and scale 2, nullable. The status column is a SQLAlchemy Enum type constructed from AnimalStatus, non-nullable, with a server_default set to the string value of AnimalStatus.available so new records are available without requiring explicit assignment. The description column is a Text type, nullable, for the freeform prose description shown on the public catalog. The is_featured column is a Boolean type, non-nullable, defaulting to False, used to highlight specific animals on the homepage. The is_vaccinated column is a Boolean type, nullable. The is_neutered column is a Boolean type, nullable. The microchip_number column is a String of length 50, nullable, with a unique constraint. The intake_date column is a Date type, non-nullable, recording the date the animal arrived at the shelter. The shelter_id column is an Integer type referencing shelters.id as a foreign key, non-nullable. The created_at column is a DateTime type with timezone set to True, non-nullable, with server_default set to func.now(). The updated_at column is a DateTime type with timezone set to True, nullable, with onupdate set to func.now() so SQLAlchemy automatically refreshes this column on every UPDATE statement.

Define a SQLAlchemy relationship from Animal to Shelter using the relationship() function with the attribute named shelter. Define the corresponding back-reference on Shelter so that accessing shelter.animals returns the list of Animal records associated with that shelter.

### Step 3: Define PostgreSQL Indexes

Indexes on the animals table are defined inside the __table_args__ tuple on the Animal model class using SQLAlchemy's Index constructor. Define four indexes: one on the status column, because the public catalog API filters by status available on nearly every request; one on the species column, because species filtering is the second most common query parameter; one on shelter_id, because shelter-scoped queries need this for efficient JOIN execution; and one on intake_date, because the admin dashboard sorts and filters by intake date for monthly reporting. Name each index descriptively using the pattern ix_animals followed by the column name.

### Step 4: Define Pydantic v2 Schemas

In src/schemas/animal.py, define three Pydantic v2 model classes. AnimalBase contains all fields that appear in both creation requests and responses: name, species, breed, gender, approximate_age_months, weight_kg, status, description, is_featured, is_vaccinated, is_neutered, microchip_number, intake_date, and shelter_id. AnimalCreate inherits from AnimalBase and adds no additional fields — it represents the request body for POST /animals. AnimalResponse inherits from AnimalBase and adds id, created_at, and updated_at. All three classes configure model_config equal to ConfigDict(from_attributes=True) so that Pydantic can construct response instances directly from SQLAlchemy ORM objects returned by session queries.

### Step 5: Create the Alembic Migration

Generate the initial migration for the animals table by running alembic revision with the --autogenerate flag after the Animal model is defined and the model file is imported in the Alembic env.py. Alembic reads the model definition, compares it against the current database state, and generates a migration file in alembic/versions/.

Review the generated migration file before applying it. Confirm that the upgrade function creates the PostgreSQL enum types first, then creates the animals table with all columns and constraints, then creates all four indexes in the correct order. Confirm that the downgrade function drops the indexes, drops the table, and drops the enum types in reverse order.

Apply the migration with alembic upgrade head and verify the table was created correctly.

### Step 6: Enforce Access Control via FastAPI Dependencies

Access to animal data is controlled at the FastAPI route layer. The GET /animals and GET /animals/{id} routes are public and require no authentication. The POST /animals, PATCH /animals/{id}, and DELETE /animals/{id} routes require a valid JWT token with a staff or admin role claim.

Access control is implemented as a FastAPI dependency function in src/dependencies/auth.py. The dependency reads the Authorization header, decodes the JWT token using the python-jose library, extracts the role claim, and raises HTTPException with status code 403 if the role does not have permission for the requested operation. Route handlers receive the current user object via Depends() and never read the Authorization header directly. There are no PostgreSQL RLS policies anywhere in this system — all access control logic lives in FastAPI dependencies.

## Acceptance Criteria

- The Animal class is defined in src/models/animal.py using SQLAlchemy 2.x declarative syntax with all columns, enum types, indexes, and the shelter relationship
- AnimalStatus, AnimalSpecies, and AnimalGender are Python enums that inherit from both str and Enum
- The Alembic migration file applies cleanly with alembic upgrade head and rolls back cleanly with alembic downgrade
- The animals table exists in PostgreSQL after migration with all columns, constraints, enum types, and indexes present
- Pydantic v2 schemas AnimalBase, AnimalCreate, and AnimalResponse are defined in src/schemas/animal.py with ConfigDict(from_attributes=True)
- The FastAPI auth dependency enforces staff and admin role requirement on all write endpoints
- No RLS policies exist in the database — all access control is enforced in the FastAPI dependency layer

## Common Issues and Solutions

If Alembic does not detect the Animal model during autogenerate, the model file is not being imported when Alembic loads the metadata. The fix is to import the Animal model in alembic/env.py before target_metadata is assigned, so SQLAlchemy registers the table in the metadata object that Alembic inspects.

If the PostgreSQL enum types already exist from a previous failed migration attempt, the upgrade function will fail with a type already exists error. Add conditional checks to the CREATE TYPE statements, or drop the orphaned types manually before re-running the migration.

If onupdate on updated_at does not fire, verify that the SQLAlchemy session calls session.commit() after updates rather than only session.flush(). The onupdate hook fires during SQL UPDATE generation, which only happens at flush or commit time.

## Related Tasks

- S01/T02: Configure Alembic migration workflow and database management commands — the tooling that applies and manages this migration
- S01/T03: Implement seed data for testing — test animals that populate the animals table created here
- S03/T01: Veterinary records model — defines a foreign key relationship pointing to the animals.id column defined here
