---
story: S02
epic: EPIC-7
title: User & Role Management
status: ready
created: 2026-03-25T17:13:26.734016
version: V5
---

# S02: User & Role Management

## Description

Admin interface for managing user accounts, assigning roles, controlling permissions, and tracking user activity.

## Acceptance Criteria

**Given** I am a super admin
**When** I access Users & Roles section
**Then** I see a list of all users with columns: name, email, role, status (active/inactive), last login, created date

**Given** I want to add a new user
**When** I click "Add User"
**Then** a form opens for: email, name, role, initial password (optional auto-generate), and I can click to invite

**Given** I send a user invitation
**When** invitation is sent
**Then** user receives email with setup link, creates password, and account becomes active

**Given** I want to change a user's role
**When** I select a user and click "Edit Role"
**Then** a dialog shows current role, available roles with descriptions, and I can save new role (change logged in audit)

**Given** roles are defined in the system
**When** I view available roles
**Then** I see: admin (full access), staff (animal/adoption/medical), volunteer_manager (shift/task management), viewer (read-only dashboard)

**Given** a user's account needs to be disabled
**When** I click "Deactivate"
**Then** user can no longer log in, their sessions are terminated, and audit trail records the deactivation (with reason if provided)

**Given** I want to track user activity
**When** I view a user's details
**Then** I see: last login date, login history (last 10 logins), actions performed (filtered by user_id in audit trail)

**Given** a user account is deactivated
**When** I later want to reactivate it
**Then** I can click "Reactivate", user can log in again, and change is logged

## Tasks

- T01: Create user management UI
- T02: Implement role editor
