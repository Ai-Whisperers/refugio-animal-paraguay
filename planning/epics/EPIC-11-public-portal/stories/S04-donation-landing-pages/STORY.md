# S04: Donation Landing Pages

## Story

As a **donor** (both EU/international and local Paraguay), I want to access dedicated donation landing pages with campaign details, donation form integration, and multiple payment methods so that I can easily contribute to the shelter's specific programs and see the impact of my donation.

## Context

Refugio Animal Paraguay relies heavily on donations from European network partners (EUR funding) and local supporters (PYG cash/transfers). Current state: no dedicated donation interface exists. This story enables transparent fundraising with:

- Campaign-based fundraising (e.g., "Medical Fund," "Food Program," "Building Expansion")
- Multi-currency support (EUR for EU donors, PYG for local, USD fallback)
- Payment processor integration (Stripe SEPA for EU, local payment methods for PYG)
- EU donor compliance (GDPR, donation receipts, tax reporting)
- Real-time progress tracking for campaigns
- Donor visibility into fund allocation

This story is critical for the shelter's financial sustainability and aligns with the Dutch owner's European fundraising network.

## Acceptance Criteria

**Given** a visitor lands on the donation page
**When** they select a campaign (Medical, Food, Operations, etc.)
**Then** they see:
- Campaign name, description, and impact story
- Current funds raised vs. target amount
- Progress bar showing percentage funded
- List of available payment methods based on their location

**Given** a donor initiates a donation for a campaign
**When** they enter amount and select payment method
**Then** the system:
- Validates amount against campaign minimum/maximum
- Routes to appropriate payment processor (Stripe SEPA for EUR, local processor for PYG)
- Creates a pending donation record with status "processing"
- Handles currency conversion for mixed-currency donations

**Given** a donor completes payment
**When** payment processor confirms transaction
**Then** the system:
- Updates donation status to "completed"
- Increments campaign funding total
- Sends confirmation email with donation receipt (EUR donors get tax-compliant receipt)
- Creates donor record if new (GDPR-compliant)
- Updates progress bar in real-time for all viewers

**Given** staff needs to manage campaigns
**When** they access admin panel
**Then** they can:
- Create new fundraising campaigns (name, description, target amount, deadline)
- Upload campaign images and impact stories
- Set minimum/maximum donation amounts
- Configure available payment methods per campaign
- View donation list with donor information (GDPR-masked)

**Given** an EU donor provides contact info
**When** they complete a donation
**Then** the system:
- Stores donation record with GDPR compliance (hash PII, no plain text)
- Generates downloadable tax receipt (for EU tax deduction)
- Adds donor to opt-in newsletter with explicit consent
- Creates audit log entry for compliance

**Given** campaign reaches its target funding
**When** target is met
**Then** the system:
- Displays "Campaign Complete" badge
- Disables further donations to that campaign (configurable)
- Sends notifications to admin and donors who supported it

## Definition of Done

- [ ] **Backend endpoints created**:
  - `GET /api/v1/campaigns` (list active campaigns with progress)
  - `GET /api/v1/campaigns/{id}` (campaign details + donation history aggregate)
  - `POST /api/v1/donations` (create donation, validate amount, initiate payment)
  - `GET /api/v1/donations/{id}` (get donation status)
  - `POST /api/v1/admin/campaigns` (create campaign, staff+ role)
  - `PATCH /api/v1/admin/campaigns/{id}` (update campaign, admin role)
  - `GET /api/v1/admin/campaigns/{id}/donations` (list donations for campaign)

- [ ] **Database schema created**:
  - `campaigns` table (id, name, description, target_amount, raised_amount, currency, deadline, image_url, impact_story, staff_id, created_at, updated_at, published boolean)
  - `donations` table (id, campaign_id, donor_id, amount_usd, amount_original, original_currency, payment_processor, processor_transaction_id, status, created_at, completed_at, receipt_url, soft_delete published flag)
  - `donors` table (id, email_hash, country_code, opt_in_newsletter, pii_encrypted, created_at) — GDPR-compliant, PII hashed/encrypted
  - Composite indexes: (campaign_id, status), (donor_id, created_at), (processor_transaction_id)

- [ ] **Payment processor integration**:
  - Stripe SEPA implementation for EUR donations (EU donors)
  - Local payment processor for PYG donations (details in T02)
  - Idempotent transaction handling (prevent duplicate charges)
  - Webhook handling for payment status updates

- [ ] **Frontend components created**:
  - Campaign list page with filtering (active/completed)
  - Campaign detail page with progress visualization
  - Donation form with amount input, payment method selector, GDPR consent checkbox
  - Payment success/failure pages
  - Admin campaign management interface (create, edit, publish, view donations)

- [ ] **Multilingual support**:
  - Campaign content supports Spanish (es), Dutch (nl), English (en)
  - Language fallback: es → nl → en
  - Email templates translated for all languages

- [ ] **Caching strategy**:
  - Campaign list cached 5 minutes (TTL)
  - Campaign detail cached 5 minutes (invalidate on donation/update)
  - In-memory cache with Redis fallback for distributed deployments

