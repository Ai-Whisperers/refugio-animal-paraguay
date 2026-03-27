---
story: S2
epic: EPIC-82
ticket: RAP-552
title: "Homepage dynamic content"
status: ready
points: 5
priority: P0
track: Fullstack
sprint: 13
version: V1
created: 2026-03-27T20:00:00
---

# S2: Homepage dynamic content

## Story
As a **visitor**, I want **homepage statistics to reflect real data** so that **I see current impact and can feel confident in the organization**.

## Description
Replace hardcoded homepage statistics (rescued animals count, adoption count, volunteer count, donation total) and sections (team, testimonials) with dynamic API calls to live data from the database.

## Acceptance Criteria
- [ ] GET /api/content/home_stats endpoint created, returns: animal_count (total from animals table), adoption_count (count of completed adoptions), volunteer_count (count of active volunteers), donation_total_cents (sum of all donations)
- [ ] GET /api/content/home_team endpoint returns team member blocks from content table
- [ ] GET /api/content/home_testimonials endpoint returns testimonial blocks from content table
- [ ] Homepage component fetches stats on mount and caches for 5 minutes (client-side or via API cache headers)
- [ ] Stats display updates with actual numbers from /stats/home_stats endpoint
- [ ] Team section displays team members from /content/home_team with fallback to hardcoded defaults if API fails
- [ ] Testimonials section displays from /content/home_testimonials with fallback to hardcoded defaults
- [ ] Error handling: if API fails, component logs error and displays fallback cached values without breaking page
- [ ] Network request waterfall analyzed: stats call doesn't block other page loads
- [ ] Performance: page loads in under 3 seconds with all dynamic content (measured via Lighthouse)
- [ ] Accessibility: stats are properly labeled for screen readers (aria-label on stat values)

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage)
- [ ] Integration test for API and component interaction
- [ ] E2E test: navigate to homepage, verify stats are displayed
- [ ] Performance verified with Lighthouse
- [ ] Fallback behavior tested (API errors)
- [ ] Deployed to staging and verified

## Technical Notes
- Use React Query or SWR for data fetching with built-in caching
- Set Cache-Control: public, max-age=300 on API responses
- Implement exponential backoff for retries
- Consider using Next.js getStaticProps with revalidation for SSR
- Add loading skeleton while fetching
- Monitor API call latency in observability tool

## Story Points: 5
