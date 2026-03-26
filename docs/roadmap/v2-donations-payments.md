# V2 — Donations & EU Payment Integration

**Version**: 2.0.0
**Timeline**: Weeks 5-8 (after V1 launch)
**Prerequisites**: V1 complete (frontend + CI/CD operational)
**Theme**: *"European donors can find us online and donate with one click"*

---

## Goal

Enable the EU donor network to contribute financially through the website. This is the revenue engine — the Dutch owner's European contacts need a frictionless way to donate in EUR. Add SEPA Direct Debit for recurring donors and a public donation page that builds trust.

---

## What V2 Adds

### 1. Public Donation Experience (EPIC-3 + EPIC-11)

| Feature | Description | Priority |
|---------|-------------|----------|
| Donation landing page | Impact story, photos, clear CTA | P0 |
| One-time donation form | Amount selection (preset + custom), card payment via Stripe | P0 |
| SEPA Direct Debit | Recurring donations for EU donors (IBAN entry) | P0 |
| Donation receipt page | Thank you + tax receipt download (PDF) | P1 |
| Donor profile creation | Optional account for donation history | P2 |
| Currency handling | EUR (default for EU), PYG (local), display conversion | P0 |

### 2. Stripe Webhook Processing (EPIC-3)

| Feature | Description | Priority |
|---------|-------------|----------|
| Webhook endpoint | `POST /webhooks/stripe` — verify signature, process events | P0 |
| Payment confirmation | Update donation status on `payment_intent.succeeded` | P0 |
| Failed payment handling | Mark donation failed, optional retry notification | P1 |
| Idempotency | Deduplicate webhook retries using event ID | P0 |
| SEPA mandate events | Handle `mandate.updated`, `charge.failed` for SEPA | P1 |

### 3. Donation Dashboard (EPIC-3 + EPIC-7 partial)

| Feature | Description | Priority |
|---------|-------------|----------|
| Staff donation list | Filterable by date, amount, currency, status | P0 |
| Donation totals | Daily/weekly/monthly aggregations, EUR + PYG | P0 |
| Donor directory | List donors with total contribution history | P1 |
| CSV export | Export donation records for accounting | P1 |
| Tax reporting view | EU-compliant donation summaries per donor per year | P2 |

### 4. Email Notifications (EPIC-6 partial — donation-related only)

| Feature | Description | Priority |
|---------|-------------|----------|
| Donation confirmation email | Sent after successful payment | P0 |
| Recurring donation setup email | SEPA mandate confirmation | P1 |
| Failed payment alert | Notify donor of failed charge | P1 |
| Email provider integration | Resend or Mailgun — transactional only | P0 |

### 5. GDPR Compliance Hardening

| Feature | Description | Priority |
|---------|-------------|----------|
| Cookie consent banner | Required for EU visitors | P0 |
| Privacy policy page | Data processing, retention, rights | P0 |
| Donor data export | GDPR Article 15 — download personal data | P1 |
| Consent tracking | Record when/how consent was given | P0 |

---

## Acceptance Criteria

V2 is complete when:

- [ ] EU donor can visit donation page and pay with credit card (Stripe)
- [ ] EU donor can set up recurring SEPA Direct Debit donation
- [ ] Donation amount correctly recorded in EUR with exchange rate to PYG
- [ ] Stripe webhooks process payment confirmations reliably
- [ ] Duplicate webhook events are handled idempotently
- [ ] Donor receives confirmation email after successful donation
- [ ] Staff can view donation list with filters and totals
- [ ] Staff can export donation records as CSV
- [ ] Cookie consent banner appears for all visitors
- [ ] Privacy policy page exists and is linked from footer
- [ ] All new endpoints have test coverage >80%
- [ ] SEPA mandate lifecycle events handled correctly

---

## What V2 Does NOT Include

- WhatsApp notifications (V3)
- Tigo Money / local PYG payment methods (V3)
- Recurring donation management UI for donors (V3)
- Sponsorship programs (V4)
- Advanced analytics dashboards (V5)

---

## Technical Notes

### Stripe Configuration

```
Stripe mode: Live (EU merchant account required)
Products:
  - One-time donation (variable amount)
  - Recurring donation (SEPA, monthly)
Currency: EUR (primary), PYG (display only)
Webhook events to handle:
  - payment_intent.succeeded
  - payment_intent.payment_failed
  - charge.refunded
  - mandate.updated
  - invoice.payment_succeeded (recurring)
  - invoice.payment_failed (recurring)
```

### Exchange Rate Strategy

- Fetch EUR/PYG rate daily from ECB or exchangerate.host API
- Store rate at time of donation (immutable — for accounting)
- Display PYG equivalent on dashboard, but EUR is the source of truth for EU reporting

### Email Provider

- **Recommended**: Resend (developer-friendly, EU data processing)
- **Alternative**: Mailgun (established, good deliverability)
- Transactional only in V2 — no marketing emails yet

---

## Risk Register

| Risk | Impact | Mitigation |
|------|--------|------------|
| Stripe EU merchant approval delays | Can't accept live payments | Start application in V1, use test mode until approved |
| SEPA mandate failures | Recurring donors can't donate | Implement retry logic + donor notification |
| Exchange rate volatility | PYG amounts look wrong | Cache rates, show "approximate" disclaimer |
| GDPR non-compliance | Legal risk with EU donors | Privacy policy reviewed before launch, consent audit |
| Email deliverability | Donors don't receive receipts | Use dedicated IP, verify domain SPF/DKIM |

---

## Estimated Effort

| Area | New Tickets | Story Points | Weeks |
|------|-------------|-------------|-------|
| Donation frontend pages | 3-4 | 10-12 | 1.5-2 |
| Stripe webhooks + SEPA | 3 | 10 | 1-1.5 |
| Donation dashboard (staff) | 2-3 | 8 | 1-1.5 |
| Email notifications | 2 | 5 | 0.5-1 |
| GDPR compliance | 2-3 | 5-8 | 0.5-1 |
| **Total** | **12-15** | **38-43** | **4-6** |

---

## Demo Script (Client Presentation)

1. Open the donation page — show impact story with animal photos
2. Make a test donation with card — show Stripe checkout
3. Show confirmation email in inbox
4. Log in as staff — show donation appear in dashboard
5. Show EUR amount with PYG equivalent
6. Export CSV — open in Excel
7. Show SEPA Direct Debit setup flow (test mode)
8. Show cookie consent banner and privacy policy

*"Your EU network can now donate directly. Every euro is tracked, receipted, and reportable."*

---

## Dependencies

- **Requires**: V1 frontend, CI/CD pipeline
- **Blocks V3**: Notification infrastructure built here reused for adoption + volunteer alerts
- **External**: Stripe merchant account, email domain verification, privacy policy legal review

---

*Epics touched: EPIC-3 (complete), EPIC-6 (partial), EPIC-7 (partial), EPIC-11 (partial)*
*Target release tag: `v2.0.0`*
