# V5 — Analytics, Dashboard & Production Scale

**Version**: 5.0.0
**Timeline**: Weeks 19-24 (after V4 launch)
**Prerequisites**: V4 complete (all operational modules live)
**Theme**: *"The owner sees everything at a glance — and the platform is ready to grow"*

---

## Goal

Give the shelter owner and EU funders real-time visibility into operations, finances, and impact. Build the admin dashboard that ties all modules together, add advanced search, harden the platform for production scale, and complete the quality assurance layer. After V5, the platform is presentation-ready for funders and operationally mature.

---

## What V5 Adds

### 1. Admin Dashboard (EPIC-7)

| Feature | Description | Priority |
|---------|-------------|----------|
| KPI cards | Animals sheltered, adopted, in foster, donations this month | P0 |
| Real-time activity feed | WebSocket-powered live feed of events across the shelter | P1 |
| Adoption funnel | Visual: applications → reviews → approvals → completed | P0 |
| Donation analytics | EUR/PYG totals, trends, top donors, campaign performance | P0 |
| Volunteer overview | Active volunteers, hours this month, upcoming shifts | P1 |
| Medical overview | Animals needing attention, overdue vaccinations | P1 |
| Configurable date ranges | Last 7/30/90 days, custom range | P0 |
| Export to PDF/CSV | Any dashboard view exportable for funder reports | P1 |

### 2. Funder Reporting (New)

| Feature | Description | Priority |
|---------|-------------|----------|
| Impact report generator | Auto-generate quarterly impact report (PDF) | P0 |
| Donation allocation | Show how donations were spent (categories: medical, food, operations) | P1 |
| Before/after galleries | Rescue-to-adoption photo stories for funder updates | P2 |
| EU tax compliance report | Per-donor annual donation summary for tax deductions | P1 |
| Public impact page | Live stats widget embeddable on external websites | P2 |

### 3. Advanced Search (EPIC-1 completion)

| Feature | Description | Priority |
|---------|-------------|----------|
| Full-text search | PostgreSQL tsvector across animal names, descriptions, notes | P0 |
| Search filters | Species, age range, size, medical status, location | P0 |
| Search results ranking | Relevance scoring, boost available animals | P1 |
| Search suggestions | Autocomplete for animal names, breeds | P2 |
| Saved searches | Adopters can save search criteria and get notifications | P2 |

### 4. User & Role Management (EPIC-10 completion)

| Feature | Description | Priority |
|---------|-------------|----------|
| User management page | Admin creates/edits/deactivates user accounts | P0 |
| Role assignment UI | Assign roles: admin, staff, vet, volunteer, foster | P0 |
| Two-factor authentication | TOTP-based 2FA for admin and staff accounts | P1 |
| Session management | View active sessions, force logout | P2 |
| Audit log viewer | Who did what, when — filterable by user and action | P0 |

### 5. Production Hardening (EPIC-8 + EPIC-9 completion)

| Feature | Description | Priority |
|---------|-------------|----------|
| E2E test suite | Playwright tests for critical user journeys | P0 |
| Performance testing | Locust load tests, baseline metrics | P1 |
| CDN setup | Static assets and images served via CDN | P1 |
| Redis caching | Animal listings, dashboard aggregations cached | P1 |
| Database optimization | Query analysis, indexing strategy, connection pooling | P0 |
| Sentry error monitoring | Error tracking with context for all environments | P0 |
| Structured logging | JSON logs with request tracing, shipped to Grafana | P1 |
| Uptime monitoring | External health checks with alerting | P0 |
| Backup strategy | Automated daily DB backups, tested restore procedure | P0 |
| Security audit | Penetration test checklist, dependency audit | P1 |

### 6. Multi-language Completion

| Feature | Description | Priority |
|---------|-------------|----------|
| Guarani support | Third language for public-facing pages | P2 |
| Admin panel localization | Spanish admin interface | P1 |
| Date/currency formatting | Locale-aware display across all pages | P1 |

---

## Acceptance Criteria

V5 is complete when:

- [ ] Admin dashboard loads with real-time KPI cards (animals, adoptions, donations, volunteers)
- [ ] Adoption funnel visualization shows conversion rates
- [ ] Donation analytics show trends with EUR/PYG breakdown
- [ ] Impact report generates as PDF with correct data
- [ ] Full-text search returns relevant animals within 200ms
- [ ] Admin can create/edit/deactivate user accounts
- [ ] Audit log shows all sensitive operations with timestamps
- [ ] 2FA works for admin accounts
- [ ] E2E tests cover: adoption flow, donation flow, volunteer sign-up
- [ ] Load test confirms system handles 100 concurrent users
- [ ] Sentry captures and alerts on production errors
- [ ] Database backup runs daily with verified restore
- [ ] Overall test coverage >80%, critical paths >95%
- [ ] Zero high/critical vulnerabilities in dependency audit

