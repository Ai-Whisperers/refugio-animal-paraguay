# Exemplar: Good Epic

This is a well-written epic. Use it as a calibration reference when writing or reviewing epics.

---

# [EPIC-2] Donor Management & EU Fundraising

## Overview
**Goal**: Enable the shelter to accept, track, and report donations from both local (PYG) and European (EUR) donors, with full GDPR compliance and automated tax receipt generation.

**Why it matters**: European donors represent 70% of current funding. Without structured donation tracking and GDPR-compliant communication, we risk losing donor trust and violating EU data protection law.

**Target users**: Donors (EU and local), shelter admin, accountant/bookkeeper.

## Scope

### In Scope
- Online donation form accepting EUR and PYG
- Stripe integration for card payments (EUR), local bank transfer instructions (PYG)
- Donor account creation and history view
- Automated PDF tax receipts for EU donors (required by Dutch/German law)
- GDPR consent management (opt-in, opt-out, data deletion)
- Donor communication preferences (newsletter, impact reports)
- Monthly and annual donation summaries for accounting export

### Out of Scope
- Cryptocurrency donations (separate epic)
- Corporate/grant fundraising management (separate epic)
- Crowdfunding campaign management (future)
- Physical donation jar tracking

## Features
- [ ] [FEAT-4] Donation submission form (EUR + PYG)
- [ ] [FEAT-5] Donor account portal
- [ ] [FEAT-6] Automated tax receipt generation
- [ ] [FEAT-7] GDPR consent management
- [ ] [FEAT-8] Accounting export (CSV/PDF)

## Success Metrics
- Donation conversion rate: >60% of started donations completed
- Time to receipt: automated receipts within 5 minutes of payment
- GDPR compliance: 100% of EU donors have explicit consent recorded
- Accounting export: accountant can self-serve monthly reports without admin help

## Dependencies
- Depends on: Auth system (EPIC-6) — donors need accounts
- Blocks: Reporting & Analytics (EPIC-5) — needs donation data

## Risks
- Risk: Stripe EU compliance requirements change → Mitigation: Use Stripe's built-in compliance tools, review annually
- Risk: EUR/PYG exchange rate reporting requirements unclear → Mitigation: Consult accountant before FEAT-8 begins

## Status
- [x] Planning
- [ ] In Progress
- [ ] Complete
