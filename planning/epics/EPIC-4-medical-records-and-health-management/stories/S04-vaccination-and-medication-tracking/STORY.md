---
story: S04
epic: EPIC-4
title: Vaccination & Medication Tracking
status: ready
created: 2026-03-25T17:13:26.730847
version: V4
---

# S04: Vaccination & Medication Tracking

## Description

System for tracking scheduled and completed vaccinations and medications with automated reminder generation for upcoming due dates.

## Acceptance Criteria

**Given** a vaccination is due for an animal
**When** staff view the animal's medical record
**Then** vaccination section shows: vaccine name, last administered date, next due date, and status (due/overdue/completed/scheduled)

**Given** a vaccination is overdue
**When** it is displayed
**Then** a red alert badge shows "OVERDUE" and clear call-to-action to schedule with vet

**Given** staff records a vaccination
**When** they enter vaccine name, date, and vet info
**Then** system calculates next due date based on vaccine type, stores record, and updates timeline

**Given** an animal is on medication
**When** staff add medication to record
**Then** they enter: medication name, dosage, frequency (daily/twice daily/weekly), start date, end date, vet notes

**Given** daily medication is recorded
**When** the dashboard displays upcoming tasks
**Then** shelters see a "Medication Due Today" widget showing animals needing medication with time

**Given** multiple animals need medication today
**When** staff view the tasks dashboard
**Then** they see a sorted list of animals by medication time, with checkboxes to mark as given and notes field

**Given** medication is marked as given
**When** staff check the completion box
**Then** timestamp is recorded, audit trail is updated, and entry is moved to completed/history section

**Given** vaccination or medication is upcoming
**When** system runs daily check
**Then** reminders are created for staff (in-app notification, optional email) showing animals with upcoming due dates

## Tasks

- T01: Create vaccination tracker
- T02: Setup reminder system
