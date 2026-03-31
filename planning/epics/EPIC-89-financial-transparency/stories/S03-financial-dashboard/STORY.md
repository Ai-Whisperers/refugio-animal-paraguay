---
story: S3
epic: EPIC-89
ticket: RAP-606
title: "Financial transparency dashboard"
status: done
points: 7
priority: P0
track: Fullstack
sprint: 14
version: V14
created: 2026-03-27T20:00:00
---
# S03: Public Financial Dashboard

## Story

As a donor, I want to see how Refugio Animal Paraguay uses donations so that I can verify the organization is operating transparently and efficiently.

## Description

Create public financial transparency page showing approved expenses vs income, monthly trends, expense breakdown by category, and current balance. Data refreshes daily and is cached for performance.

## Acceptance Criteria

- [ ] Create /transparency public page (no authentication required)
- [ ] Page title: "Transparencia Financiera" (Financial Transparency)
- [ ] Display 4 key metrics cards (updated daily):
  - [ ] Total received this month (in PYG and USD)
  - [ ] Total spent this month (in PYG and USD)
  - [ ] Total received this year (in PYG and USD)
  - [ ] Current balance (in PYG and USD)
- [ ] Show pie chart of expenses by category (last 12 months):
  - [ ] Medical (Medico)
  - [ ] Food (Comida)
  - [ ] Shelter (Refugio)
  - [ ] Rescue (Rescate)
  - [ ] Operations (Operaciones)
  - [ ] Transport (Transporte)
  - [ ] Administration (Administracion)
- [ ] Show bar chart: monthly income vs expenses (last 12 months)
  - [ ] X-axis: months (Jan-Dec)
  - [ ] Y-axis: amount in PYG
  - [ ] Two bars per month: income (blue), expenses (red)
  - [ ] Bars stacked or grouped
- [ ] Display current month breakdown:
  - [ ] "Recibido este mes" (Received this month): total donations
  - [ ] "Gastado este mes" (Spent this month): total approved expenses
  - [ ] "Balance disponible" (Available balance)
- [ ] Add disclaimer: "Todos los gastos mostrados son aprobados por la junta directiva" (All expenses shown are approved by the board)
- [ ] Add "Last updated: [date]" timestamp
- [ ] Responsive layout: full width on mobile, centered on desktop
- [ ] Data source: GET /api/stats/financial (public, cached 1 hour)
- [ ] Charts use Chart.js or similar library
- [ ] Page loads within 2 seconds

## Definition of Done

- [ ] Code complete, peer reviewed
- [ ] Public API endpoint /api/stats/financial implemented
- [ ] Caching configured (1 hour TTL)
- [ ] Charts display correctly on mobile and desktop
- [ ] Data accuracy verified against database
- [ ] Responsive layout tested
- [ ] Performance tested (load time <2s)
- [ ] Unit tests for calculations
- [ ] Integration test for API endpoint
- [ ] Manual testing on browsers
- [ ] SEO metadata added to page
- [ ] Accessibility verified (alt text for charts)
- [ ] Deployed to staging and verified

## Technical Notes

- Implement /api/stats/financial backend endpoint
- Cache data in Redis with 1 hour TTL
- Pre-aggregate data: daily, monthly, yearly sums
- Use Chart.js or Recharts for charts
- Format currency with proper thousands separator
- Handle edge cases: no data, zero balance
- Include only approved expenses in calculations
- Consider data visualization best practices

## Story Points: 5
