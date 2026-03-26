---
epic: EPIC-5
title: Volunteer & Staff Management
status: ready
created: 2026-03-25T17:13:26.731105
updated: 2026-03-25T17:13:26.731108
---

# EPIC-5: Volunteer & Staff Management

## Overview

**Goal**: Build a lightweight but functional system for registering volunteers, scheduling their shifts, assigning them tasks, and recognizing their contributions — enabling the shelter to coordinate a distributed team of unpaid helpers who are critical to daily operations.

**Why it matters**: Small shelters in Paraguay rely heavily on volunteers for feeding, socializing animals, cleaning, veterinary assistance, and event support. Without a structured system, coordination happens through informal WhatsApp messages and manual spreadsheets, leading to missed shifts, duplicated effort, and volunteer burnout. A structured system improves reliability, gives staff visibility into who is available and what tasks are complete, and creates the data needed to recognize and retain good volunteers over time. For a shelter with European donors, a professional volunteer management system also signals organizational maturity.

**Target users**: Volunteers who register their availability, sign up for shifts, and view their assigned tasks; shelter staff who create shift schedules, assign tasks, and review completion status; shelter administrators who need aggregate volunteer metrics for donor reporting.

---

## Scope

### In Scope

- Volunteer registration: capturing name, contact information, availability windows, skills (veterinary background, transport, construction, language skills), and emergency contact
- Volunteer profile management: volunteers can update their own availability and contact details through a self-service interface
- Shift scheduling: staff can create shifts with a date, time window, location, required headcount, and description; volunteers can sign up for open shifts
- Shift capacity management: shifts have a maximum participant count; the system prevents overbooking
- Task assignment: staff can create discrete tasks associated with a shift or standing tasks not tied to specific shifts; tasks can optionally be associated with a specific animal; staff assign tasks to individuals or leave them open for volunteers to claim
- Task completion tracking: volunteers mark tasks complete; staff can verify completions and add notes
- Basic recognition: tracking lifetime volunteer hours, total shifts completed, and tasks completed per volunteer; exposing this on a volunteer profile page
- Volunteer analytics for admin reporting: total active volunteers, hours contributed per month, shifts with unfilled capacity, most frequent contributors

### Out of Scope

- Payroll or stipend management for paid staff (handled separately by the shelter owner's financial processes)
- Complex recurring shift generation beyond basic weekly pattern support
- Background check integration or vetting workflows
- Training curriculum or certification tracking (a future enhancement)
- Public volunteer recruitment portal (tracked as a feature of EPIC-11)

---

## Stories

- **S01: Volunteer Registration & Profiles** — Design the volunteer profile data model and implement the registration and self-service update endpoints. Capture availability windows as a structured set of day-of-week and time-of-day preferences. Enforce that only the volunteer themselves (or an admin) can modify a volunteer profile. Staff can view all profiles; volunteers can view only their own.

- **S02: Shift Scheduling System** — Implement the staff-facing endpoints for creating, editing, and canceling shifts. Implement the volunteer-facing endpoint for browsing upcoming open shifts and signing up. Enforce capacity constraints. Emit notification events to EPIC-6 when a volunteer successfully registers for a shift and when a shift is canceled by staff.

- **S03: Task Assignment & Tracking** — Implement the task data model with fields for description, assigned animal (optional foreign key to EPIC-1), assigned volunteer (optional), status (open, claimed, in progress, complete, verified), and due time. Staff-facing endpoints create and assign tasks. Volunteer-facing endpoints allow claiming open tasks, marking tasks in progress, and submitting completions. Staff-facing verification endpoint records the staff confirmation.

- **S04: Volunteer Recognition & Analytics** — Implement the volunteer hours calculation (derived from completed and verified shift records) and expose it on the volunteer profile endpoint. Implement the admin analytics endpoint that aggregates volunteer activity by month for the dashboard in EPIC-7. Define the data structure for the recognition display without building the frontend (handled by EPIC-11).

---

## Dependencies

**Depends on**:
- EPIC-10 (Authentication & User Accounts) — volunteers have their own role in the JWT authentication system; volunteers authenticate to sign up for shifts and claim tasks; staff and admin roles have elevated permissions to manage schedules
- EPIC-1 (Animal Catalog & Management) — tasks can optionally reference a specific animal; the animal foreign key relationship requires EPIC-1's schema to be stable
- EPIC-6 (Communications & Notifications) — shift confirmation and shift cancellation notifications are delivered via EPIC-6; this epic only emits the event payloads

**Blocks**:
- EPIC-7 (Admin Dashboards) — volunteer hours and shift analytics are surfaced in the admin reporting view

---

## Success Metrics

- Staff can create a shift and have it visible to volunteers for sign-up within two minutes
- Volunteers can register, browse available shifts, and sign up for one in under ten minutes on their first visit
- Zero overbooking: no shift exceeds its defined headcount limit under any concurrent request scenario
- Volunteer retention metric: the percentage of registered volunteers who complete at least one shift per month is visible in the admin dashboard
- Task completion visibility: staff can see the status of all open and in-progress tasks for the current day in a single API response

---

## Risk Factors

- **Volunteer no-shows**: A digital sign-up system does not guarantee physical attendance. Mitigation: reminder notifications via EPIC-6 the day before a shift; track no-show history on volunteer profiles so staff can deprioritize unreliable volunteers.
- **Privacy of volunteer contact data**: Volunteer names, phone numbers, and emergency contacts are personal data subject to GDPR considerations for EU volunteers. Mitigation: apply PII logging exclusions from EPIC-9; document the legal basis for processing volunteer data in the platform's privacy policy.
- **WhatsApp coordination parallel to the system**: Volunteers accustomed to informal WhatsApp groups may continue to coordinate outside the system. Mitigation: the system should complement rather than replace WhatsApp by sending shift confirmations and reminders through WhatsApp (EPIC-6 WhatsApp integration) to meet volunteers where they already are.

---

## Effort & Priority

**Priority**: Medium. Volunteer management is operationally important but does not block donor-facing features. It should be delivered after the core animal catalog and adoption workflows are stable.

**Estimated effort**: Two sprints. Registration and shift scheduling (S01, S02) form the first sprint. Task tracking and analytics (S03, S04) follow in the second sprint.
