---
story: S1
epic: EPIC-80
ticket: RAP-533
title: "Rescuer self-registration and profile model"
status: ready
points: 5
priority: P0
track: Backend
sprint: 13
version: V1
created: 2026-03-27T20:00:00
---

# S1: Rescuer self-registration and profile model

## Story
As a **animal rescuer**, I want **to register as a rescuer and create my profile** so that **I can be discovered by donors and volunteers**.

## Description
Create RescuerProfile model and registration flow allowing rescuers to register and create public profiles with bio, location, and social links.

## Acceptance Criteria
- [ ] RescuerProfile model/table: user_id (FK), display_name (string, 2-100 chars), bio (text, 0-1000 chars), location_city (string), location_coords (JSON {lat, lng}, nullable), social_links (JSON {facebook, instagram, whatsapp, email}), phone_whatsapp (string), is_verified (boolean, default false), verification_method (enum: whatsapp|social|manual, nullable), joined_at, animal_count (integer, cached count of animals), supporter_count (integer, cached count of donors), created_at, updated_at
- [ ] POST /rescuers/register endpoint: accepts user_id (authenticated user), display_name, bio, city, phone, social_links, creates RescuerProfile
- [ ] Validation: display_name unique, phone format +595, bio max 1000 chars, at least one social link or contact method
- [ ] GET /rescuers/{slug} endpoint: public profile page, returns all profile data, animal_count, supporter_count, is_verified status
- [ ] Slug generation: auto-generate from display_name (slugify, ensure unique), e.g. "maria-gomez-rescuer"
- [ ] GET /api/rescuers/{slug} endpoint: public API endpoint returning profile data
- [ ] PUT /api/rescuers/profile endpoint: update rescuer profile, requires auth
- [ ] Caching: animal_count and supporter_count are denormalized (cached), updated on new animal/donation
- [ ] Verification badge: shows verified status on profile

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage) - test profile creation, uniqueness, slug generation
- [ ] Integration test: create rescuer profile
- [ ] Integration test: update profile
- [ ] Integration test: slug generation unique
- [ ] Database migration created
- [ ] Deployed to staging and verified

## Technical Notes
- Slug generation: use slugify library, check uniqueness, append number if needed
- Social links: stored as JSON, optional fields
- Verification: done separately (S8)
- Caching: denormalized counts updated via triggers or manual update on animal/donation creation
- Phone: validate +595 format

## Story Points: 5