---

## What V5 Does NOT Include (Future / V6+)

- Mobile native app (React Native / Flutter)
- AI-powered animal matching (adopter preferences → recommendations)
- Multi-shelter support (multiple locations under one platform)
- Inventory management (food, medicine, supplies stock tracking)
- Telemedicine / video vet consultations
- Social media integration (auto-post new arrivals)
- Blockchain donation tracking (transparency for large funders)
- Integration with government animal registries

---

## Technical Notes

### Dashboard Architecture

```
Frontend (Next.js)
  │
  ├── Static pages (SSG) — public portal
  ├── Server pages (SSR) — dashboard with auth
  └── Client components — real-time widgets
        │
        └── WebSocket connection
              │
              └── FastAPI WebSocket endpoint
                    │
                    └── Redis Pub/Sub (event bus)
                          │
                          ├── Adoption events
                          ├── Donation events
                          ├── Volunteer events
                          └── Medical events
```

### Search Implementation

```sql
-- Add tsvector column to animals table
ALTER TABLE animals ADD COLUMN search_vector tsvector;

-- Generate from name + description + species
CREATE FUNCTION animals_search_update() RETURNS trigger AS $$
BEGIN
  NEW.search_vector :=
    setweight(to_tsvector('spanish', coalesce(NEW.name, '')), 'A') ||
    setweight(to_tsvector('spanish', coalesce(NEW.description, '')), 'B') ||
    setweight(to_tsvector('spanish', coalesce(NEW.species, '')), 'C');
  RETURN NEW;
END $$ LANGUAGE plpgsql;

-- GIN index for fast search
CREATE INDEX idx_animals_search ON animals USING GIN(search_vector);
```

### Caching Strategy

| Cache Target | TTL | Invalidation |
|-------------|-----|-------------|
| Animal listings (public) | 5 min | On animal create/update/delete |
| Dashboard KPIs | 1 min | On any write operation |
| Search results | 10 min | On animal create/update |
| Exchange rates | 24h | Daily ECB fetch |

### Backup Strategy

```
Daily: pg_dump → compressed → S3 (EU-West region)
Weekly: Full backup with WAL archiving verification
Monthly: Restore test to temporary instance
Retention: 30 daily, 12 weekly, 6 monthly
```

---

## Risk Register

| Risk | Impact | Mitigation |
|------|--------|------------|
| Dashboard performance with large datasets | Slow page loads | Pre-computed aggregations, materialized views |
| WebSocket scaling | Real-time feed drops connections | Redis Pub/Sub, graceful reconnection on frontend |
| Search relevance poor | Users don't find animals | Spanish-language stopwords, boost available animals |
| 2FA user lockout | Admin can't access system | Recovery codes generated at setup, backup admin account |
| Backup restore fails | Data loss risk | Monthly restore drills, documented procedure |
| Security audit findings | Last-minute fixes delay launch | Run audit at week 20, leave 2 weeks for remediation |

---

## Estimated Effort

| Area | New Tickets | Story Points | Weeks |
|------|-------------|-------------|-------|
| Admin dashboard + analytics | 5-6 | 18-22 | 3-4 |
| Funder reporting | 3-4 | 10-12 | 1.5-2 |
| Advanced search | 2-3 | 8-10 | 1-1.5 |
| User management + 2FA | 3 | 8-10 | 1-1.5 |
| Production hardening | 5-6 | 15-18 | 2-3 |
| Multi-language completion | 2 | 5 | 0.5-1 |
| **Total** | **20-24** | **64-77** | **9-13** |

---

## Demo Script (Client / Funder Presentation)

1. Open admin dashboard — show live KPI cards updating
2. Show adoption funnel — "60% approval rate this quarter"
3. Show donation trends — "EUR 12,400 from 47 EU donors this quarter"
4. Generate impact report PDF — hand it to the funder
5. Search for "cachorro" — show instant results with photos
6. Show audit log — "every action is traceable"
7. Show the public impact page — embeddable on funder websites
8. Show backup running — "your data is safe"

*"Full visibility, full accountability. This is what you show your board."*

---

## Dependencies

- **Requires**: V4 (all operational data — volunteers, medical, foster)
- **Requires**: V2 (donation data for analytics)
- **External**: CDN provider account, Redis hosting, S3 bucket for backups
- **External**: Security audit provider (or self-conducted with OWASP checklist)

---

*Epics touched: EPIC-1 (complete), EPIC-7 (complete), EPIC-8 (complete), EPIC-9 (complete), EPIC-10 (complete)*
*Target release tag: `v5.0.0`*
