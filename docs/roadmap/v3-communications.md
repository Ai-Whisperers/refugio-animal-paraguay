# V3 — Communications, Notifications & Adoption Workflow Completion

**Version**: 3.0.0
**Timeline**: Weeks 9-12 (after V2 launch)
**Prerequisites**: V2 complete (email provider live, donation flow working)
**Theme**: *"Nobody falls through the cracks — every adopter, donor, and volunteer gets timely updates"*

---

## Goal

Close the communication loop. Right now the system accepts data but doesn't talk back. V3 adds multi-channel notifications (email + WhatsApp), completes the adoption workflow with contracts and status updates, and adds local PYG payment options for Paraguayan donors. After V3, the platform is a complete adoption + donation system.

---

## What V3 Adds

### 1. Notification Engine (EPIC-6)

| Feature | Description | Priority |
|---------|-------------|----------|
| Notification service | Central dispatch: event in, message out (email/WhatsApp/in-app) | P0 |
| Email templates | Adoption status, donation receipt, welcome, password reset | P0 |
| WhatsApp Business API | Adoption updates, shift reminders (template messages) | P1 |
| In-app notifications | Bell icon with unread count in staff panel | P2 |
| Notification preferences | Users choose channels per event type | P1 |
| Template management | Staff can edit email/WhatsApp message templates | P2 |

### 2. Adoption Workflow Completion (EPIC-2)

| Feature | Description | Priority |
|---------|-------------|----------|
| Status notification events | Email/WhatsApp on: submitted, under review, approved, rejected | P0 |
| PDF adoption contract | Auto-generated with adopter + animal details, downloadable | P0 |
| Contract signing flow | Digital signature or checkbox confirmation | P1 |
| Duplicate application detection | Warn staff if same adopter applies for same animal | P1 |
| Adoption follow-up reminders | 30/60/90-day check-in emails to adopters | P2 |
| Adoption analytics | Approval rate, avg time-to-adopt, popular species | P2 |

### 3. Local Payment Methods (EPIC-3 completion)

| Feature | Description | Priority |
|---------|-------------|----------|
| Tigo Money integration | PYG donations via mobile money (Paraguay's dominant method) | P1 |
| Cash donation recording | Staff can log walk-in cash donations | P0 |
| Recurring donation management | Donors can pause/cancel recurring SEPA from their profile | P1 |
| Donation campaigns | Create named campaigns with goals and progress bars | P2 |

### 4. Public Portal Enhancements (EPIC-11 continuation)

| Feature | Description | Priority |
|---------|-------------|----------|
| Success stories page | Adopted animals with happy-ending photos | P1 |
| Contact form | General inquiries, routed to staff email | P0 |
| About the shelter page | Mission, team, location map | P1 |
| Multi-language foundation | Spanish (primary) + English (EU donors) toggle | P1 |
| SEO optimization | Meta tags, structured data, sitemap | P2 |

---

## Acceptance Criteria

V3 is complete when:

- [ ] Adopter receives email when application status changes
- [ ] Adopter receives WhatsApp message on approval (if phone provided)
- [ ] Staff receives notification when new application is submitted
- [ ] PDF adoption contract generates with correct adopter + animal data
- [ ] Adopter can download contract from their application status page
- [ ] Staff is warned about duplicate applications
- [ ] Cash donations can be recorded by staff
- [ ] Contact form submissions arrive in staff email
- [ ] Success stories page displays at least 3 adoption stories
- [ ] Spanish language support works across all public pages
- [ ] Notification preferences are respected (no unwanted messages)
- [ ] All new features have test coverage >80%

---

## What V3 Does NOT Include

- Volunteer management (V4)
- Medical records (V4)
- Admin analytics dashboard (V5)
- Advanced search / full-text (V5)
- Sponsorship / foster programs (V4)

---

## Technical Notes

### Notification Architecture

```
Event Bus (in-process for V3, upgrade to Redis in V5)
    │
    ├── EmailChannel
    │   └── Resend API (templates stored in DB)
    │
    ├── WhatsAppChannel
    │   └── Meta Cloud API (pre-approved templates)
    │
    └── InAppChannel
        └── DB notifications table + WebSocket push
```

### WhatsApp Business API

- Requires Meta Business verification (start in V2)
- Template messages only (no free-form until user initiates)
- Templates need Meta approval (submit during V2)
- Paraguay phone format: +595 9XX XXX XXX

### PDF Contract Generation

- Use `weasyprint` (Python) for HTML-to-PDF conversion
- Template: shelter letterhead, adopter details, animal details, terms
- Store generated PDF in object storage (S3 or local volume)
- Link from adoption request detail page

### Multi-language Strategy

- `next-intl` for Next.js i18n
- Default: Spanish (es-PY)
- Secondary: English (en) for EU donor pages
- Guarani: deferred to V5 (limited digital content available)

---

## Risk Register

| Risk | Impact | Mitigation |
|------|--------|------------|
| WhatsApp Business approval delays | Can't send WhatsApp notifications | Email-first, WhatsApp as enhancement |
| Tigo Money API documentation limited | Can't integrate local payments | Cash recording as fallback, manual reconciliation |
| PDF generation performance | Slow contract creation on low-spec server | Generate async, cache result |
| Translation quality | Spanish content sounds machine-translated | Human review of all public-facing strings |
| Notification spam | Users unsubscribe or report | Strict opt-in, preference center, rate limiting |

---

## Estimated Effort

| Area | New Tickets | Story Points | Weeks |
|------|-------------|-------------|-------|
| Notification engine + email | 3-4 | 10-13 | 1.5-2 |
| WhatsApp integration | 2 | 8 | 1 |
| Adoption workflow completion | 3-4 | 10-12 | 1.5-2 |
| Local payment methods | 2-3 | 8 | 1 |
| Public portal enhancements | 3-4 | 8-10 | 1-1.5 |
| Multi-language foundation | 2 | 5 | 0.5-1 |
| **Total** | **15-19** | **49-56** | **6-8** |

---

## Demo Script (Client Presentation)

1. Submit an adoption application as a public user
2. Show the email notification arriving in the adopter's inbox
3. Log in as staff — approve the application
4. Show WhatsApp message sent to adopter's phone
5. Download the PDF adoption contract
6. Record a cash donation from a walk-in donor
7. Show the contact form and success stories page
8. Toggle language to English — show EU donor experience

*"The shelter now communicates automatically. No more lost applications, no more manual follow-ups."*

---

## Dependencies

- **Requires**: V2 email infrastructure, V1 frontend
- **Blocks V4**: Volunteer notifications reuse this notification engine
- **External**: WhatsApp Business API approval, Tigo Money API access, translation services

---

*Epics touched: EPIC-2 (complete), EPIC-3 (complete), EPIC-6 (complete), EPIC-11 (continuation)*
*Target release tag: `v3.0.0`*
