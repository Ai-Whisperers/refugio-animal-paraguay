---
story: S1
epic: EPIC-82
ticket: RAP-551
title: "CMS content model and API"
status: ready
points: 5
priority: P0
track: Backend
sprint: 13
version: V1
created: 2026-03-27T20:00:00
---

# S1: CMS content model and API

## Story
As a **staff member**, I want **a database model for managing content blocks** so that **content can be edited independently of code**.

## Description
Create the foundational ContentBlock model and API endpoints to manage reusable content blocks used throughout the application. Content blocks are keyed by page/section identifiers and support multiple languages.

## Acceptance Criteria
- [ ] ContentBlock model created with fields: id (UUID), page_key (enum: home_hero, home_stats, home_team, home_testimonials, about_history, about_team, volunteer_activities, foster_requirements), content (JSON), language (enum: es, en), is_published (bool), updated_by (FK to User), updated_at (datetime), created_at (datetime)
- [ ] Database migration written and tested
- [ ] GET /api/content/blocks endpoint returns all content blocks with pagination (50 per page)
- [ ] GET /api/content/blocks/{page_key} endpoint returns blocks for specific page key, supporting ?lang=es|en parameter
- [ ] POST /api/admin/content/blocks endpoint creates new content block (auth: admin/editor role required)
- [ ] PUT /api/admin/content/blocks/{id} endpoint updates content block
- [ ] DELETE /api/admin/content/blocks/{id} endpoint deletes content block (soft delete recommended)
- [ ] Migration script seeds content blocks with current hardcoded data from strings.ts (creating both es and en versions where applicable)
- [ ] API returns structured error responses with appropriate HTTP status codes (400 for validation, 403 for auth, 404 for not found)
- [ ] Unit tests cover: create, read, update, delete, language filtering, pagination
- [ ] Database indexes created on page_key and language for query performance

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage)
- [ ] Integration test for CRUD operations
- [ ] Migration tested in staging
- [ ] Deployed to staging and verified
- [ ] API documented in OpenAPI/Swagger

## Technical Notes
- Use SQLAlchemy ORM for model definition
- Implement proper enum types for page_key and language
- Add database constraints: unique(page_key, language)
- Use JSON type for content field to support flexible schemas
- Implement soft delete with is_deleted flag and filter in queries
- Add audit trail: track who updated and when

## Story Points: 5
