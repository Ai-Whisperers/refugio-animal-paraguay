---
story: S05
epic: EPIC-5
title: Volunteer Onboarding Checklist
status: ready
created: 2026-03-26T00:00:00.000000
effort: 5
---

# S05: Volunteer Onboarding Checklist

## User Story

As a **volunteer**, I want to **complete a structured onboarding checklist with training modules and staff sign-off** so that **I am properly trained on shelter procedures and can be scheduled for shifts safely**.

## Acceptance Criteria

**Given** I am a newly registered volunteer
**When** I log in to my account
**Then** I see my onboarding checklist with required steps and training modules

**Given** I am completing onboarding
**When** I complete a training module (animal handling, safety, shelter procedures)
**Then** the module is marked as complete and staff is notified

**Given** my onboarding is incomplete
**When** I try to request a volunteer shift
**Then** I am prevented from scheduling until onboarding is finished

**Given** I have completed all training modules
**When** staff member verifies my completion
**Then** staff can mark my onboarding as signed off and I become eligible for shift assignment

**Given** onboarding is required for all volunteers
**When** I view the volunteer management system
**Then** I can see onboarding status and completion percentage for each volunteer

## Tasks

- T01: Create onboarding checklist model with required steps (training modules, health/safety briefing, orientation)
- T02: Build onboarding progress API endpoint for volunteers to mark steps complete and for staff to verify
- T03: Implement shift-blocking logic to prevent non-onboarded volunteers from requesting shifts
- T04: Add staff verification/sign-off workflow with ability to mark onboarding complete or request additional steps
- T05: Write unit and integration tests for onboarding workflow including shift-blocking and staff sign-off

## Definition of Done

- [ ] Onboarding checklist model includes: training modules (animal_handling, safety, procedures), health_briefing, orientation, sign_off_date, sign_off_staff_id
- [ ] Volunteers can view checklist and mark training modules as complete
- [ ] API endpoint tracks completion date and status for each step
- [ ] Shift request logic checks onboarding_status != "complete" and returns error if incomplete
- [ ] Staff can view volunteer onboarding status and mark steps as verified or complete
- [ ] Sign-off workflow captures staff_id and sign_off_date
- [ ] Unit tests cover onboarding state transitions and shift-blocking logic (80%+ coverage)
- [ ] Integration tests verify end-to-end flow from volunteer registration through shift eligibility
- [ ] Database tracks onboarding progress with clear completion status

## Technical Notes

- Onboarding model: id, volunteer_id, animal_handling_completed (boolean, date), safety_briefing_completed (boolean, date), procedures_training_completed (boolean, date), health_briefing_completed (boolean, date), orientation_completed (boolean, date), overall_status (enum: pending, in_progress, complete), staff_sign_off_id (FK), sign_off_date (optional)
- Training modules: Can be self-paced or staff-led; completion tracked with date timestamp
- Health/safety briefing: Required staff interaction with documented sign-off
- Shift request validation: Before allowing shift creation, query onboarding status — if overall_status != "complete", reject with message "Onboarding must be completed before requesting shifts"
- Database indexes: volunteer_id, overall_status, sign_off_date
- Authorization: Volunteers can only update their own checklist; staff can view and verify all volunteers

## Dependencies

- Depends on: EPIC-5 S01 (Volunteer registration system), EPIC-10 (Authentication for staff role)
- Blocks: EPIC-5 S02 (Shift scheduling depends on onboarded volunteer status)

## Story Points: 5
