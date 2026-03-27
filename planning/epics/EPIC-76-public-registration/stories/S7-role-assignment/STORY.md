---
story: S7
epic: EPIC-76
ticket: RAP-506
title: "Role self-assignment"
status: ready
points: 4
priority: P2
track: Fullstack
sprint: 11
version: V1
created: 2026-03-27T20:00:00
---

# S7: Role self-assignment

## Story
As a **existing user**, I want **to add additional roles to my account** so that **I can participate in volunteering, fostering, or donating even if I registered as an adopter**.

## Description
Allow users to add volunteer, foster, or donor roles to their account after initial registration. Roles are not exclusive - a user can have multiple roles simultaneously.

## Acceptance Criteria
- [ ] Settings page at /portal/settings shows current user roles with "Add a Role" button
- [ ] "Add a Role" button opens modal or navigates to /portal/settings/add-role
- [ ] Role selection form shows checkboxes: "I want to volunteer", "I want to foster animals", "I want to donate", "I want to adopt" (last one pre-checked if adopter)
- [ ] User can select any combination of roles
- [ ] Each role has optional description: Volunteer = "Help with animal care, transportation, events", Foster = "Temporarily care for animals in my home", Donate = "Support animals with financial donations"
- [ ] POST /api/users/roles endpoint: accepts role (enum: adopter|donor|volunteer|foster), adds role to user without removing existing roles
- [ ] Response returns updated user.roles array with all roles
- [ ] Role addition shows confirmation: "You can now [role description]"
- [ ] GET /api/users/me endpoint includes user.roles array (can have multiple)
- [ ] Dashboard sections appear/disappear based on roles: volunteer section shows if 'volunteer' in roles, foster section if 'foster' in roles, etc.
- [ ] Users cannot remove their initial role through this flow (e.g., adopter who registered as adopter cannot remove adopter role)
- [ ] Actually, correction: users CAN remove roles by posting with role and action='remove', but must have at least one role
- [ ] Volunteer role adds: access to /portal/volunteer/schedule, volunteer opportunities listing, volunteer dashboard
- [ ] Foster role adds: access to /portal/foster/animals, foster profile completion, foster animal matching
- [ ] Donor role adds: access to /donate pages, donor dashboard, donation history
- [ ] Role-specific email confirmations: "Welcome to volunteering!" or similar
- [ ] Database: users table has roles column (JSON array or separate user_roles table)

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage) - test role addition, duplicate role prevention, minimum role enforcement
- [ ] Integration test: user adds volunteer role and can see volunteer section on dashboard
- [ ] Integration test: user adds multiple roles simultaneously
- [ ] Integration test: user cannot remove last role
- [ ] Integration test: role changes appear immediately in /api/users/me
- [ ] Component test: role selection form displays correctly
- [ ] Component test: dashboard sections appear/disappear based on roles
- [ ] Deployed to staging and verified

## Technical Notes
- Backend: FastAPI endpoint POST /api/users/roles with body {role: string, action: 'add'|'remove'}, validate user has at least one role after removal
- Frontend: React component at pages/portal/settings/add-role.tsx with checkboxes for each role
- Database: Option A - roles column as JSON array: ["adopter", "volunteer"]. Option B - user_roles junction table with user_id, role, created_at
- Validation: ensure role is valid enum value, prevent duplicate roles, prevent removing all roles, prevent removing adopter if registered as adopter (actually allow, but enforce at least 1 role)
- Email notifications: send role-specific welcome email when role added
- Dashboard: use user.roles to conditionally render sections (if 'volunteer' in roles, show volunteer section)
- No role deletion from settings by default - user can only remove roles via API call with explicit action='remove'

## Story Points: 4
