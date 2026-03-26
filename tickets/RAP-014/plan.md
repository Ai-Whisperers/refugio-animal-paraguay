# RAP-014 Plan

## Objective
Set up the Next.js 14 frontend project scaffold with App Router, TypeScript, Tailwind CSS, and API integration utilities.

## Description
This ticket creates the `frontend/` directory with a fully configured Next.js 14 application. It establishes the foundation for all frontend development: TypeScript strict mode, Tailwind CSS with shelter branding tokens, ESLint, a typed API client pointing to the FastAPI backend, and JWT auth utilities. This unblocks all subsequent frontend stories (animal browsing, admin panel, adoption forms).

## Acceptance Criteria
- [x] `frontend/` directory created with Next.js 14 App Router
- [x] TypeScript strict mode, Tailwind CSS 3.x, ESLint configured
- [x] Root layout with placeholder navigation and footer
- [x] Homepage with placeholder content
- [x] API client (`lib/api.ts`) with typed fetch wrapper
- [x] Auth utilities (`lib/auth.ts`) for JWT handling
- [x] Environment variables documented (NEXT_PUBLIC_API_URL)
- [x] `npm run dev`, `npm run build`, `npm run lint` all pass
- [x] SWR, React Hook Form, Zod installed

## Complexity Assessment
**Track**: Complex Implementation

### Simple Fix Criteria (ALL must be met)
- [ ] Single, clear root cause identified — N/A (new feature)
- [x] Solution affects ≤3 files — NO, affects 15+ files
- [ ] Change impact ≤10 lines of actual code — NO
- [x] Low risk of side effects — YES (new directory, no backend changes)
- [x] Solution pattern is well-understood — YES

**Assessment result**: Complex — New project scaffold with multiple configuration files, utility modules, and components.

## Approach
1. Initialize Next.js 14 with App Router and TypeScript via `create-next-app`
2. Configure Tailwind CSS with shelter branding design tokens
3. Set up ESLint with strict rules
4. Create root layout with navigation and footer components
5. Build homepage with placeholder content
6. Implement typed API client with configurable base URL
7. Implement JWT auth utilities (token storage, request injection)
8. Install SWR, React Hook Form, Zod
9. Verify dev server, build, and lint all pass

## Dependencies
- Depends on: RAP-007 (JWT Auth — delivered)
- Blocks: Story #5 (Animal Browsing), Story #6 (Admin Panel)

## Risks
- Risk: Node.js version mismatch → Mitigation: Use Node 18+ (LTS)
- Risk: Tailwind/Next.js version conflicts → Mitigation: Use create-next-app defaults
