---
epic: EPIC-1
story: S02
task: T03
title: Implement Pagination Contract and Filter-Preserving URL Pattern
status: pending
effort_hours: 2
priority: medium
dependencies:
  - S02/T01-create-catalog-page-layout
  - S02/T02-implement-animal-list-component
---

## Overview

Define the canonical pagination contract for the animals catalog endpoint and document the URL query parameter pattern that the frontend must follow to implement filter-preserving page navigation. This task also adds integration tests that verify the pagination behavior across multiple pages, the total_pages calculation, and the boundary conditions at the first and last page.

## Why This Matters

Pagination is the contract between the backend API and every client that consumes it. If the pagination field names, the page numbering convention (1-based versus 0-based), or the total_pages calculation formula change after the frontend is built, all frontend pagination logic breaks. Defining this contract explicitly now and backing it with tests prevents silent drift. The URL pattern for filter-preserving pagination is also important: when a user is on page 3 of a filtered species search and clicks to page 4, all filter parameters must be preserved in the URL so that the next page continues the filtered search rather than starting a new unfiltered search.

## Context

The animals catalog uses 1-based page numbering: the first page is page 1, not page 0. The total_pages field is the ceiling of total_count divided by page_size. A catalog with 25 animals and a page_size of 12 has total_pages of 3 (pages 12, 12, and 1 animal). The frontend should not request a page beyond total_pages — doing so returns an empty list because the offset exceeds the total record count, but does not return an error.

The URL pattern is described here for the future frontend: filter parameters use Spanish names for SEO-friendly URLs (especie, genero, grupo_edad, pagina) that appear in search engine indexes. The backend accepts English internal names as query parameters (species, gender, age_group, page) and maps them to the Spanish display names in documentation and URL scheme guidance. The API parameter names are the canonical names; the Spanish URL scheme is for the frontend routing layer.

## Implementation Steps

### Step 1: Define the Pagination Response Fields

The PaginatedAnimalsResponse schema (defined in T01 and implemented in T02) contains five pagination fields. The page field echoes back the page number that was requested. The page_size field echoes back the page_size value that was used. The total_count field contains the total number of animals matching the current filter criteria across all pages, not just the current page. The total_pages field contains the ceiling of total_count divided by page_size, calculated as an integer. The animals field contains the list of AnimalSummaryResponse objects for the current page.

The reason for echoing page and page_size back in the response (rather than requiring the client to track these from its request) is to allow caching layers and logging systems to understand the context of a response purely from the response body, without needing to correlate it with the request.

### Step 2: Define Page Boundary Behavior

If page equals 1 and total_count is zero, the response returns an empty animals list, total_count of zero, and total_pages of zero. This is the empty catalog state described in T02.

If page is greater than total_pages (the client requested a page beyond the last page of results), the response returns an empty animals list with the correct total_count and total_pages values. The response status code is 200, not 404. This behavior allows clients to handle stale pagination state gracefully — if a user bookmarks page 5 of a catalog and the shelter later has fewer animals, the bookmark loads a valid empty-page response rather than an error page.

If page_size is at its maximum value of 50 and the total result count is less than 50, the response returns all matching records in a single page with total_pages equal to 1.

### Step 3: Write Pagination Integration Tests

In tests/integration/test_animals.py, add integration tests for pagination behavior. Each test is marked with pytest.mark.integration and is async. All tests use the client fixture and db_session fixture from conftest.py.

The test for the first page of a multi-page catalog creates 15 animal records using the db_session fixture, then sends a GET request to /animals with page_size equal to 10. The response should have total_count equal to 15, total_pages equal to 2, and animals containing exactly 10 items.

The test for the second page sends GET /animals with page equal to 2 and page_size equal to 10. The response should contain 5 animals (the remaining records from the 15 total), total_count equal to 15, and total_pages equal to 2.

The test for a page beyond the last page sends GET /animals with page equal to 999. The response should have status code 200, total_count equal to the actual number of available animals in the database, and an empty animals list.

The test for filter-and-paginate sends GET /animals with species equal to dog and page_size equal to 5. The response should contain only dogs in the animals list, and total_count should reflect only the dog count, not the total animal count across all species. This test verifies that pagination and filtering are applied correctly together.

### Step 4: Document the Frontend URL Pattern

For the future frontend implementation, document the URL pattern that creates shareable, SEO-friendly catalog URLs. A user browsing dogs on page 2 should have a URL like /animales?especie=perro&pagina=2. When the user changes the filter to cats, the pagina parameter should reset to 1 (or be omitted, since page 1 is the default). When the user navigates to the next page, the especie parameter should be preserved.

The frontend routing layer is responsible for implementing this URL management. The backend API does not enforce URL patterns — it accepts its English query parameter names regardless of what URL the frontend uses to construct the request. The URL pattern described here is a frontend convention, not a backend requirement.

The page 1 URL should omit the pagina parameter entirely to produce a clean URL for the default state. This means the frontend must treat both the absence of pagina and pagina equal to 1 as equivalent, which the backend handles correctly (both map to page 1 in the query).

## Acceptance Criteria

- PaginatedAnimalsResponse contains page, page_size, total_count, total_pages, and animals fields
- A request for page 999 on a catalog with 15 animals returns status 200 with an empty animals list and total_count equal to 15
- A request for page 2 with page_size 10 on a catalog with 15 animals returns 5 animals, not 10
- total_pages is calculated as the ceiling of total_count divided by page_size, not as the floor
- Filter parameters and page parameter are independent: requesting page 2 with a species filter returns the second page of species-filtered results, not the second page of all animals
- Integration tests exist for multi-page catalog, second page, beyond-last-page, and filter-and-paginate scenarios
- The frontend URL pattern is documented with examples in prose

## Common Issues and Solutions

If total_pages is one less than expected (for example, 2 instead of 3 for 25 animals at page_size 12), the total_pages calculation is using integer floor division rather than ceiling division. In Python, ceiling division for non-negative integers is computed by adding page_size minus one to total_count before dividing, or by importing the math module and using math.ceil. Verify that the calculation handles the edge case of total_count equal to zero, which should produce total_pages equal to zero rather than division-by-zero error.

If a request for page 2 returns the same animals as page 1, the offset calculation is incorrect. Verify the offset formula: offset equals page minus one multiplied by page_size. For page 2 with page_size 10, offset should be 10, causing the query to skip the first 10 records.

If integration tests for pagination fail with isolation errors (animals from one test appearing in another test's count), the db_session fixture is not rolling back correctly between test functions. Verify the SAVEPOINT-based rollback pattern described in EPIC-0/S03/T01.

## Related Tasks

- S02/T01: Catalog endpoint definition — declares the query parameters this task documents
- S02/T02: Animal list query logic — the service function whose results this pagination wraps
- EPIC-0/S02/T03: pytest integration test module structure — the test file and fixtures pattern that this task's integration tests follow
