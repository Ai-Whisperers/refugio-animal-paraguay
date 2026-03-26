# RAP-028 Context

## STATUS: ACTIVE
**Last updated**: 2026-03-26

## Current Focus
Creating Next.js 14 project scaffold with all required tooling and utilities.

## Technical State
- Backend API exists at localhost:8000 with JWT auth, CRUD endpoints
- CORS already configured (RAP-013)
- No frontend directory exists yet on develop
- Need: Next.js 14, App Router, TypeScript strict, Tailwind, API client, auth utils

## Next Steps
1. Initialize Next.js 14 project
2. Configure TypeScript and Tailwind
3. Create API client and auth utilities
4. Build layout and homepage

## Blockers
None

## Key Decisions Made
- App Router (not Pages Router) per story spec
- Client-side auth guard (no SSR for authenticated pages initially)
- SWR for data fetching per story spec
