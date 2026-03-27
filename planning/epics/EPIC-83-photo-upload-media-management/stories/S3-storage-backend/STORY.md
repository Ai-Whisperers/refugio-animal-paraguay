---
story: S3
epic: EPIC-83
ticket: RAP-561
title: "Storage backend (local + S3 compatible)"
status: ready
points: 5
priority: P0
track: Backend
sprint: 12
version: V1
created: 2026-03-27T20:00:00
---

# S3: Storage backend (local + S3 compatible)

## Story
As a **devops engineer**, I want **flexible storage backend configuration** so that **I can use local storage in development and S3 in production**.

## Description
Implement abstract StorageBackend interface with two concrete implementations: LocalStorage (saves to filesystem, served by Nginx) and S3Storage (uses AWS S3 or compatible service like MinIO). Selection via environment variable.

## Acceptance Criteria
- [ ] StorageBackend abstract base class with methods: upload(key, file_path), download(key), delete(key), list(prefix), get_url(key, expires_in=3600)
- [ ] LocalStorage implementation: saves files to /media/ directory (configurable via MEDIA_LOCAL_PATH env var), implements all StorageBackend methods
- [ ] LocalStorage.get_url() returns local path suitable for Nginx serving (e.g., /media/uploads/2026/03/27/uuid/file.webp)
- [ ] S3Storage implementation: configurable bucket, region, endpoint, credentials (from env vars: AWS_S3_BUCKET, AWS_S3_REGION, AWS_S3_ENDPOINT, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
- [ ] S3Storage supports S3-compatible services (MinIO, DigitalOcean Spaces) via custom endpoint configuration
- [ ] S3Storage.get_url() returns pre-signed URL with configurable expiry (default 1 hour)
- [ ] S3Storage implements retry logic with exponential backoff for transient failures
- [ ] S3Storage creates bucket if not exists (with proper error handling if already exists)
- [ ] StorageBackend selection via STORAGE_BACKEND env var: "local" or "s3" (default: "local")
- [ ] Factory pattern: StorageFactory.create() returns appropriate backend based on env var
- [ ] Dependency injection: inject StorageBackend into upload endpoint
- [ ] Both implementations handle errors gracefully and raise custom StorageError
- [ ] Unit tests: mock StorageBackend for upload endpoint tests
- [ ] Integration tests: test both LocalStorage and S3Storage implementations
- [ ] Configuration validated on startup (bucket exists, permissions correct)

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage for both backends)
- [ ] Integration test for LocalStorage implementation
- [ ] Integration test for S3Storage against MinIO or S3
- [ ] Configuration validation tested
- [ ] Error handling tested (permission denied, bucket not found, etc.)
- [ ] Deployed to staging and verified

## Technical Notes
- Use boto3 for AWS S3 operations
- Implement retry logic with tenacity or similar library
- Add logging for all storage operations for debugging
- Consider connection pooling for S3 (boto3 handles this)
- Document environment variable configuration
- Consider lifecycle policies for automatic cleanup of old media

## Story Points: 5
