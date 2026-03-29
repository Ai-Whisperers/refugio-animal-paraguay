# RAP-232 Plan

## Objective
Create a bilingual (Spanish + English) terms of service page at /terms.

## Acceptance Criteria
- [ ] Terms of service page accessible at /terms
- [ ] Bilingual with ES/EN language toggle
- [ ] Covers: acceptance, use policy, donations, adoptions, IP, liability, changes, contact
- [ ] Consistent visual design with privacy page

## Complexity Assessment
**Track**: Simple Fix — mirrors privacy page structure exactly.

**Assessment result**: Simple Fix — clones privacy page pattern with terms-specific content.

## Approach
1. Add TERMS strings to strings.ts
2. Create frontend/src/app/terms/page.tsx

## Dependencies
- Soft dep on RAP-230 (footer links added there)
