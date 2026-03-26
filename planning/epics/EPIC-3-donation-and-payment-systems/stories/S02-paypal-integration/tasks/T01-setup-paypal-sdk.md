---
task: T01
story: S02
epic: EPIC-3
title: Setup EU bank transfer (SEPA) service
status: ready
priority: medium
created: 2026-03-25T17:13:26.729178
---

# T01: Setup EU Bank Transfer (SEPA) Service

## Description

Implement the backend service for EU bank transfer / SEPA donations. PayPal is not the right tool for this shelter — the donor base is primarily European (Dutch owner, EU network), and SEPA bank transfer is the standard low-cost method used by European NGOs. This task sets up the service layer: bank account configuration, payment reference code generation, and the Supabase table structure for tracking pending transfers.

> **Tech note**: This story was originally labeled "PayPal integration" but PayPal is incorrect for this context. European donors strongly prefer direct bank transfer (SEPA) for charitable giving — it carries no PayPal fees, works with any EU bank, and is standard for NGO donations.

## Acceptance Criteria

- [ ] `BankTransferService` class created at `src/lib/payments/bank-transfer-service.ts`
- [ ] IBAN and BIC/SWIFT stored in environment variables, never hardcoded
- [ ] `generatePaymentReference()` produces unique, collision-resistant reference codes
- [ ] Reference codes follow the format `RAP-YYYYMMDD-XXXXXX` (human-readable, 6-char random suffix)
- [ ] `createBankTransferDonation()` Server Action inserts a pending donation record
- [ ] IBAN validation utility rejects malformed IBANs before persisting
- [ ] `bank_transfer_donations` view or table tracks transfer status (pending → confirmed → failed)
- [ ] Unit tests for reference generation (uniqueness, format) and IBAN validation

## Implementation Notes

### Environment Variables

```bash
# .env.local
BANK_IBAN=NL91ABNA0417164300        # Shelter's Dutch IBAN
BANK_BIC=ABNANL2A                   # BIC/SWIFT of the bank
BANK_ACCOUNT_NAME="Refugio Animal Paraguay"
BANK_ACCOUNT_CITY="Amsterdam"        # City where account is held
```

Never read these client-side. All bank detail rendering must happen in Server Components.

### File Structure

```
src/
└── lib/
    └── payments/
        ├── bank-transfer-service.ts    ← Service class (this task)
        ├── iban-validator.ts           ← IBAN validation utility
        └── stripe-service.ts           ← Existing (T01)
```

### IBAN Validator

```typescript
// src/lib/payments/iban-validator.ts

// IBAN character values for mod-97 check (A=10, B=11, ..., Z=35)
const IBAN_CHAR_VALUES: Record<string, string> = {}
for (let i = 0; i < 26; i++) {
  IBAN_CHAR_VALUES[String.fromCharCode(65 + i)] = String(10 + i)
}

export type IBANValidationResult =
  | { valid: true; formatted: string; countryCode: string }
  | { valid: false; reason: string }

export function validateIBAN(raw: string): IBANValidationResult {
  // Normalize: remove spaces and uppercase
  const iban = raw.replace(/\s/g, '').toUpperCase()

  if (iban.length < 15 || iban.length > 34) {
    return { valid: false, reason: 'IBAN must be between 15 and 34 characters' }
  }

  const countryCode = iban.slice(0, 2)
  if (!/^[A-Z]{2}$/.test(countryCode)) {
    return { valid: false, reason: 'IBAN must start with a 2-letter country code' }
  }

  // Rearrange: move first 4 chars to end, then replace letters with numbers
  const rearranged = iban.slice(4) + iban.slice(0, 4)
  const numeric = rearranged
    .split('')
    .map((char) => IBAN_CHAR_VALUES[char] ?? char)
    .join('')

  // Mod-97 check using BigInt for large numbers
  const remainder = BigInt(numeric) % BigInt(97)
  if (remainder !== BigInt(1)) {
    return { valid: false, reason: 'IBAN checksum is invalid' }
  }

  // Format with spaces every 4 chars for display
  const formatted = iban.match(/.{1,4}/g)!.join(' ')
  return { valid: true, formatted, countryCode }
}
```

### Bank Transfer Service

