# RAP-028 Plan

## Objective
Set up the Next.js 14 frontend project scaffold with App Router, TypeScript, Tailwind CSS, and API integration scaffolding.

## Description
The backend API (FastAPI) is complete through Phase 2 with JWT auth, CRUD endpoints, and Docker. This ticket creates the `frontend/` directory with a working Next.js 14 application that can communicate with the backend, enabling all subsequent frontend stories.

## Acceptance Criteria
- [ ] `frontend/` directory created with Next.js 14 App Router
- [ ] TypeScript strict mode enabled
- [ ] Tailwind CSS 3.x configured with shelter branding tokens
- [ ] ESLint configured and passing
- [ ] Root layout with placeholder navigation and footer
- [ ] Homepage with placeholder content
- [ ] API client (`lib/api.ts`) with typed fetch wrapper
- [ ] Auth utilities (`lib/auth.ts`) for JWT token storage and injection
- [ ] Environment variables documented (NEXT_PUBLIC_API_URL)
- [ ] SWR installed for client-side data fetching
- [ ] React Hook Form + Zod installed for future forms
- [ ] `npm run dev`, `npm run build`, `npm run lint` all pass

## Complexity Assessment
**Track**: Complex Implementation

### Simple Fix Criteria (ALL must be met)
- [ ] Single, clear root cause identified — N/A (new feature)
- [x] Solution affects ≤3 files — NO, many files
- [ ] Change impact ≤10 lines of actual code — NO
- [ ] Low risk of side effects — YES
- [x] Solution pattern is well-understood — YES

**Assessment result**: Complex — new project scaffold with multiple configuration files, utilities, and components.

## Approach
1. Initialize Next.js 14 with `create-next-app` (App Router, TypeScript, Tailwind, ESLint)
2. Configure TypeScript strict mode and Tailwind design tokens
3. Create API client with typed fetch wrapper and error handling
4. Create auth utilities for JWT token management
5. Build root layout with navigation and footer components
6. Create homepage with placeholder content
7. Install SWR, React Hook Form, Zod
8. Verify all quality gates pass

## Dependencies
- Depends on: RAP-007 (JWT Auth — delivered)
- Blocks: Story #5 (Animal Browsing Page), Story #6 (Admin Panel)

## Risks
- Risk: Node.js version incompatibility → Mitigation: Use Node 18+ (LTS)
- Risk: CORS issues with backend → Mitigation: Backend already has CORS configured (RAP-013)
