# RAP-643 Plan

## Objective
Build a staff-facing volunteer application review page at `/admin/volunteers` that lists pending applications and allows approve/reject workflow.

## Description
Staff need a dedicated interface to manage volunteer applications. When someone submits a volunteer application, staff must review it and either approve or reject it (with a mandatory rejection reason). This page mirrors the adoptions review flow and is the staff counterpart to the public volunteer application form.

## Acceptance Criteria
- [ ] `/admin/volunteers` page lists all volunteer applications with status filter tabs
- [ ] Each row shows applicant name, email, status, skills, and submission date
- [ ] Clicking a row opens a detail view at `/admin/volunteers/[id]`
- [ ] Detail view shows full application: motivation, skills, availability, hours/week, emergency contact
- [ ] Staff can approve application via button (requires confirmation)
- [ ] Staff can reject application via button with mandatory rejection reason input
- [ ] Status badge colors: pending=yellow, approved=green, rejected=red, inactive=gray
- [ ] Empty state handled gracefully
- [ ] Error state handled with retry option
- [ ] Volunteer link added to AdminSidebar

## Complexity Assessment
**Track**: Frontend

### Simple Fix Criteria (ALL must be met)
- [x] Single, clear root cause identified
- [ ] Solution affects ≤3 files — affects ~4 files (page, detail, sidebar, types)
- [ ] Change impact ≤10 lines of actual code
- [x] Low risk of side effects
- [x] Solution pattern is well-understood

**Assessment result**: Complex — involves multiple new files + sidebar update, but well-understood pattern mirroring adoptions review.

## Approach
1. Add volunteer types to frontend types
2. Add `Voluntarios` nav link to AdminSidebar
3. Create `/admin/volunteers/page.tsx` — list with status filter tabs and pagination
4. Create `/admin/volunteers/[id]/page.tsx` — detail view with approve/reject workflow

## Dependencies
- Depends on: RAP-640 (volunteer model), RAP-641 (profile), RAP-642 (onboarding) — backend API exists
- Backend endpoints: `GET /api/staff/volunteers`, `PUT /api/staff/volunteers/{id}/review`

## Risks
- Risk: PR #303 (RAP-642) not merged yet, but staff endpoints from RAP-640 are already in develop → No risk, review endpoint exists since RAP-640
