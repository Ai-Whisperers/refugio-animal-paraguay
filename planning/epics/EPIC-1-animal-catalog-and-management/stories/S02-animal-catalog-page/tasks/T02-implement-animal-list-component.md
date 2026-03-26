---
epic: EPIC-1
story: S02
task: T02
title: Implement Animal List Query Logic and Response Shaping
status: pending
effort_hours: 3
priority: high
dependencies:
  - S01/T01-define-supabase-schema-for-animals-table
  - S02/T01-create-catalog-page-layout
---

## Overview

Implement the SQLAlchemy query logic that powers the animal catalog list, including the empty-state response when no animals match the filter criteria, the response shape for each animal summary card, and the photo URL resolution logic. This task details the data layer behavior that T01 described at the route level, focusing on how the query is constructed, what the animal summary object looks like, and how the system handles edge cases like animals with no photos, animals with unknown breeds, and filter combinations that return zero results.

## Why This Matters

The catalog list is the entry point for almost every adoption journey in the system. Getting the query logic right — especially the filter combinations, sort stability, and empty-state handling — directly affects whether potential adopters find animals that match their household and whether staff trust the catalog as an accurate reflection of shelter inventory. Poorly shaped response data forces the frontend to perform defensive checks on every field, increasing frontend complexity and the likelihood of display bugs.

## Context

The frontend stack is TBD. This task documents the backend data layer in full so that when a frontend is chosen and built, the data contract is already defined and implemented. The animal summary response object described here is the canonical shape that all frontend implementations will consume from GET /animals. Changes to this shape after a frontend is deployed against it constitute a breaking change requiring a versioned API response.

## Implementation Steps

### Step 1: Define the SQLAlchemy Service Function

Extract the catalog query logic from the route handler into a dedicated service function in src/services/animal_service.py. The function is named get_animal_catalog and accepts a SQLAlchemy AsyncSession, an optional species string, an optional gender string, an optional age_group string, a page integer, and a page_size integer as arguments.

Separating the query logic from the route handler keeps the handler thin and makes the query logic independently testable with unit tests that pass a mock session, without needing to spin up the full FastAPI application. The service function returns a tuple of two values: the list of Animal model instances for the current page, and the integer total count of matching records.

### Step 2: Define the Animal Summary Response Shape

The AnimalSummaryResponse Pydantic schema describes each item in the catalog grid. Each item contains the following fields. The id field is an integer, the unique identifier used to construct the detail page URL. The name field is a string. The species field is an AnimalSpecies enum value serialized as a string. The breed field is a nullable string — many rescued animals have unknown breed, so this field is frequently None. The gender field is an AnimalGender enum value serialized as a string. The approximate_age_months field is a nullable integer. The is_featured field is a boolean. The primary_photo_url field is a nullable string containing a fully qualified URL or a relative path to the animal's primary photo. If the animal has no associated photos, this field is None, and the frontend is responsible for showing a placeholder image.

The primary_photo_url is resolved by joining the animal_photos table (described in S04) and selecting the URL of the first photo ordered by is_primary descending and then by created_at ascending. If no photo rows exist for the animal, the field is None. This join is performed in the SQLAlchemy query using a left outer join and a subquery that selects the single most-appropriate photo URL per animal.

### Step 3: Handle the Empty State

When the filter combination produces zero matching records, the catalog query returns an empty list. The total_count is zero. The route handler returns a valid PaginatedAnimalsResponse with animals equal to an empty list, total_count equal to zero, page equal to the requested page, page_size equal to the requested page_size, and total_pages equal to zero.

The route handler does not return a 404 in this case. A 404 indicates that the resource does not exist, but the catalog resource always exists — it may simply contain zero results for a given filter combination. The frontend interprets a total_count of zero as the signal to display the empty-state message inviting the user to adjust their filters.

### Step 4: Handle Photo URL Resolution Without the Photo Table

During the initial development phase before the animal_photos table and S04 are implemented, the primary_photo_url field will always be None because no photo infrastructure exists yet. The query still executes correctly — the left outer join on a non-existent or empty table returns None for all photo URL columns. The response schema handles this gracefully because primary_photo_url is declared as nullable.

Once S04 implements the photo upload and storage infrastructure, the left outer join will begin returning URLs for animals that have uploaded photos. No changes to this query or response schema are needed when S04 is complete — the schema already accommodates both states.

### Step 5: Write Unit Tests for the Query Logic

In tests/unit/test_animal_service.py, write unit tests for the get_animal_catalog function using a mock SQLAlchemy session. The test for the species filter verifies that when species equals dog, the resulting SQLAlchemy query includes a where clause that filters on species. The test for the age_group filter verifies that each of the four age group values translates to the correct approximate_age_months range. The test for the empty state verifies that a total_count of zero and an empty list are returned when the query finds no matching records. The test for sort order verifies that is_featured descending appears in the order_by clause of the generated query.

These unit tests run without a database connection by inspecting the SQLAlchemy query object before execution, verifying the clause structure rather than the query results. This makes the tests fast and independent of the test database state.

## Acceptance Criteria

- The get_animal_catalog service function exists in src/services/animal_service.py and accepts species, gender, age_group, page, and page_size parameters
- The function returns a tuple of a list of Animal instances and an integer total count
- AnimalSummaryResponse Pydantic schema is defined with all fields described above, including nullable primary_photo_url
- The route handler delegates to get_animal_catalog and constructs PaginatedAnimalsResponse from the returned tuple
- An empty result set returns a valid PaginatedAnimalsResponse with animals as an empty list and total_count as zero, not a 404
- Unit tests exist for species filter, age_group filter, empty state, and sort order
- The primary_photo_url field is None when no photos are associated with an animal

## Common Issues and Solutions

If the left outer join for photo URL resolution produces duplicate animal rows (one row per photo rather than one row per animal), the query is not limiting itself to a single photo per animal. Use a subquery or a DISTINCT ON clause to ensure one photo URL per animal. SQLAlchemy's subquery approach is generally cleaner: write a subquery that selects the single most appropriate photo URL keyed by animal_id, then left join that subquery to the main animals query.

If the age_group filter does not work for animals with None values in approximate_age_months, the range filter implicitly excludes null values in PostgreSQL comparison operators. This is the correct behavior — animals with unknown ages should not appear in age-filtered results. Document this behavior explicitly in the service function's docstring so frontend developers know to inform users that filtering by age may exclude some animals.

## Related Tasks

- S01/T01: Animal model definition — the SQLAlchemy model being queried
- S02/T01: Catalog endpoint definition — the route handler that calls this service function
- S02/T03: Pagination details — the pagination contract this service function's results feed into
- S04/T01: Animal photo storage — the photo infrastructure that populates primary_photo_url
