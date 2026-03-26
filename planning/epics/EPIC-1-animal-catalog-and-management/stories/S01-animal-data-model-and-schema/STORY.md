---
story: S01
epic: EPIC-1
title: Animal Data Model & Schema
status: ready
created: 2026-03-25T17:13:26.725441
version: V1
---

# S01: Animal Data Model & Schema

## Description

Design and implement PostgreSQL schema for animals with species, breed, medical history, and adoption status tracking.

## Acceptance Criteria

**Given** the system needs to store animal records
**When** the schema is defined and applied to the database
**Then** the Animal table includes all required fields: id, name, species, breed, age, weight, health_status, adoption_status, intake_date, photo_urls, created_at, updated_at

**Given** a new animal record is created
**When** the data is saved to the database
**Then** all fields are validated: species is from enum (dog, cat, bird, rabbit, other), breed is not empty, age is non-negative integer, health_status is from enum (healthy, injured, sick, special_needs)

**Given** the database is deployed to production
**When** migrations are applied
**Then** the Animal table exists with proper indexes on species, breed, adoption_status, and intake_date for query performance

**Given** test data is needed for feature development
**When** seed data is created
**Then** the database contains at least 20 animal records spanning all species and health statuses for testing filters and search

## Tasks

- T01: Define Prisma schema for Animal entity
- T02: Create database migrations
- T03: Implement seed data for testing
