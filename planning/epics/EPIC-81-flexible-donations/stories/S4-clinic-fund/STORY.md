---
story: S4
epic: EPIC-81
ticket: RAP-546
title: "Clinic fund page"
status: ready
points: 5
priority: P1
track: Fullstack
sprint: 12
version: V1
created: 2026-03-27T20:00:00
---

# S4: Clinic fund page

## Story
As a **donor**, I want **to fund a clinic** so that **they can provide affordable services**.

## Description
Create clinic funding page with service-specific donation options.

## Acceptance Criteria
- [ ] Clinic page /clinics/{slug}: includes "Fund Castrations" or "Support Clinic" button
- [ ] /clinics/{slug}/fund page: shows clinic info, services offered, funding target (optional)
- [ ] Service-specific donations: select service type (castration, consultation, surgery), donate to fund that service
- [ ] Donation type: target_type='clinic', target_id=clinic_id, service_id (optional)
- [ ] Impact message: "Your EUR 30 pays for one castration at [clinic]"
- [ ] Funding progress: if clinic has funding goal, show progress bar
- [ ] Total funded: show total amount funded to clinic (all-time)

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage)
- [ ] Integration test: donate to clinic
- [ ] Component test: clinic fund page renders
- [ ] Deployed to staging and verified

## Technical Notes
- Donation: target_type='clinic', target_id=clinic_id, optional service_id
- Progress: if clinic.funding_goal set, calculate progress
- Total: sum all donations to clinic

## Story Points: 5
