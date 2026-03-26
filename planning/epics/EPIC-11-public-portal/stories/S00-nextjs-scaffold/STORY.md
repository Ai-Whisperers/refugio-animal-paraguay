---
story: S00
epic: EPIC-11
title: Next.js 14 Project Scaffold
status: ready
created: 2026-03-26T00:00:00.000000
effort: 5
---

# S00: Next.js 14 Project Scaffold

## User Story

As a **developer**, I want to **set up the Next.js 14 frontend project with App Router, TypeScript, Tailwind CSS, and API integration scaffolding** so that **frontend development can begin with consistent conventions and tooling**.

## Acceptance Criteria

**Given** the project repository
**When** the scaffold is created
**Then** a `frontend/` directory exists with a working Next.js 14 application

**Given** the frontend scaffold
**When** I run `npm run dev`
**Then** the dev server starts and serves a homepage at http://localhost:3000

**Given** the frontend scaffold
**When** I check the configuration
**Then** TypeScript strict mode is enabled, Tailwind CSS is configured, and ESLint is set up

**Given** the frontend needs to communicate with the backend
**When** I examine the API client
**Then** a typed fetch wrapper exists that points to the FastAPI backend (configurable via env var)

**Given** the project has authenticated endpoints
**When** I examine the auth utilities
**Then** JWT token storage and injection into API requests is implemented

## Definition of Done

- [ ] `frontend/` directory created with Next.js 14 App Router
- [ ] TypeScript strict mode, Tailwind CSS 3.x, ESLint configured
- [ ] Root layout with placeholder navigation and footer
- [ ] Homepage with placeholder content
- [ ] API client (`lib/api.ts`) with typed fetch wrapper
- [ ] Auth utilities (`lib/auth.ts`) for JWT handling
- [ ] Environment variables documented (NEXT_PUBLIC_API_URL)
- [ ] `npm run dev`, `npm run build`, `npm run lint` all pass
- [ ] README section for frontend development

## Technical Notes

- Use App Router (not Pages Router)
- Directory: `frontend/` at project root (separate from Python backend)
- API base URL: `NEXT_PUBLIC_API_URL` (default http://localhost:8000)
- No SSR for authenticated pages initially — client-side auth guard
- Tailwind design tokens: define primary/accent colors for shelter branding
- SWR for client-side data fetching
- React Hook Form + Zod for forms (install but don't build forms yet)

## Dependencies

- Depends on: EPIC-10 S01 (Auth — already delivered as RAP-007)
- Blocks: EPIC-11 S01 (Animal Browsing Page), EPIC-7 S01 (Admin Panel)

## Story Points: 5
