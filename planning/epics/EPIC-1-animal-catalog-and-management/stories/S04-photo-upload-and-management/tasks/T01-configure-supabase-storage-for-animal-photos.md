---
epic: EPIC-1
story: S04
task: T01
title: Create animal_photos Table and SQLAlchemy Model
status: pending
effort_hours: 3
priority: high
dependencies:
  - S01/T01-define-supabase-schema-for-animals-table
---

## Overview

Create the animal_photos database table via an Alembic migration, define the corresponding SQLAlchemy model, and configure the photos relationship on the Animal model. This task establishes the data layer that all photo operations — uploading, listing, deleting, and designating a primary photo — will read from and write to. It is the prerequisite for every other photo-related task in this story and for the photo gallery endpoint in S03/T03.

## Why This Matters

The initial animal data model stored photo information as a single URL column on the animals table. That approach cannot represent multiple photos per animal, cannot track upload order, and cannot designate a primary photo independently from gallery photos. The animal_photos table solves all three by giving each photo its own row, with a foreign key to the animal it belongs to, a flag indicating whether it is the primary photo, and a timestamp that establishes the canonical display order for gallery photos.

Decoupling photos from the animals row also means that photo uploads and deletions do not touch the animals table at all, which avoids unnecessary row locking on the most heavily-read table in the database during photo management operations.

## Context

The animal_photos table is referenced by the S03/T01 detail endpoint (which joins photos into the animal detail response), by the S03/T03 photo gallery endpoint (which queries photos independently), and by the S04/T02 upload endpoint (which inserts new rows). All three of those tasks depend on this migration being applied before they can be tested with real data.

The AnimalPhoto SQLAlchemy model lives in src/models/animal_photo.py and follows the same pattern as the Animal model: it uses the declarative base from src/database/base.py and declares all columns with explicit types. The photos relationship on the Animal model uses a lazy loading configuration of selectin by default, so that any query that loads an Animal instance will automatically include its photos list without requiring a second query when the photos attribute is accessed.

## Implementation Steps

### Step 1: Create the Alembic Migration

In the alembic/versions directory, create a new migration file with a descriptive name such as create_animal_photos_table. The migration's upgrade function creates a table named animal_photos with the following columns: an id column as a serial integer primary key, an animal_id column as an integer with a foreign key constraint referencing the animals table's id column and a cascade delete rule so that deleting an animal automatically deletes all its photos, a url column as a non-nullable text string containing the path or fully qualified URL to the photo file, an is_primary column as a non-nullable boolean defaulting to false, and a created_at column as a timestamp with timezone defaulting to the current time at the database server.

The migration also creates a partial unique index on the pair of animal_id and is_primary where is_primary is true. This index enforces the constraint that at most one photo per animal can have is_primary set to true at the database level. Without this constraint, a bug in the application layer could silently create multiple primary photos for the same animal, causing non-deterministic ordering in the detail response. The migration's downgrade function drops the index first and then drops the table.

After writing the migration file, run it against the development database and confirm that the animal_photos table appears with the expected columns and constraints.

### Step 2: Define the AnimalPhoto SQLAlchemy Model

In src/models/animal_photo.py, define a SQLAlchemy declarative model class named AnimalPhoto that maps to the animal_photos table. The class declares the same columns as the migration: id as an integer primary key with autoincrement, animal_id as an integer foreign key to animals.id with ondelete set to CASCADE, url as a non-nullable string, is_primary as a non-nullable boolean with a server default of false, and created_at as a DateTime with timezone and a server default of the current timestamp.

The model does not need any methods beyond what SQLAlchemy provides. It does not need a relationship back to the Animal model — the relationship is defined on Animal, not on AnimalPhoto, to keep the photo model simple and avoid circular import issues.

### Step 3: Add the Photos Relationship to the Animal Model

In src/models/animal.py, import AnimalPhoto and add a photos relationship attribute to the Animal class. The relationship targets the AnimalPhoto model and uses the back_populates parameter to name the reverse attribute on AnimalPhoto as animal, though that reverse attribute is not used in practice. The relationship uses lazy set to selectin so that loading any Animal instance will issue a second SELECT to fetch all its photos immediately, making them available on the instance without requiring a subsequent query. The order_by parameter specifies that photos should be ordered by is_primary descending first and then by created_at ascending, so that when any code accesses animal.photos, the primary photo is always the first element in the list.

This ordering on the relationship definition ensures that the ordering is applied consistently by every piece of code that accesses photos through the relationship, without requiring each caller to specify the order independently.

### Step 4: Write Unit Tests for the Model

In tests/unit/test_models.py, add a unit test that constructs an Animal instance and two AnimalPhoto instances manually (without a database session) and verifies that the relationship attribute is accessible. This test does not require a database connection — it only checks that the relationship is defined correctly as a Python attribute on the Animal class and that AnimalPhoto instances can be appended to it.

In tests/integration/test_animal_photos_table.py, add an integration test that uses the test database session to create an animal, insert two photo rows with different is_primary values, and verify that querying the animal with the photos relationship loaded returns both photos with the primary photo appearing first. A second integration test verifies that deleting the animal cascades to delete its photo rows.

## Acceptance Criteria

- The Alembic migration applies cleanly without errors in both upgrade and downgrade directions
- The animal_photos table exists with columns id, animal_id, url, is_primary, and created_at
- The partial unique index on animal_id where is_primary is true exists and prevents inserting a second primary photo for the same animal
- The AnimalPhoto SQLAlchemy model maps to the animal_photos table and all columns are correctly typed
- The Animal model has a photos relationship that returns photos ordered by is_primary descending and created_at ascending
- The cascade delete rule causes animal photo rows to be deleted when the parent animal is deleted
- Integration tests confirm the ordering and cascade behavior

## Common Issues and Solutions

If the partial unique index constraint is violated during testing, verify that the test setup does not insert two rows with is_primary equal to true for the same animal. The correct approach when changing the primary photo is to update the existing primary row to set is_primary to false before inserting or updating the new primary row. The application service layer is responsible for this two-step update, not the database constraint — the constraint only catches bugs where the service layer fails to clear the old primary flag.

If the photos relationship returns an empty list for an animal that has photos in the database, verify that the selectin lazy loading strategy is configured on the relationship and that the query was executed within an open AsyncSession. With async SQLAlchemy, if the session is closed before the relationship is accessed, the selectin load will not fire and the collection will appear empty.

If the cascade delete is not removing photo rows when an animal is deleted, verify that the foreign key column on animal_photos declares ondelete equal to CASCADE at the SQLAlchemy level and that the database-level constraint also specifies ON DELETE CASCADE. SQLAlchemy's cascade parameter on the relationship does not generate the SQL ON DELETE CASCADE clause — that must be set separately on the Column definition.

## Related Tasks

- S01/T01: Animal model — the parent table this migration references via foreign key
- S03/T01: Animal detail endpoint — queries photos via the relationship
- S03/T03: Photo gallery endpoint — queries photos directly from animal_photos
- S04/T02: Photo upload endpoint — inserts rows into animal_photos
