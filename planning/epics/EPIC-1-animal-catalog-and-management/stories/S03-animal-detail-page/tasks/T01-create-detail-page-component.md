---
epic: EPIC-1
story: S03
task: T01
title: Define FastAPI Animal Detail Endpoint
status: pending
effort_hours: 2
priority: medium
dependencies:
  - S01/T01-define-supabase-schema-for-animals-table
  - S02/T01-create-catalog-page-layout
---

## Overview

Implement the public-facing FastAPI endpoint that returns the full record for a single animal, identified by its integer primary key. This endpoint is the data source for the animal detail page — the page a visitor reaches when they click on an animal card in the catalog and want to learn everything about that specific animal before deciding to submit an adoption request. The endpoint returns a detailed response schema that contains every field visible on the detail page, including all nullable fields omitted from the catalog summary.

## Why This Matters

The animal detail page is where adoption decisions are made. The endpoint must return a complete picture of the animal — description, vaccination status, neutering status, microchip number, intake date, and all other fields — so the frontend has everything it needs without making additional requests. The endpoint also establishes the HTTP 404 behavior for invalid or stale animal IDs: a user who bookmarked a detail page for an animal that was later removed from the system should receive a clear 404 response rather than a malformed page.

## Context

The endpoint is public — no authentication is required to view animal details. This is consistent with the catalog endpoint: the shelter wants potential adopters to be able to browse and research animals without creating an account. The endpoint lives in the same router file as the catalog endpoint, at src/routers/animals.py, and is registered on the FastAPI application in src/main.py with the same /animals prefix.

The path parameter is an integer, not a UUID, because the animals table uses an integer autoincrement primary key. The path is GET /animals/{id} where id is a positive integer. FastAPI validates the path parameter type automatically and returns a 422 Unprocessable Entity response if the id cannot be parsed as an integer.

## Implementation Steps

### Step 1: Define the Route Handler

In src/routers/animals.py, add a new route at GET /animals/{id} with a response model of AnimalDetailResponse. The route handler is an async function that accepts an integer id path parameter and a SQLAlchemy AsyncSession via the database dependency. The handler queries the animals table for a record matching the given id. If no record is found, the handler raises an HTTPException with status code 404 and a detail message indicating the animal was not found. If a record is found, the handler constructs and returns an AnimalDetailResponse instance.

The query includes a left outer join to the animal_photos table so that the response includes the list of photos associated with the animal. The photos are ordered by is_primary descending and then by created_at ascending, placing the primary photo first in the list. If no photos exist, the photos field of the response is an empty list.

### Step 2: Define the Not-Found Behavior

When the requested animal id does not exist in the database, the endpoint returns a 404 response with a JSON body containing a detail field. The status code is 404 because the resource genuinely does not exist — this is different from the catalog empty-state behavior, where the catalog resource exists but has zero results for a filter combination. A 404 on the detail endpoint tells the frontend to display a not-found page rather than an empty detail view.

The 404 also applies when the animal exists but has a status other than available, if the business rules call for hiding non-available animals from the public. In the initial implementation, the detail endpoint returns all animals regardless of status, so a staff member who shares a direct link to an animal that is in medical_hold status will still see the detail page. The status field in the response tells the frontend whether to show or suppress the adoption request call-to-action button — the backend does not make that presentation decision.

### Step 3: Add HTTP Caching Headers

The animal detail endpoint is public and the data for a specific animal changes infrequently within a short time window. Add a Cache-Control header with max-age set to 60 seconds to allow browser and CDN caching of individual animal pages. This is a shorter max-age than the catalog page because an animal's status can change — for example, from available to reserved — and stale detail pages that still show the adoption CTA for a reserved animal would be misleading. Sixty seconds balances caching efficiency with freshness.

### Step 4: Write Integration Tests

In tests/integration/test_animals.py, add integration tests for the detail endpoint. The test for a successful fetch creates an animal using the animal fixture, sends a GET request to /animals/{animal.id}, and verifies that the response status is 200 and that the response body contains the expected id, name, and status fields matching the created animal.

The test for a not-found response sends a GET request to /animals/NONEXISTENT_ANIMAL_ID (using the 999999 constant from conftest.py) and verifies that the response status is 404.

The test for a non-available animal creates an animal with status medical_hold using the unavailable_animal fixture, fetches it by id, and verifies that the response status is 200 and that the status field in the response body equals medical_hold. This test documents that the detail endpoint does not filter by status — it returns all animals that exist in the database.

## Acceptance Criteria

- The GET /animals/{id} endpoint returns a 200 response with an AnimalDetailResponse body when the animal exists
- The endpoint returns a 404 response when the requested id does not exist
- The endpoint returns all animals regardless of status — status filtering is a frontend responsibility
- The response includes a photos list, ordered with the primary photo first
- No authentication is required to call this endpoint
- Response includes a Cache-Control header with max-age 60
- A non-integer id path parameter results in a 422 response from FastAPI's automatic validation

## Common Issues and Solutions

If the 404 response is not being returned for a missing animal, verify that the handler checks whether the SQLAlchemy query result is None before constructing the response. A scalar_one_or_none() call returns None when no matching record exists, but scalar_one() raises a NoResultFound exception that propagates as a 500 if not caught.

If the photos list is not included in the response, verify that the query performs a left outer join to the animal_photos table and that the AnimalDetailResponse schema includes a photos field typed as a list of AnimalPhotoResponse objects.

If the photos list is empty for an animal that has photos, verify that the animal_photos table exists and that the foreign key join is on the correct column. During early development before the photo upload infrastructure is built in S04, the photos list will always be empty because no photos have been inserted — this is expected behavior.

## Related Tasks

- S01/T01: Animal model definition — the SQLAlchemy model this endpoint queries
- S02/T01: Catalog endpoint — shares the same router file and database dependency
- S03/T02: AnimalDetailResponse schema — the full response shape this endpoint returns
- S03/T03: Photo gallery endpoint — the separate /animals/{id}/photos route for lazy photo loading
- S04/T01: Animal photo storage — the infrastructure that populates the photos list
