---
epic: EPIC-1
story: S03
task: T02
title: Define AnimalDetailResponse Schema and Service Function
status: pending
effort_hours: 2
priority: medium
dependencies:
  - S01/T01-define-supabase-schema-for-animals-table
  - S03/T01-create-detail-page-component
---

## Overview

Define the full AnimalDetailResponse Pydantic v2 schema that represents every piece of information available about a single animal, and implement the SQLAlchemy service function that retrieves the animal record with its associated photos. The detail response is deliberately wider than the catalog summary: while AnimalSummaryResponse contains only the fields needed to render a catalog card, AnimalDetailResponse contains all fields that a visitor would want to see when deciding whether to adopt an animal.

## Why This Matters

The detail response schema is the contract between the backend and every client that renders an animal detail page. All fields that the detail page needs — the animal's description, vaccination and neutering status, intake date, microchip number, weight, and photo list — must be present in this schema. If a field is added to the page later but is not included in this schema, the frontend will have to either call a second endpoint or wait for a breaking schema change. Defining the full schema now prevents both outcomes. The schema also communicates which fields are nullable, which tells the frontend exactly which fields it must handle gracefully by showing placeholder text or omitting the display element.

## Context

The animals table stores the complete record. The animal_photos table stores zero or more photos per animal. The detail response assembles both into a single response object. The photos field of the detail response is populated by the same left outer join used in the catalog endpoint to resolve primary_photo_url, but in the detail case, all photos are returned as a list of AnimalPhotoResponse objects rather than just the primary URL.

The status field in the response tells the frontend whether to show the adoption request call-to-action. When status equals available, the frontend should display a button that leads to the adoption request flow defined in EPIC-2. When status equals reserved, the frontend should display a message indicating that an adoption process is already in progress. When status equals medical_hold, adopted, or deceased, the frontend should suppress the call-to-action entirely. The backend does not make this presentation decision — it returns the status and leaves the rendering choice to the frontend.

## Implementation Steps

### Step 1: Define the AnimalPhotoResponse Schema

In src/schemas/animal.py, define a Pydantic v2 model named AnimalPhotoResponse that represents one photo from the animal_photos table. The schema contains the id field as an integer, the url field as a string containing the fully qualified or relative path to the photo file, the is_primary field as a boolean indicating whether this is the designated primary photo, and the created_at field as a datetime. The model uses ConfigDict with from_attributes set to True to enable construction from SQLAlchemy model instances.

### Step 2: Define the AnimalDetailResponse Schema

In src/schemas/animal.py, define a Pydantic v2 model named AnimalDetailResponse that extends the base animal fields with the full set of columns. The schema contains the following fields: id as an integer, name as a string, species as the AnimalSpecies enum serialized as a string, breed as a nullable string, gender as the AnimalGender enum serialized as a string, approximate_age_months as a nullable integer, weight_kg as a nullable Decimal, status as the AnimalStatus enum serialized as a string, description as a nullable string, is_featured as a boolean, is_vaccinated as a nullable boolean, is_neutered as a nullable boolean, microchip_number as a nullable string, intake_date as a nullable date, shelter_id as an integer, created_at as a datetime, updated_at as a datetime, and photos as a list of AnimalPhotoResponse instances.

The distinction between nullable booleans for is_vaccinated and is_neutered and a plain false boolean is significant: None means the information is not recorded or not applicable (as is common for rabbits and birds where these fields are not routinely tracked by the shelter), while False means the animal has been explicitly recorded as not vaccinated or not neutered. The frontend can use this distinction to display different messages to potential adopters — for example, showing "vaccination status unknown" versus "not vaccinated."

The model uses ConfigDict with from_attributes set to True and populate_by_name set to True.

### Step 3: Define the Service Function

In src/services/animal_service.py, define a function named get_animal_by_id that accepts a SQLAlchemy AsyncSession and an integer animal_id and returns either an Animal model instance with its associated photos loaded, or None if no matching record exists.

The function constructs a SQLAlchemy select statement that queries the Animal model filtered by the given id. It performs a selectinload or joinedload of the animal's photos relationship so that the photos are available on the returned Animal instance without requiring additional queries from the route handler. The function uses scalar_one_or_none() to return either the single matching Animal instance or None when no record exists.

The route handler calls get_animal_by_id and raises a 404 HTTPException when the result is None. The route handler then constructs AnimalDetailResponse from the returned Animal instance using Pydantic's model_validate method with from_attributes enabled.

### Step 4: Write Unit Tests for the Service Function

In tests/unit/test_animal_service.py, add unit tests for the get_animal_by_id function. The test for a successful fetch creates a mock session that returns a single Animal instance when queried and verifies that the function returns that instance rather than None. The test for a missing animal creates a mock session that returns None from scalar_one_or_none and verifies that the function returns None.

These unit tests do not require a database connection — they use a mock AsyncSession that returns pre-constructed results, keeping them fast and deterministic.

## Acceptance Criteria

- AnimalPhotoResponse schema is defined with id, url, is_primary, and created_at fields
- AnimalDetailResponse schema is defined with all fields described above, including nullable fields
- The photos field in AnimalDetailResponse is typed as a list of AnimalPhotoResponse, not a list of strings
- is_vaccinated and is_neutered are nullable booleans, not plain booleans, to distinguish unknown from false
- The get_animal_by_id service function returns None when no matching record exists
- The route handler returns a 404 when the service function returns None
- The route handler constructs AnimalDetailResponse from the Animal instance using Pydantic's from_attributes behavior
- Unit tests exist for the found and not-found cases

## Common Issues and Solutions

If the photos field in the response is always an empty list even when photos exist in the database, the relationship loading strategy may not be configured correctly. Verify that the Animal SQLAlchemy model declares a photos relationship to the AnimalPhoto model and that the service function uses selectinload or joinedload to eagerly load the photos relationship before the session is closed. If the session is closed before the photos are accessed, SQLAlchemy will raise an error or return an empty collection depending on whether lazy loading is configured.

If is_vaccinated and is_neutered are being serialized as false instead of null when the database contains NULL, verify that the Pydantic field type is declared as Optional[bool] or bool | None rather than bool. A plain bool type will coerce None to False during validation.

If the created_at and updated_at fields are being serialized as strings instead of ISO 8601 datetime strings, verify that the Pydantic model uses datetime as the field type and that Pydantic v2's default JSON serialization is not being bypassed. Pydantic v2 serializes datetime values as ISO 8601 strings by default.

## Related Tasks

- S01/T01: Animal model definition — the SQLAlchemy model whose fields this schema mirrors
- S03/T01: Detail endpoint route handler — calls the service function defined here
- S03/T03: Photo gallery endpoint — the separate endpoint for photo-only requests
- S04/T01: Animal photo storage — creates the AnimalPhoto model and animal_photos table
