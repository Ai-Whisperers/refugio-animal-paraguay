---
story: S1
epic: EPIC-90
ticket: RAP-612
title: "Survey model with question types"
status: ready
points: 5
priority: P0
track: Backend
sprint: 15
version: V15
created: 2026-03-27T20:00:00
---
# S01: Survey Model and Creation API

## Story

As an admin, I want to create surveys with various question types to gather structured feedback from the community.

## Description

Implement Survey model with flexible JSON schema for questions. Create API endpoints for survey CRUD operations and response storage.

## Acceptance Criteria

- [ ] Create Survey model with fields: title, description, questions (JSON array), is_active, start_date, end_date, created_by FK
- [ ] Question JSON schema: {type: radio|checkbox|text|rating, question: string, options: array [for radio/checkbox]}
- [ ] Create SurveyResponse model: survey_id FK, respondent_email nullable, respondent_user_id nullable, answers (JSON), created_at
- [ ] Implement POST /admin/surveys - create new survey (requires admin)
- [ ] Implement GET /admin/surveys - list surveys with pagination
- [ ] Implement GET /admin/surveys/{id} - get survey details
- [ ] Implement PUT /admin/surveys/{id} - edit survey
- [ ] Implement DELETE /admin/surveys/{id} - delete survey
- [ ] Implement POST /surveys/{id}/responses - submit survey response (public)
- [ ] Validate that survey is_active and within date range
- [ ] Prevent duplicate responses: max 1 response per email per survey
- [ ] Return 429 Too Many Requests if duplicate attempt
- [ ] Validate question types: radio, checkbox, text, rating only
- [ ] Validate radio/checkbox options are not empty
- [ ] Store responses with timestamp

## Definition of Done

- [ ] Database models created and tested
- [ ] API endpoints implemented
- [ ] Validation logic tested
- [ ] Rate limiting tested
- [ ] Unit tests for model validation
- [ ] Integration tests for API endpoints
- [ ] Deployed to staging

## Story Points: 5
