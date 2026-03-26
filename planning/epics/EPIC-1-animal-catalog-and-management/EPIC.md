---
epic: EPIC-1
title: Animal Catalog & Management
status: ready
created: 2026-03-25T17:13:26.725194
updated: 2026-03-25T17:13:26.725205
---

# EPIC-1: Animal Catalog & Management

## Overview

**Goal**: Build the authoritative data layer and public-facing catalog for every animal in the shelter's care, enabling adopters to discover animals and staff to manage records throughout each animal's stay.

**Why it matters**: The animal catalog is the foundational building block of the entire platform. Every other domain — adoptions, medical records, donations, volunteer tasks — references animal records. Without a well-designed, stable animal schema and management interface, none of the downstream features can be built reliably. The public-facing catalog is also the primary discovery surface for prospective adopters, including European donors who may sponsor specific animals.

**Target users**: Shelter staff and administrators who create and update animal records; prospective adopters and general visitors browsing for animals to adopt; volunteers who need context about the animals they are caring for; European sponsors who may follow a specific animal's journey.

---

## Scope

### In Scope

- PostgreSQL schema for the animals table including species, breed, age, weight, sex, health status, behavioral notes, intake date, and adoption eligibility status
- Animal status lifecycle management: intake, available, reserved, adopted, in foster care, on medical hold, and deceased — each with appropriate constraints and audit timestamps
- Staff-facing forms for creating and editing animal records, accessible through the admin interface built in EPIC-7
- Photo upload and management: multiple photos per animal stored in object storage, with one designated as the primary listing photo
- Public-facing catalog endpoint returning paginated, filterable animal listings without authentication
- Filtering capabilities: species (dog, cat, other), size category, age range, sex, and adoption eligibility status
- Full-text search against animal names and behavioral description text using PostgreSQL's native text search capabilities
- Animal detail page data: complete profile including all photos, full behavioral notes, known medical summary (suitable for public display), and current status
- Intake records tracking how and when the animal arrived at the shelter (street rescue, owner surrender, transfer from another organization)
- Soft deletion for records that must be retired without losing historical data

### Out of Scope

- Medical and veterinary records in detail (handled in EPIC-4; this epic captures only a brief health summary suitable for public display)
- Adoption application processing (handled in EPIC-2; this epic manages animal data only)
- Volunteer task assignments to specific animals (handled in EPIC-5)
- Public portal rendering and frontend presentation (handled in EPIC-11; this epic provides the API)
- Animal transfer workflows between shelters
- Lost-and-found or microchip registry features

---

## Stories

- **S01: Animal Data Model & Schema** — Design and migrate the complete PostgreSQL schema for animals, including all required fields, status enum types, intake records, and appropriate indexes for the filtering and search queries that the catalog will issue. Write Alembic migrations with rollback capability.

- **S02: Animal Catalog Page** — Implement the FastAPI endpoint that returns a paginated list of adoptable animals with filtering by species, size, age range, sex, and status. Include total count in the response so the frontend can render pagination controls. This endpoint is public and requires no authentication.

- **S03: Animal Detail Page** — Implement the FastAPI endpoint that returns the complete profile for a single animal by its UUID identifier, including all photos, full behavioral notes, and current status. Return 404 for non-existent animals and for animals in states that should not be publicly visible (deceased, in medical hold).

- **S04: Photo Upload & Management** — Implement staff-facing endpoints for uploading, reordering, and deleting animal photos. Photos are stored in an S3-compatible object store. Each animal can have up to ten photos. The primary photo designation determines which image appears in catalog listings.

- **S05: Advanced Search & Filters** — Implement full-text search over animal names and descriptions using PostgreSQL's tsvector indexing. Ensure search and filter parameters can be combined in a single query. Document the query performance characteristics and add appropriate indexes.

---

## Dependencies

**Depends on**:
- EPIC-10 (Authentication & User Accounts) — staff create and edit records using their authenticated staff or admin role; the catalog endpoint itself is public but write operations require a valid JWT token with the staff or admin role
- Object storage provisioning (EPIC-9, S03) — photo uploads require a configured S3-compatible bucket

**Blocks**:
- EPIC-2 (Adoption Process & Workflows) — adoption applications reference animal records and rely on the status lifecycle defined here
- EPIC-4 (Medical Records) — medical records are foreign-keyed to animal IDs established by this epic
- EPIC-5 (Volunteer Management) — volunteer task assignments reference specific animals
- EPIC-7 (Admin Dashboards) — the admin activity feed and reporting endpoints query animal data
- EPIC-11 (Public Portal) — the public-facing website consumes the catalog and detail endpoints defined here

---

## Success Metrics

- All adoptable animals are visible in the public catalog within five minutes of a staff member marking them as available
- Catalog API endpoint returns results in under 200 milliseconds at the p95 percentile for pages of 20 animals including photo URLs
- Full-text search returns relevant results for common query patterns (breed name, color, behavioral trait) with no query taking more than 500 milliseconds
- Zero data loss for any animal record — soft deletion preserves all historical records
- Staff can create a complete animal record including photo upload in under five minutes of real-world usage

---

## Risk Factors

- **Photo storage cost and size**: Animal photos can be large. Without resize-on-upload, storage costs can grow unexpectedly and catalog page load times will suffer. Mitigation: define maximum upload size and generate thumbnail variants at upload time.
- **Status transition correctness**: Invalid status transitions (for example, moving a deceased animal back to available) can corrupt downstream reporting. Mitigation: enforce status transitions via application-layer validation rather than relying on database constraints alone, and test all valid and invalid transitions explicitly.
- **Search relevance**: Basic PostgreSQL full-text search may return unexpected results for Spanish-language descriptions with accented characters. Mitigation: configure the text search dictionary for Spanish and test with realistic Spanish query strings.

---

## Effort & Priority

**Priority**: Highest. This is the prerequisite for the majority of the platform's functionality.

**Estimated effort**: Two sprints. The data model and catalog endpoint (S01, S02) form the critical path and should be completed first. Photo management (S04) and advanced search (S05) can be delivered in a second sprint without blocking adoption workflows.
