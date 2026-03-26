# RAP-014 Context

## STATUS: ACTIVE
**Last updated**: 2026-03-26

## Current Focus
Scaffolding the Next.js 14 frontend project.

## Technical State
- New `frontend/` directory at project root
- Next.js 14 with App Router, TypeScript strict, Tailwind CSS
- API client targeting FastAPI backend at NEXT_PUBLIC_API_URL
- JWT auth utilities for token management

## Next Steps
1. Create feature branch
2. Run create-next-app
3. Configure and customize

## Blockers
- None

## Key Decisions Made
- Using App Router (not Pages Router) per story requirements
- SWR for data fetching (not React Query) per story requirements
- Client-side auth guard initially (no SSR for authenticated pages)
