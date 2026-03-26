---
story: S03
epic: EPIC-5
title: Task Assignment & Tracking
status: ready
created: 2026-03-25T17:13:26.731823
version: V4
---

# S03: Task Assignment & Tracking

## Description

Daily task assignment system for volunteers and staff with status tracking, completion validation, and task history reporting.

## Acceptance Criteria

**Given** a manager wants to assign tasks
**When** they access the Tasks section
**Then** they see a list of common tasks (feed animals, clean pens, exercise animals, etc.) and option to create custom tasks

**Given** I create a task
**When** I fill in task details (type, animal/area, deadline, priority, assigned to)
**Then** task is saved and assigned volunteer receives notification (in-app, optional email)

**Given** I am assigned a task
**When** I view my task list
**Then** I see assigned tasks organized by priority/deadline with descriptions and any special instructions

**Given** I start working on a task
**When** I click "Start"
**Then** task status changes to "in_progress" and timer may start (for optional time tracking)

**Given** I complete a task
**When** I click "Mark Complete"
**Then** I can optionally add notes, task moves to "completed", timestamp recorded, and manager receives notification for approval

**Given** a manager reviews completed task
**When** they view pending tasks for approval
**Then** they can approve (task closes), request changes (reopen), or mark as incomplete

**Given** tasks are tracked over time
**When** I view task history
**Then** I can see: completed tasks, completion rate, average time per task type, and task history for individual volunteers

**Given** a task is overdue
**When** deadline passes without completion
**Then** task shows overdue status in red, volunteer receives reminder, and manager sees alert

## Tasks

- T01: Create task assignment interface
- T02: Build tracking dashboard
