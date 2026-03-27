# RAP-105 Plan

## Objective
Build a staff-facing animal list page with search, sort, and pagination in the admin dashboard.

## Description
Staff need a way to view and manage animals through the admin UI. This page provides a paginated table of all animals with search-by-name, column sorting, and species/status filtering.

## Acceptance Criteria
- [x] Paginated table of all animals with name, species, status, intake date
- [x] Search bar filters by animal name in real-time
- [x] Column headers sort ascending/descending
- [x] Species and status dropdown filters
- [x] Empty state for no results
- [x] Error state with retry button
- [x] Loading state with spinner
- [x] Navigation from dashboard to animals page

## Complexity Assessment
**Track**: Simple Fix — 2 files, well-understood pattern

## Approach
Create admin/animals/page.tsx using existing API client and auth patterns. Client-side search/sort/pagination over fetched data.

## Dependencies
- Animals API (GET /animals) — already exists
- Admin layout and auth — already exists
