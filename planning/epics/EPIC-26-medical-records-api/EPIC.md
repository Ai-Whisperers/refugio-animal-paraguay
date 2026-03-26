---
epic: EPIC-26
title: "Medical Records API"
sprint: 2
status: planned
points: 25
created: 2026-03-26T19:06:04
version: V5
---

# EPIC-26: Medical Records API

## Overview
**Goal**: Database schema, models, and API endpoints for vet visits, diagnoses, treatments, and medications.
**Why it matters**: Medical records are a core shelter function. No medical tracking exists yet.
**Target users**: Veterinarians, shelter staff

## Stories
- [ ] [S1] Medical record schema and Alembic migration (5 pts, P0, Backend)
- [ ] [S2] Vet visit CRUD API endpoints (5 pts, P0, Backend)
- [ ] [S3] Diagnosis and treatment recording (5 pts, P0, Backend)
- [ ] [S4] Medication tracking with dosage/schedule (5 pts, P1, Backend)
- [ ] [S5] Medical document upload (lab results, X-rays) (5 pts, P1, Backend)

## Total Points
25

## Dependencies
- Sprint 2 prerequisite epics (if any)

## Acceptance Criteria (Epic Level)
- [ ] All P0 stories completed
- [ ] All tests passing
- [ ] Deployed to staging and verified
