# ADR-0001: Use Stripe for EU Donor Payment Processing

**Date**: 2026-03-25
**Status**: Accepted

## Context

Refugio Animal Paraguay has a significant European donor base, particularly Dutch and German donors. The shelter owner is relocating from the Netherlands and has an existing network of EU supporters.

We need a payment processor that:
- Accepts EUR payments via credit/debit cards
- Supports SEPA Direct Debit for recurring monthly donations
- Provides a webhook-based integration for reliable payment confirmation
- Complies with EU Strong Customer Authentication (SCA/PSD2)
- Handles GDPR data processing requirements
- Works with a Paraguayan-registered organization receiving EUR

The team has Python/FastAPI backend experience. Budget is limited — we need a processor with competitive fees and no monthly minimums.

## Decision

We will use Stripe for all EU and international donor payment processing because it is the most mature API for EUR + SEPA recurring donations, has Python SDK support, and provides built-in SCA/PSD2 compliance.

## Alternatives Considered

### Option A: PayPal
- Pro: Globally recognized brand — donors trust it
- Pro: No setup fee, easy onboarding
- Con: Higher transaction fees (3.5-4.5% vs Stripe's 1.4-2.9%)
- Con: No native SEPA Direct Debit support
- Con: Worse developer API — webhook reliability issues documented
- Con: Account freezes on "high-risk" categories (animal rescue sometimes flagged)

### Option B: Mollie
- Pro: Netherlands-based — very donor-friendly for Dutch supporters
- Pro: Excellent SEPA support, iDEAL (Dutch bank transfer) support
- Pro: Lower fees for EU-to-EU transactions
- Con: Less Python SDK support than Stripe
- Con: Smaller global reach for non-EU donors
- Con: No Paraguay-specific presence for future local payment integration

### Option C: Stripe ← chosen
- Pro: Best Python SDK, extensive documentation
- Pro: Native SEPA Direct Debit + subscription billing
- Pro: SCA/PSD2 compliant out of the box (PaymentIntents API)
- Pro: Works for organization based outside EU receiving EUR
- Pro: Webhook reliability is excellent (retry logic built-in)
- Pro: Competitive EU fees: 1.4% + €0.25 (cards), 0.8% (SEPA)
- Con: Not well-known to Paraguayan donors (local donations handled separately)
- Con: PYG not supported — local donations need a separate flow

## Consequences

**Positive outcomes:**
- EU donors can pay with card or set up recurring SEPA donations in one flow
- PSD2/SCA compliance is handled by Stripe — no custom implementation
- Webhook-based architecture means donations are confirmed asynchronously (reliable)
- Stripe Dashboard gives the shelter owner real-time donation visibility

**Negative outcomes / trade-offs:**
- Local (PYG) donations require a separate solution (bank transfer, cash) — not handled by Stripe
- Stripe fees apply: ~1.4-2.9% per EU card transaction
- Integration complexity: need to handle PaymentIntents, webhooks, and SEPA mandate flows

**Risks and mitigations:**
- Risk: Stripe account freeze for "animal rescue" category → Mitigation: Register as nonprofit/NGO, maintain clear website showing legitimate operation
- Risk: EUR → PYG conversion costs → Mitigation: Stripe pays out in EUR to a European account; conversion happens at owner's discretion
- Risk: SEPA mandate complexity → Mitigation: Use Stripe's hosted mandate pages rather than building custom UI

## Compliance Notes

- **GDPR**: Stripe is a Data Processor under GDPR. Standard Contractual Clauses (SCCs) apply automatically via Stripe's DPA. Donor card data is never stored on our servers (Stripe tokenizes it).
- **PSD2/SCA**: PaymentIntents API handles 3D Secure authentication natively — no custom SCA implementation needed.
- **Paraguayan law**: Stripe operates as the payment intermediary. The shelter is responsible for local tax reporting on received funds.

## Related ADRs

- ADR-0002: Local (PYG) Donation Handling (TBD — covers cash and local bank transfer flow)
