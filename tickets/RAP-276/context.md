# RAP-276 Context

## STATUS: ACTIVE
**Last updated**: 2026-03-29 22:09

## Current Focus
Implementing document upload for adopters — backend model, API, service, and tests.

## Technical State
- Branch: feature/RAP-276-document-upload-for-adopters
- Pattern reference: vet_document.py for model, medical_documents.py for router
- Auth: _get_current_user from src.auth.dependencies
- Storage: file-system based (similar to media upload service)
- Migration: next is 092

## Next Steps
1. Create AdopterDocument ORM model
2. Create migration 092
3. Create adopter_documents API router
4. Add schemas
5. Register in app.py
6. Write tests

## Blockers
- None

## Key Decisions Made
- Using file-system storage consistent with existing media_upload_service
- Documents linked to adopter by adopter_id (FK to adopters table)
- Staff can view all documents, adopters can only view/manage their own
