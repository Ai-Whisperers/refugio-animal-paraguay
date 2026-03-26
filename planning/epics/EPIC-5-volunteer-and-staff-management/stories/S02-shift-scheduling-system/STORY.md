---
story: S02
epic: EPIC-5
title: Shift Scheduling System
status: ready
created: 2026-03-25T17:13:26.731567
version: V4
---

# S02: Shift Scheduling System

## Description

Calendar-based shift scheduling allowing admin to create shifts, volunteers to claim shifts, and tracking attendance with reminder notifications.

## Acceptance Criteria

**Given** I am a manager/admin
**When** I access the Scheduling section
**Then** I see a calendar view showing available shifts by date, time, and position needed

**Given** I want to create a new shift
**When** I click "Create Shift"
**Then** a form opens for: date, start time, end time, position/role, max volunteers needed, notes

**Given** a shift is created
**When** the shift is saved
**Then** it appears on the calendar, volunteers can see it, and availability is tracked

**Given** I am a volunteer
**When** I view the schedule
**Then** I see available shifts matching my registered availability and interests, with clear indication of open/full status

**Given** I want to claim a shift
**When** I click "Volunteer" on a shift
**Then** my name is added to the shift roster (if slots available), I receive confirmation, and shift appears in my personal calendar

**Given** a shift is coming up
**When** it is within 24 hours
**Then** volunteer receives reminder notification (email/in-app) with shift details, time, and location

**Given** a volunteer attends a shift
**When** they check in at the shelter (or admin marks as attended)
**Then** hours are logged, attendance record created with timestamp, and cumulative hours updated

**Given** a volunteer cancels a shift
**When** they click "Cancel" within allowed timeframe
**Then** they are removed from roster, another volunteer may claim the spot, and admin receives notification if too late to find replacement

## Tasks

- T01: Build scheduling calendar
- T02: Implement shift assignment