- [ ] **Security & compliance**:
  - PII encrypted at rest (email, donor names)
  - SQL injection prevention (parameterized queries)
  - CSRF protection on donation form
  - GDPR audit logging (who accessed what donor data, when)
  - EU-compliant donation receipts with tax ID and donation amount

- [ ] **Performance targets**:
  - Campaign list response: <500ms (cached), <1000ms (uncached)
  - Campaign detail response: <500ms
  - Donation creation response: <2000ms (includes payment processor round-trip)
  - Progress bar updates real-time via WebSocket or polling (max 5s latency)

- [ ] **Tests created**:
  - Unit tests: donation amount validation, currency conversion, campaign filtering
  - Integration tests: payment processor webhook handling, donation status updates, campaign progress calculation
  - E2E tests: full donation flow (form → payment → confirmation)
  - Coverage: 80% overall, 95% for payment critical path

- [ ] **Documentation created**:
  - API documentation (OpenAPI spec)
  - Payment processor integration guide
  - GDPR compliance guide for donors
  - Admin guide for campaign management

- [ ] **Code quality**:
  - Zero linting errors/warnings
  - Zero type check errors
  - All tests pass
  - No hardcoded secrets, credentials masked in logs

- [ ] **Deployed to staging**:
  - All endpoints accessible in staging environment
  - Payment processor in test mode
  - Admin can create test campaigns
  - E2E tests pass against staging

## Technical Notes

### Currency Handling (EUR + PYG)

Donation amounts stored in database as:
- `amount_usd`: Normalized to USD for comparison (1 source of truth)
- `amount_original`: Original amount as entered
- `original_currency`: EUR, PYG, or USD

Conversion happens at donation creation:
```
1 EUR = 1.10 USD (updated daily)
1 PYG = 0.00014 USD (updated daily)
```

Exchange rates sourced from OpenExchangeRates API or Stripe's built-in rates.

### Payment Processors

**Stripe SEPA** (EU donors, EUR):
- IBAN capture, SEPA Direct Debit
- Webhook: payment_intent.succeeded → update donation status
- EU tax receipt generation

**Local Processor** (Paraguay donors, PYG):
- Details in T02 (may be Stripe USD with local bank transfer, or regional provider)
- Cash donations logged manually by staff

### Webhook Security

All payment processor webhooks:
- Verified via signature (Stripe uses X-Stripe-Signature header)
- Processed idempotently (check processor_transaction_id for duplicates)
- Logged for audit trail

### Real-Time Progress Updates

Campaign progress bar updates:
- Option A: WebSocket connection for real-time push (preferred for EU donors watching live)
- Option B: 5-second polling for campaign progress (simpler, acceptable latency)

### GDPR Compliance for EU Donors

Donor PII never stored in plain text:
- Email: SHA256 hash (one-way)
- Name: AES-256 encrypted (reversible for receipt generation)
- Newsletter consent: stored separately, explicit opt-in
- Audit log: access requests, deletions, data exports

### Staff Access to Donor Data

Staff can view:
- Donor country (from IP geolocation, not stored)
- Donation amount and date
- Payment status
- Referral source (campaign ID)

Staff CANNOT view:
- Donor email address (hashed)
- Donor name (encrypted)
- Payment method details (PCI-DSS compliance)

### Donation Receipts

EU donors (EUR donations):
- Tax-compliant receipt with shelter tax ID
- Downloadable PDF with donation amount, date, shelter VAT number
- EU donors can print for tax deduction

PYG donors:
- Simple text receipt
- Email confirmation

## Story Points: 13

**Justification**:
- Multiple payment processors require integration and webhook handling
- GDPR compliance adds complexity (encryption, audit logging)
- Currency conversion and exchange rate management
- Real-time progress visualization
- Admin campaign management UI
- Comprehensive testing across payment flows
- Database schema with security considerations

## Related Stories

- **S03** (About & Educational): provides context on shelter mission that donation campaigns reference
- **S02** (Animal Listings): donation page links to specific animals (e.g., "Help Fluffy with medical expenses")
- **S05** (Volunteer Program): donation page can feature volunteer opportunities alongside fundraising

## Dependencies

- Stripe account setup (business account with SEPA capability)
- Local payment processor configuration (identified in T02)
- Email template system (for receipts, created in S03 or earlier)
- GDPR compliance framework (encryption keys, audit logging infrastructure)

## Risks

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Payment processor integration delays | 4 weeks setback | Start Stripe SEPA setup immediately; have local processor as fallback |
| PII encryption overhead | Slow donor creation | Use cached encryption keys; batch encrypt on migration |
| GDPR audit logging performance | Slow donation endpoint | Async logging to queue; separate audit database |
| Currency rate staleness | Incorrect donations | Update rates hourly; alert if update fails |
| Webhook timeout/retry storms | Duplicate donations | Idempotent transaction IDs; deduplication logic |

---

**Created**: 2026-03-25
**Status**: Ready for sprint planning
**Assignee**: Pending sprint allocation
