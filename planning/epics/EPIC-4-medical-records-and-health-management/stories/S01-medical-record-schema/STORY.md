---
story: S01
epic: EPIC-4
title: Medical Record Schema
status: ready
created: 2026-03-25T17:13:26.730007
version: V4
---

# S01: Medical Record Schema

## Description

Design and implement PostgreSQL schema for medical records including vaccinations, treatments, health checks, and medications with audit trail.

## Acceptance Criteria

**Given** the system needs to track animal medical history
**When** the schema is designed
**Then** tables are created for: medical_records, vaccinations, medications, health_checks, veterinary_documents with proper relationships

**Given** a medical record is created
**When** data is stored
**Then** fields include: animal_id, date, record_type (enum: checkup, vaccination, treatment, etc.), vet_name, notes, status, created_at, updated_at

**Given** vaccinations are tracked
**When** a vaccination record is created
**Then** fields include: animal_id, vaccine_name, date_administered, next_due_date, vet_id, batch_number, created_at

**Given** a medical record is modified
**When** updates occur
**Then** audit trail logs: who changed it, when, what changed, previous value, new value (via audit triggers)

**Given** the database is indexed
**When** queries are performed
**Then** indexes exist on: animal_id, date, record_type, next_due_date for fast retrieval and filtering

**Given** medical schema is deployed
**When** migration is applied
**Then** no existing animal records are lost, and new medical tables are initialized empty and ready for data

## Tasks

- T01: Design medical record schema
- T02: Create database migrations
- T03: Implement audit logging
