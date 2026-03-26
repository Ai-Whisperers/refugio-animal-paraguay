---
epic: EPIC-1
story: S02
task: T01
title: Define FastAPI Catalog Endpoint and Public Animal Listing API
status: pending
effort_hours: 3
priority: high
dependencies:
  - S01/T01-define-supabase-schema-for-animals-table
---

## Overview

Implement the public-facing FastAPI endpoint that returns a paginated, filterable list of available animals for the catalog page. This endpoint is the primary data source for the adoption catalog — it is called by every visitor who browses the shelter's available animals. The frontend stack is TBD, so this task focuses on defining and implementing the backend API contract that any future frontend will consume.

## Why This Matters

The catalog endpoint is the highest-traffic route in the entire system. Defining it correctly now — with the right pagination contract, filter parameters, response shape, and caching headers — prevents breaking changes once a frontend is built against it. Every design decision made here propagates forward: the query parameter names become URL patterns that appear in SEO-indexed pages, the response shape becomes the TypeScript or other-language interface that frontend developers work against, and the sort order becomes the expected behavior that adopters experience.

## Context

The endpoint is public — no authentication required. It only returns animals with status equal to available, so animals in reserved, adopted, medical_hold, or deceased status are never exposed to the public catalog. Animals with is_featured equal to True appear at the top of the list before the sort order is applied to the remaining records. The endpoint lives in a router file at src/routers/animals.py and is registered on the FastAPI application in src/main.py.

## Implementation Steps

### Step 1: Define the Catalog Query Parameters

The GET /animals endpoint accepts the following optional query parameters. The species parameter accepts a string value matching one of the AnimalSpecies enum values and filters results to a single species. The gender parameter accepts a string matching AnimalGender and filters to one gender. The age_group parameter accepts one of four string values — puppy (under 12 months), young (12 to 36 months), adult (36 to 96 months), senior (over 96 months) — and translates the age group label into a range filter on the approximate_age_months column. The page parameter accepts a positive integer defaulting to 1 and controls which page of results is returned. The page_size parameter accepts a positive integer between 1 and 50, defaulting to 12, and controls how many records appear per page.

These parameters are declared as FastAPI Query dependencies in the route handler function signature. FastAPI validates the types automatically and returns a 422 Unprocessable Entity response if a parameter value cannot be parsed to the declared type. Add explicit validation constraints using Query(ge=1) for page and Query(ge=1, le=50) for page_size.

### Step 2: Implement the SQLAlchemy Query

The route handler function is defined as an async function in src/routers/animals.py and accepts a SQLAlchemy AsyncSession via the database dependency. The query starts by selecting all columns from the Animal model and filtering for status equal to AnimalStatus.available.

Each optional filter is applied conditionally. If the species parameter is present, add a where clause filtering species to the given value. If the gender parameter is present, add a where clause filtering gender to the given value. If the age_group parameter is present, translate it to a range filter on approximate_age_months: puppy translates to approximate_age_months less than 12, young to between 12 and 36, adult to between 36 and 96, and senior to greater than or equal to 96.

The sort order is applied last: featured animals first (order by is_featured descending, so True sorts before False), then by created_at descending (most recently added animals appear first within each featured group).

Pagination uses SQLAlchemy's offset and limit modifiers. The offset is calculated as page minus one multiplied by page_size. The limit is page_size. A separate count query runs against the same filter conditions but without offset and limit, returning the total number of matching records. This count is needed by the frontend to calculate total pages and display the result count. Use SQLAlchemy's select(func.count()) subquery pattern to run the count efficiently as a single additional query.

### Step 3: Define the Response Schema

In src/schemas/animal.py, define an AnimalSummaryResponse Pydantic v2 model that contains only the fields needed for the catalog list view: id, name, species, breed, gender, approximate_age_months, status, is_featured, and the primary photo URL (a field that references the first photo from the animal's photo relationship, or None if no photos exist). This is a smaller schema than the full AnimalResponse used on the detail page — returning only necessary fields reduces response payload size for the catalog endpoint, which may return up to 50 records per page.

Also define a PaginatedAnimalsResponse Pydantic v2 model that wraps the list response with pagination metadata: a field named animals containing a list of AnimalSummaryResponse instances, a total_count integer, a page integer, a page_size integer, and a total_pages integer calculated as the ceiling of total_count divided by page_size.

### Step 4: Define the Route Handler

In src/routers/animals.py, define the route at GET /animals with a response model of PaginatedAnimalsResponse. The route handler is an async function that receives the filter query parameters, the page and page_size parameters, and the database session dependency. It executes the SQLAlchemy queries, constructs the PaginatedAnimalsResponse instance from the results, and returns it.

The route handler includes a response_model_exclude_none parameter set to True so that null fields (like breed for animals of unknown breed) are omitted from the JSON response rather than serialized as null. This keeps the response compact for fields that are commonly absent.

Register the animals router in src/main.py with a prefix of /animals and the tag Animals.

### Step 5: Add HTTP Caching Headers

Since the catalog endpoint is public and the data changes infrequently, add HTTP caching headers to improve performance for repeated requests from the same browser or a CDN. Include a Cache-Control header with max-age set to 300 (five minutes) for requests without any filter parameters. For filtered requests, use a shorter max-age of 60 seconds. These headers are set on the FastAPI Response object passed as a dependency.

When an animal's status changes (for example, when a new animal is added or an existing animal is adopted), the cache will expire naturally after the max-age window. There is no explicit cache invalidation mechanism in this initial implementation.

## Acceptance Criteria

- The GET /animals endpoint returns a 200 response with a PaginatedAnimalsResponse body when called without parameters
- The endpoint returns only animals with status equal to available
- Featured animals appear before non-featured animals in the response
- The species and gender filter parameters reduce the result set correctly
- The age_group filter translates to the correct approximate_age_months range
- Pagination returns the correct slice of results for each page value
- The total_count field reflects the total matching records, not the count of records in the current page
- The endpoint returns a 422 response if page is less than 1 or page_size is greater than 50
- No authentication is required to call this endpoint
- Response includes Cache-Control headers with appropriate max-age values

## Common Issues and Solutions

If the count query returns a different number than expected, verify that the count query applies the same filter conditions as the data query. A common mistake is forgetting to apply the status filter to the count query when both queries are written separately.

If featured animals are not appearing first, verify that the order_by clause specifies descending order on is_featured. SQLAlchemy's default sort order is ascending, which would place False (featured equals False) before True (featured equals True) — the opposite of the intended behavior.

If the offset calculation is incorrect for page numbers greater than one, verify the formula uses page minus one as the multiplier rather than page directly. Page 1 should have offset 0, page 2 should have offset equal to page_size, and so on.

## Related Tasks

- S01/T01: Animal model definition — the SQLAlchemy model this endpoint queries
- S02/T02: Animal list query details — additional filtering and sorting behavior
- S02/T03: Pagination implementation — the pagination contract this endpoint follows
- S03/T01: Animal detail endpoint — the detail page URL that catalog cards link to
