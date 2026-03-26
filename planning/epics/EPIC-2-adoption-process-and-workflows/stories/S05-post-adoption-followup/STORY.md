---
story: S05
epic: EPIC-2
title: Post-Adoption Follow-up
status: ready
created: 2026-03-26T00:00:00.000000
effort: 8
---

# S05: Post-Adoption Follow-up

## User Story

As a **staff member**, I want to **automatically schedule and track post-adoption follow-ups at 7, 30, 90, and 365 days with welfare surveys and return/rehome tracking** so that **we can monitor adoption outcomes, measure success rates, and meet EU funder requirements for outcome data**.

## Acceptance Criteria

**Given** an adoption is completed
**When** the adoption status changes to "completed"
**Then** follow-up tasks are automatically scheduled for day 7, 30, 90, and 365

**Given** a follow-up is due
**When** the scheduled date arrives
**Then** the adopter receives a notification with a link to the welfare survey

**Given** I am an adopter completing a follow-up survey
**When** I submit the survey
**Then** my responses are recorded and visible to staff for review

**Given** an adoption has issues
**When** I mark the animal as returned or rehomed
**Then** return reason codes are captured and stored for analytics

**Given** I am a staff member reviewing outcomes
**When** I access the adoption outcomes dashboard
**Then** I can see success rate, return rate by species, and return rate by adopter demographic

**Given** EU funders require outcome data
**When** I export adoption outcomes
**Then** the export includes adoption completion status, return rates, and survey responses

## Tasks

- T01: Create follow-up schedule model and auto-generation logic triggered on adoption completion
- T02: Build follow-up survey form schema, API endpoint, and storage for survey responses
- T03: Implement return/rehome tracking with reason code categorization (moved away, behavior issues, family circumstances, etc.)
- T04: Create adoption outcomes analytics endpoint with success rate, return rate by species, and return rate by adopter demographics
- T05: Write unit and integration tests for follow-up scheduling, survey submission, return tracking, and analytics

## Definition of Done

- [ ] Follow-up schedule model created and auto-generates 4 tasks per adoption
- [ ] Follow-up survey form captures welfare check, satisfaction, and optional photo submission
- [ ] Survey API endpoint stores responses with survey_date, adopter_id, adoption_id, responses JSON
- [ ] Return/rehome tracking records reason code and allows staff to update adoption outcome
- [ ] Analytics endpoint provides: total adoptions, returned adoptions, success rate %, return rate by species, return rate by adopter demographic
- [ ] Notification system (EPIC-6) triggers survey reminders on scheduled dates
- [ ] Unit tests cover scheduling, survey storage, return tracking (80%+ coverage)
- [ ] Integration tests verify end-to-end follow-up workflow from adoption completion through outcome recording
- [ ] Export functionality available for EU funder reporting

## Technical Notes

- Follow-up model: id, adoption_id, scheduled_date, survey_sent_date, survey_completed_date, survey_responses (JSON), return_date (optional), return_reason_code (optional enum), status (pending, sent, completed, returned)
- Survey response schema: welfare_score (1-5), satisfaction_score (1-5), comments (text), photo_url (optional), issues_noted (text)
- Return reason codes: "moved_away", "behavior_issues", "family_circumstances", "allergies", "housing_situation", "financial", "time_constraints", "other"
- Analytics queries: COUNT(adoptions WHERE status='completed'), COUNT(adoptions WHERE return_date IS NOT NULL), GROUP BY species, GROUP BY adopter_demographics (age_group, location, etc.)
- Database indexes: adoption_id, scheduled_date, status, species, adopter_demographics
- Notification integration: Use EPIC-6 email service to send survey reminders 1 day before scheduled date

## Dependencies

- Depends on: EPIC-2 S01-S04 (Adoption must be completed), EPIC-6 (Notification delivery system), EPIC-10 (Authentication)
- Blocks: EPIC-13 (Impact reporting depends on outcome data)

## Story Points: 8