```typescript
// src/lib/payments/bank-transfer-service.ts

export interface BankDetails {
  iban: string
  bic: string
  accountName: string
  accountCity: string
}

export interface BankTransferDonation {
  id: string
  reference: string
  amount: number
  currency: 'eur'          // SEPA is EUR only
  donorName: string
  donorEmail: string
  bankDetails: BankDetails
  status: 'pending_transfer' | 'confirmed' | 'failed'
  createdAt: string
  expiresAt: string        // Transfers expire after 30 days
}

export type CreateBankTransferResult =
  | { success: true; donation: BankTransferDonation }
  | { success: false; error: string }

export class BankTransferService {
  private readonly bankDetails: BankDetails

  constructor() {
    // Read from env — throws at startup if misconfigured rather than at runtime
    const iban = process.env.BANK_IBAN
    const bic = process.env.BANK_BIC
    const accountName = process.env.BANK_ACCOUNT_NAME
    const accountCity = process.env.BANK_ACCOUNT_CITY

    if (!iban || !bic || !accountName || !accountCity) {
      throw new Error(
        'Bank transfer service is missing required environment variables: ' +
        'BANK_IBAN, BANK_BIC, BANK_ACCOUNT_NAME, BANK_ACCOUNT_CITY',
      )
    }

    this.bankDetails = { iban, bic, accountName, accountCity }
  }

  getBankDetails(): BankDetails {
    return { ...this.bankDetails }
  }

  generatePaymentReference(): string {
    const date = new Date()
    const dateStr = [
      date.getFullYear(),
      String(date.getMonth() + 1).padStart(2, '0'),
      String(date.getDate()).padStart(2, '0'),
    ].join('')

    // 6 random alphanumeric characters (uppercase only — easier for donors to type)
    const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789' // removed ambiguous I, O, 0, 1
    const suffix = Array.from(
      { length: 6 },
      () => chars[Math.floor(Math.random() * chars.length)],
    ).join('')

    return `RAP-${dateStr}-${suffix}`
  }

  async createDonation(params: {
    amount: number
    donorName: string
    donorEmail: string
    campaignId?: string
    donorUserId?: string | null
  }): Promise<CreateBankTransferResult> {
    try {
      const reference = this.generatePaymentReference()
      const expiresAt = new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString()

      return {
        success: true,
        donation: {
          id: crypto.randomUUID(),
          reference,
          amount: params.amount,
          currency: 'eur',
          donorName: params.donorName,
          donorEmail: params.donorEmail,
          bankDetails: this.bankDetails,
          status: 'pending_transfer',
          createdAt: new Date().toISOString(),
          expiresAt,
        },
      }
    } catch (err) {
      return {
        success: false,
        error: err instanceof Error ? err.message : 'Failed to create bank transfer donation',
      }
    }
  }
}

// Singleton — constructed once at module load
export const bankTransferService = new BankTransferService()
```

### Supabase Migration

```sql
-- Migration: bank_transfer_donations table
CREATE TABLE IF NOT EXISTS bank_transfer_donations (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  payment_reference TEXT UNIQUE NOT NULL,      -- e.g. RAP-20260325-AB3KLM
  amount            INTEGER NOT NULL,           -- in euro cents
  currency          TEXT NOT NULL DEFAULT 'eur' CHECK (currency = 'eur'),
  donor_name        TEXT NOT NULL,
  donor_email       TEXT NOT NULL,
  donor_user_id     UUID REFERENCES auth.users(id),  -- nullable for anonymous
  campaign_id       UUID REFERENCES campaigns(id),   -- nullable
  status            TEXT NOT NULL DEFAULT 'pending_transfer'
                    CHECK (status IN ('pending_transfer', 'confirmed', 'failed', 'expired')),
  expires_at        TIMESTAMPTZ NOT NULL,
  confirmed_at      TIMESTAMPTZ,                     -- when staff marks as confirmed
  confirmed_by      UUID REFERENCES auth.users(id),  -- staff who confirmed
  notes             TEXT,                            -- staff notes
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index for lookups by reference (used in payment confirmation flow)
CREATE INDEX idx_bank_transfer_donations_reference
  ON bank_transfer_donations (payment_reference);

-- Index for pending transfers report (staff dashboard)
CREATE INDEX idx_bank_transfer_donations_status
  ON bank_transfer_donations (status, created_at);

-- RLS: donors can see their own transfers
ALTER TABLE bank_transfer_donations ENABLE ROW LEVEL SECURITY;

CREATE POLICY "donors_view_own_transfers"
  ON bank_transfer_donations FOR SELECT
  USING (donor_user_id = auth.uid());

CREATE POLICY "staff_view_all_transfers"
  ON bank_transfer_donations FOR ALL
  USING (
    EXISTS (
      SELECT 1 FROM user_roles
      WHERE user_id = auth.uid() AND role IN ('staff', 'admin')
    )
  );
```

### Unit Tests

```typescript
// src/lib/payments/__tests__/bank-transfer-service.test.ts
import { bankTransferService } from '../bank-transfer-service'
import { validateIBAN } from '../iban-validator'

describe('BankTransferService.generatePaymentReference', () => {
  it('generates references matching the expected format', () => {
    const ref = bankTransferService.generatePaymentReference()
    expect(ref).toMatch(/^RAP-\d{8}-[A-Z0-9]{6}$/)
  })

  it('generates unique references on repeated calls', () => {
    const refs = new Set(Array.from({ length: 100 }, () =>
      bankTransferService.generatePaymentReference()
    ))
    expect(refs.size).toBe(100)
  })
})

describe('validateIBAN', () => {
  it('accepts a valid Dutch IBAN', () => {
    const result = validateIBAN('NL91 ABNA 0417 1643 00')
    expect(result.valid).toBe(true)
    if (result.valid) {
      expect(result.countryCode).toBe('NL')
      expect(result.formatted).toBe('NL91 ABNA 0417 1643 00')
    }
  })

  it('rejects an IBAN with wrong checksum', () => {
    const result = validateIBAN('NL91ABNA0417164301')  // last digit changed
    expect(result.valid).toBe(false)
  })

  it('rejects strings that are too short', () => {
    const result = validateIBAN('NL91')
    expect(result.valid).toBe(false)
  })
})
```

## Related Issues

- EPIC-3
- S02
- T02 (uses this service to render SEPA instructions UI)
