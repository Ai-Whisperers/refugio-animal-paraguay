---
story: S3
epic: EPIC-76
ticket: RAP-502
title: "Unified personal dashboard"
status: done
points: 8
priority: P0
track: Fullstack
sprint: 11
version: V1
created: 2026-03-27T20:00:00
---

# S3: Unified personal dashboard

## Story
As a **logged-in user**, I want **to see a personalized dashboard** so that **I can quickly access my adoption applications, donations, sponsored animals, and volunteer information**.

## Description
Create a unified dashboard page that dynamically shows different sections based on user roles. The dashboard consolidates key information and provides quick access to role-specific features.

## Acceptance Criteria
- [ ] Dashboard page exists at /portal/dashboard, requires authentication (redirects to /login if not authenticated)
- [ ] Dashboard shows personalized greeting: "Hello, [User's First Name]!"
- [ ] For users with 'adopter' role: section showing "My Applications" with: adoption application list (limit 5), each showing animal name, date applied, current status badge (submitted|reviewing|approved|rejected|withdrawn), link to view full application
- [ ] For users with 'donor' role: section showing "My Donations" with: total donated (sum all donations, formatted with EUR/currency), donation count, last donation date, link to /portal/donations/history
- [ ] For users with any role: section showing "My Sponsored Animals" listing all animals user is sponsoring with: animal name, photo thumbnail, sponsorship amount/frequency, status indicator, link to animal profile
- [ ] For users with 'volunteer' role: section showing "My Volunteer Shifts" with: next 3 upcoming shifts (date, location, task description), past shifts count, link to /portal/volunteer/schedule
- [ ] For users with 'foster' role: section showing "Foster Animals in Care" with: current foster animals (name, species, photo), date took care, expected return date, link to manage foster animals
- [ ] Quick action buttons at top: "Adopt an Animal", "Make a Donation", "Volunteer", "Foster an Animal" (buttons shown only for relevant roles, all roles see all buttons)
- [ ] All links navigable and maintain user context
- [ ] Dashboard is responsive: works on mobile (single column), tablet (2 columns), desktop (3 columns)
- [ ] Loading state: skeleton screens shown while sections load
- [ ] Empty states: if user has no applications/donations/animals, show friendly message with call-to-action ("You haven't adopted yet - Browse available animals")
- [ ] GET /api/portal/dashboard endpoint returns JSON with all dashboard data: user info, applications (array), donations (summary), sponsored_animals (array), volunteer_shifts (array), foster_animals (array)
- [ ] Response includes: total_donations_count (number), total_donated_amount (cents, currency), next_volunteer_shift (object|null), current_foster_count (number)

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage) - test role-based sections visibility, empty state handling, data formatting
- [ ] Integration test: adopter with 2 applications sees them on dashboard
- [ ] Integration test: donor sees total donations and donation count
- [ ] Integration test: user with no data sees appropriate empty states
- [ ] Component test: responsive layout verified at mobile/tablet/desktop breakpoints
- [ ] Performance test: page loads in < 2 seconds with typical data
- [ ] Deployed to staging and verified: dashboard works for all roles

## Technical Notes
- Backend: GET /api/portal/dashboard endpoint in FastAPI, requires authentication, returns aggregated data from multiple tables
- Frontend: Next.js page at pages/portal/dashboard.tsx with React components for each section
- Data queries: optimize with proper JOINs, limit results (5 applications, 3 shifts, etc.)
- Responsive design: use Tailwind CSS with responsive columns (md: 2-col, lg: 3-col)
- Loading: React Suspense with fallback skeleton screens for each section
- Caching: consider cache invalidation strategy (ETags or short TTL)
- Components: DashboardCard, ApplicationSummary, DonationSummary, SponsoredAnimalCard, VolunteerShiftCard, FosterAnimalCard

## Story Points: 8
