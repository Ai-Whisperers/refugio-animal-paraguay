# RAP-216 Plan

## Objective
Build a newsletter template builder frontend page in Next.js 14 that allows staff to create and manage reusable email templates.

## Acceptance Criteria
- [ ] Staff can create newsletter templates with subject line and HTML/text body
- [ ] Template list view with CRUD actions
- [ ] Preview functionality
- [ ] API endpoints backed by backend
- [ ] Unit and integration tests passing

## Complexity Assessment
**Track**: Complex — Frontend + Backend schema/model/router

**Assessment result**: Complex — new DB model, API, and Next.js page.

## Approach
1. Create EmailTemplate DB model + migration (084)
2. Create API router for template CRUD
3. Create Next.js admin page at /admin/email-templates
4. Write tests
