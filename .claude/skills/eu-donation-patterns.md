---
name: eu-donation-patterns
description: EU donation processing, GDPR compliance, and reporting patterns for Refugio Animal Paraguay. Load when working on donation features, EUR currency handling, or EU donor workflows.
triggers: donation, EUR, GDPR, EU donor, bank transfer, IBAN, tax receipt, European, SEPA, Stripe, PayPal, recurring donation, donor data
not-when: Payment gateway implementation details (use payment-patterns), general Python code (use python-patterns), REST API design (use rest-api-patterns)
---

# EU Donation Processing — Refugio Animal Paraguay

## Context

The shelter owner is Dutch, relocating to Paraguay. The primary funding network is European — EU donors represent the majority of donation revenue. All donation systems must handle EU requirements natively, not as an afterthought.

---

## Currency Handling

| Currency | Use Case | Storage |
|----------|----------|---------|
| EUR | EU donors (primary) | Store as `amount_eur NUMERIC(12,2)` |
| PYG | Local donors, local accounting | Store as `amount_pyg BIGINT` (no decimals) |
| USD | International / PayPal default | Store as `amount_usd NUMERIC(12,2)` |

**Exchange rate rule**: Convert at time of receipt, store both original currency amount AND PYG equivalent. Never recalculate historical conversions.

```sql
-- Donation record must store both
amount_original  NUMERIC(12,2) NOT NULL,  -- donor's currency
currency_code    CHAR(3)       NOT NULL,  -- EUR / USD / PYG
amount_pyg       BIGINT        NOT NULL,  -- at-receipt PYG rate
exchange_rate    NUMERIC(10,6) NOT NULL,  -- rate used for conversion
exchange_rate_at TIMESTAMPTZ   NOT NULL   -- when rate was fetched
```

**Exchange rate source**: Banco Central del Paraguay (BCP) official API
Endpoint: `https://www.bcp.gov.py/` — check current published API
Fallback: Open Exchange Rates API (free tier for non-commercial NGO)

---

## GDPR Compliance (EU Donors)

### What's required

- **Lawful basis**: Donation = contractual necessity for donor name + amount; consent required for marketing
- **Consent capture**: At donation form, before any data is stored
- **Right to erasure**: Donor personal data must be deletable without deleting the donation record
- **Data portability**: Donors can request a JSON/CSV export of their data
- **Privacy policy link**: Must appear on donation form, accessible before submission

### Soft-delete pattern (required for all donor PII)

```sql
-- donors table must have
created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
deleted_at   TIMESTAMPTZ          -- NULL = active, NOT NULL = erased
```

When a donor requests erasure:
1. Anonymize PII fields (name → "Anonymous Donor", email → NULL, address → NULL)
2. Set `deleted_at = NOW()`
3. Retain donation records with `donor_id` intact (financial records, 7-year retention)

### Data retention schedule

| Data Type | Retention | Basis |
|-----------|-----------|-------|
| Donation records | 7 years | Tax compliance (Dutch + Paraguayan) |
| Donor personal data | Until erasure request | GDPR consent |
| Bank transfer details | 7 years | AML/financial regulations |
| Email marketing consent | Until withdrawal | GDPR consent |

---

## Dutch/European Tax Receipts

### Required fields on donation receipt

1. Organization name (full legal name of the shelter)
2. Paraguayan registration number
3. Donor full name
4. Donor address
5. Donation amount (in original currency)
6. Donation date
7. Purpose of donation
8. Declaration of charitable use

### ANBI (Dutch charity status) considerations

- If the owner registers as ANBI-recognized organization in the Netherlands, Dutch donors can deduct donations from Dutch income tax
- ANBI requires annual financial transparency report
- Annual donor statements must be issued for donors who gave > €250 in a calendar year

### Annual donor statement fields

```
Year: [YYYY]
Donor: [Name]
Total donated: EUR [amount]
Donation dates: [list]
Organization: Refugio Animal Paraguay
Registration: [number]
Thank you message
```

---

## Payment Methods for EU Donors

| Method | Best For | Integration |
|--------|----------|-------------|
| IBAN bank transfer | Large one-time donations | Manual reconciliation or GoCardless |
| SEPA Direct Debit | Recurring monthly donors | GoCardless or Stripe |
| Credit/debit card | Impulse donations | Stripe |
| PayPal | Donors who prefer PayPal | PayPal SDK |
| iDEAL | Dutch donors specifically | Stripe (iDEAL support) |

**Recommended stack**: Stripe as primary (handles EUR, cards, SEPA, iDEAL via single API)

### Stripe webhook security

```python
# Always validate Stripe webhook signatures
import stripe

def handle_webhook(payload: bytes, sig_header: str) -> stripe.Event:
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid webhook signature")
    return event
```

---

## Recurring Donation Patterns

- Store subscription ID from payment provider, not payment method details
- Status transitions: `active → paused → cancelled → failed`
- Failed payment retry logic: 3 attempts over 7 days, then cancel with notification
- Cancellation: immediate effect, no partial refunds for current period

---

## Reporting Requirements

### For the shelter (internal)
- Monthly donation summary by currency
- Donor acquisition vs retention rates
- Campaign performance (if running targeted campaigns)

### For EU donors (external)
- Annual tax receipt (PDF, auto-generated)
- Donation acknowledgment email within 48 hours of receipt
- Impact report (optional but recommended for donor retention)

### For Dutch tax authorities (if ANBI)
- Annual financial statement
- Donor list (anonymized for < €500, named for > €500 as per Dutch law)
