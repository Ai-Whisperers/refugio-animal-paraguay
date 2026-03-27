---
story: S10
epic: EPIC-77
ticket: RAP-516
title: "Public voucher statistics dashboard"
status: ready
points: 3
priority: P2
track: Fullstack
sprint: 11
version: V1
created: 2026-03-27T20:00:00
---

# S10: Public voucher statistics dashboard

## Story
As a **website visitor**, I want **to see impact of voucher program** so that **I can understand how donations help animals and be inspired to donate**.

## Description
Create public-facing dashboard showing voucher program impact including total vouchers, animals treated, breakdown by service, and recent successes with photos.

## Acceptance Criteria
- [ ] /impact/vouchers public page, no authentication required
- [ ] Hero section: large counter showing "X Vouchers Purchased" (animated counter on page load), subtitle "Supporting animal medical care"
- [ ] Stats cards below hero: "X Animals Treated" (count of unique animals in redeemed vouchers), "X Clinics Partnered" (count of active clinics), "EUR X Donated" (sum of redeemed vouchers), "X Surgeries Performed" (count of castration services)
- [ ] Service breakdown chart: pie or bar chart showing breakdown of services performed: castration (dogs), castration (cats), consultations, vaccinations, surgeries, etc. Only show redeemed vouchers.
- [ ] Top clinics section: list of clinics by vouchers redeemed (limit 5), shows clinic name, location, voucher count
- [ ] Recent redemptions gallery: shows last 10 redeemed vouchers with: animal photo (if consent given), animal name, service type, clinic name, date redeemed
- [ ] Success stories: carousel or grid showing selected "success stories" - vouchers with exceptional outcomes, before/after photos (with consent)
- [ ] Donation CTA button: "Help More Animals" button directing to /donate/voucher
- [ ] Responsive design: works on mobile, tablet, desktop
- [ ] Performance: page loads in < 3 seconds
- [ ] GET /api/public/vouchers/statistics endpoint: returns all statistics as JSON for data loading, caches for 1 hour
- [ ] GET /api/public/vouchers/recent endpoint: returns last 10 redeemed vouchers with photos (filtered by consent flag)
- [ ] Consent handling: only show photos/details if animal/rescuer/clinic consented to public display
- [ ] Cache warming: cron job runs every hour to update cache

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage) - test data filtering, consent checking
- [ ] Integration test: page loads statistics correctly
- [ ] Integration test: filters only redeemed vouchers for display
- [ ] Integration test: respects consent flags
- [ ] Component test: charts render correctly
- [ ] Component test: responsive on mobile/tablet/desktop
- [ ] Performance test: page loads in < 3 seconds
- [ ] Manual testing: verify animations and interactions
- [ ] Deployed to staging and verified

## Technical Notes
- Frontend: React page at pages/impact/vouchers.tsx with animated counters, charts (Recharts), photo gallery
- Backend: FastAPI endpoint /api/public/vouchers/statistics with caching (Redis, 1-hour TTL)
- Charts: use Recharts for pie/bar charts, reactive to data changes
- Animations: use framer-motion or react-spring for counter animations and transitions
- Photo gallery: use lightbox component (photoswipe or similar), lazy load images
- Caching: cache statistics in Redis with key "vouchers_stats", update hourly via cron
- Consent checking: query animals with public_photo_consent=true, clinics with public_display=true
- Service breakdown: group redeemed vouchers by service_type, count, convert to chart data
- Recent redemptions: query top 10 from VetVouchers where status='redeemed' ORDER BY redeemed_at DESC
- Top clinics: group by clinic, count redeemed vouchers, sort by count DESC, limit 5
- Success stories: manually curated list (admin-selected) stored separately or flagged in database
- Responsive: use Tailwind CSS responsive utilities, test on actual devices

## Story Points: 3
