# RAP-230 Plan

## Objective
Create a bilingual (Spanish + English) privacy policy page for Refugio Animal Paraguay, covering data collection, usage, and GDPR compliance.

## Description
The shelter requires a privacy policy page accessible to users in both Spanish and English. This page must cover what data is collected, how it is used, and users' rights under GDPR. The page follows the existing About/Contact page patterns using the strings system.

## Acceptance Criteria
- [ ] Privacy policy page accessible at `/privacy`
- [ ] Content provided in Spanish (default) with English option or tabs
- [ ] Covers: data collected, purpose, retention, user rights (GDPR), contact
- [ ] Linked from footer (Privacy Policy link)
- [ ] SEO metadata (title, description, og:url)
- [ ] Accessible: proper heading hierarchy, readable at all screen sizes

## Complexity Assessment
**Track**: Simple Fix

### Simple Fix Criteria (ALL must be met)
- [x] Single, clear root cause identified
- [x] Solution affects ≤3 files
- [x] Change impact ≤10 lines of actual code (well, page content but straightforward)
- [x] Low risk of side effects
- [x] Solution pattern is well-understood (follows existing page patterns)

**Assessment result**: Simple Fix — new static/semi-static page following existing About page patterns.

## Approach
1. Add PRIVACY strings to lib/strings.ts (both ES and EN)
2. Create `frontend/src/app/privacy/page.tsx` with bilingual sections
3. Update Footer to add Privacy Policy link
4. Add unit test for the page component

## Dependencies
- None

## Risks
- Risk: Footer layout change breaks existing tests → Mitigation: Follow existing footer pattern exactly
