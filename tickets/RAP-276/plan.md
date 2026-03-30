# RAP-276 Plan

## Objective
Allow authenticated adopters (and staff) to upload supporting documents (ID, proof of residence, etc.) linked to their adopter profile or adoption request.

## Description
Part of EPIC-56: Adopter Portal. Adopters need to submit identification documents, proof of residence, and other required paperwork to support their adoption applications. Staff need to view these documents as part of reviewing applications.

## Acceptance Criteria
- [ ] Authenticated adopter can upload a document (PDF, JPG, PNG) up to 10MB
- [ ] Adopter can list their own uploaded documents
- [ ] Adopter can delete their own document
- [ ] Staff can view documents for any adopter
- [ ] Documents are linked to adopter profile by email match
- [ ] Documents stored with metadata (filename, type, size, content type)
- [ ] Unit and integration tests passing with 80%+ coverage
- [ ] API endpoints documented in OpenAPI schema

## Complexity Assessment
**Track**: Fullstack
**Assessment result**: Complex — requires new DB model, migration, API router, service layer, frontend component, and tests across multiple files.

## Approach
1. Create `AdopterDocument` ORM model (migration 092)
2. Create `adopter_documents.py` API router with CRUD endpoints
3. Create service functions for document management
4. Add schemas for request/response
5. Register router in app.py
6. Create frontend page component for document management
7. Write unit and integration tests

## Dependencies
- Depends on: RAP-275 (S1 adopter dashboard — done)
- Depends on: Portal auth (done — uses `_get_current_user`)

## Risks
- Risk: PDF validation without heavy dependencies → Use python-magic for MIME type detection
  Mitigation: Re-use existing magic bytes validation from media_upload_service
