---
epic: EPIC-1
story: S03
task: T03
title: Define Animal Photo Gallery Endpoint
status: pending
effort_hours: 2
priority: medium
dependencies:
  - S03/T01-create-detail-page-component
  - S03/T02-display-animal-information
  - S04/T01-configure-supabase-storage-for-animal-photos
---

## Overview

Define the FastAPI endpoint that returns the ordered list of photos for a specific animal. While the animal detail endpoint (T01) already includes a photos list embedded in the AnimalDetailResponse, this separate endpoint allows clients to fetch or refresh the photo list independently — for example, if a frontend wants to implement a lazy-loading gallery that fetches photos only when the user scrolls to the photo section, or if an admin interface wants to reload the photo list after uploading a new photo without refetching the entire animal record.

## Why This Matters

Separating the photo list endpoint from the animal detail endpoint follows the principle that resources should be independently addressable. The animal record and its photos are separate concerns: the animal record changes when staff update medical information or adoption status, while the photo list changes when volunteers upload new photos or designate a different primary photo. Clients that are subscribed to or caching the detail endpoint should not need to invalidate their cached animal record every time a photo is added. The dedicated photo endpoint allows targeted cache invalidation.

## Context

The animal_photos table, defined in S04/T01, stores one row per photo per animal. Each row contains the animal_id foreign key, the photo URL or storage path, a boolean is_primary flag indicating whether this photo should be displayed as the main photo in the catalog and at the top of the detail page, and timestamps. The photo endpoint returns these rows ordered by is_primary descending and then by created_at ascending, so the primary photo always appears first in the list.

The maximum number of photos per animal is not enforced at the database level but is documented here for clarity: shelters typically upload between one and six photos per animal, and the frontend gallery implementation is designed around displaying up to six thumbnails. The photo endpoint returns all photos without a hard limit, so if a shelter uploads more than six photos the client receives all of them and is responsible for capping the gallery display.

## Implementation Steps

### Step 1: Define the Route Handler

In src/routers/animals.py, add a route at GET /animals/{id}/photos with a response model of a list of AnimalPhotoResponse objects. The route handler accepts an integer id path parameter and a SQLAlchemy AsyncSession. It first verifies that the animal with the given id exists by querying the animals table — if no animal exists, it raises a 404 HTTPException. It then queries the animal_photos table for all rows where animal_id matches the given id, orders them by is_primary descending and created_at ascending, and returns the resulting list.

Returning a 404 when the animal does not exist is important because it distinguishes between an animal with no photos (which returns 200 with an empty list) and an animal that does not exist at all (which returns 404). A client that receives an empty list knows the animal exists but has no photos yet — perhaps a new intake that has not been photographed. A client that receives a 404 knows the animal ID is invalid.

### Step 2: Handle the Empty Photo List

When the animal exists but has no associated photos, the endpoint returns a 200 response with an empty JSON array. This is the expected state for newly created animals before S04's photo upload infrastructure is used. The frontend is responsible for showing a placeholder image when the photos list is empty — this is documented in the AnimalDetailResponse schema (S03/T02), where primary_photo_url is None when no photos exist.

### Step 3: Define the Photo Ordering Service Function

In src/services/animal_service.py, define a function named get_animal_photos that accepts a SQLAlchemy AsyncSession and an integer animal_id and returns a list of AnimalPhoto model instances ordered by is_primary descending and created_at ascending. The function queries the animal_photos table directly without joining to the animals table — the route handler is responsible for verifying animal existence before calling this function.

This separation keeps the service function narrowly focused on the photo retrieval logic and makes it independently testable with a mock session that returns a pre-constructed list of photo instances.

### Step 4: Add HTTP Caching Headers

The photo endpoint is public and benefits from aggressive caching since photos do not change frequently. Add a Cache-Control header with max-age set to 300 seconds (five minutes) for the photo list response. When new photos are uploaded via the admin interface, the cache will expire naturally, or the frontend can implement an explicit cache bust by appending a timestamp query parameter that causes the browser to treat the URL as new.

### Step 5: Write Integration Tests

In tests/integration/test_animals.py, add integration tests for the photo gallery endpoint. The test for the empty photo state creates an animal using the animal fixture and sends a GET request to /animals/{animal.id}/photos. The response should have status 200 and the body should be an empty JSON array, because no photos have been inserted for the test animal.

The test for the not-found case sends a GET request to /animals/NONEXISTENT_ANIMAL_ID/photos and verifies that the response status is 404.

Once the animal_photos table exists (after S04/T01 is implemented), an additional integration test should create an animal and insert two photo rows — one with is_primary equal to True and one with is_primary equal to False — and verify that the photo endpoint returns both photos with the primary photo appearing first in the list regardless of insertion order.

## Acceptance Criteria

- The GET /animals/{id}/photos endpoint returns a 200 response with a list of AnimalPhotoResponse objects when the animal exists
- The endpoint returns an empty list when the animal exists but has no photos
- The endpoint returns a 404 when the animal does not exist
- Photos are ordered with is_primary equal to True first, then by created_at ascending
- The response includes a Cache-Control header with max-age 300
- Integration tests cover the empty-photos case and the not-found case

## Common Issues and Solutions

If the photo endpoint returns a 200 with an empty list for an animal that has photos, the query may be filtering on the wrong column or using the wrong foreign key. Verify that the query filters animal_photos rows by animal_id and not by id (the photo's own primary key). A common mistake when constructing the query is accidentally filtering on the photos table's own primary key column, which shares the name id with the path parameter.

If the primary photo is not appearing first in the response list, verify that the order_by clause specifies is_primary in descending order. SQLAlchemy's default sort direction is ascending, and ascending order on a boolean column in PostgreSQL places False before True, which is the opposite of the intended behavior.

If the photo endpoint returns a 404 for all requests even when the animal exists, verify that the existence check queries the animals table and not the animal_photos table. An animal with no photos does not have any rows in animal_photos, so checking for the animal's existence in animal_photos would incorrectly return a 404 for animals that simply have no photos yet.

## Related Tasks

- S03/T01: Detail endpoint — embeds photo list using the same ordering logic
- S03/T02: AnimalPhotoResponse schema — the response model this endpoint returns as a list
- S04/T01: Animal photo storage — creates the AnimalPhoto model and animal_photos table that this endpoint queries
