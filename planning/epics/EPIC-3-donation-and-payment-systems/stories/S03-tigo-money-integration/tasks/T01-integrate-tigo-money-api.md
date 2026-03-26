---
task: T01
story: S03
epic: EPIC-3
title: Integrate Tigo Money API
status: ready
priority: medium
created: 2026-03-25T17:13:26.729429
---

# T01: Integrate Tigo Money API

## Description

Implement the service layer for Tigo Money, Paraguay's dominant mobile wallet payment method. Tigo Money enables donors in Paraguay to donate from their mobile wallet using their phone number (0981-XXXXXXX format). This task covers the API client, payment initiation, phone number normalization, and the Supabase table for tracking Tigo Money transactions.

**Tigo Money context**: Tigo Money (by Millicom/Tigo Paraguay) is the most widely used mobile payment method in Paraguay. It is used by a large portion of the population and is the standard method for low-to-medium value transactions in PYG. The API uses OAuth2 for authentication and supports `push payment` (charge initiation — customer approves on their phone) and `pull payment` (customer initiates transfer).

> **Note**: Tigo Money's production API requires a Tigo merchant account. For development, use their sandbox environment. API credentials and base URLs differ between environments and must be stored in environment variables.

## Acceptance Criteria

- [ ] `TigoMoneyService` class created at `src/lib/payments/tigo-money-service.ts`
- [ ] OAuth2 token fetching with automatic token refresh (client credentials flow)
- [ ] `initiatePayment()` sends a push payment charge request to donor's phone number
- [ ] `checkPaymentStatus()` polls or queries the transaction status
- [ ] Paraguay phone numbers normalized to E.164 format (`09XXXXXXXX` → `+595XXXXXXXXX`)
- [ ] Phone number validator rejects numbers outside Paraguay
- [ ] `tigo_money_donations` table created via migration
- [ ] Environment variables documented in `.env.example`
- [ ] Unit tests for phone normalization, token caching, and error handling

## Implementation Notes

### Environment Variables

```bash
# .env.local
TIGO_MONEY_CLIENT_ID=your_client_id
TIGO_MONEY_CLIENT_SECRET=your_client_secret
TIGO_MONEY_MERCHANT_ID=your_merchant_id
TIGO_MONEY_BASE_URL=https://securesandbox.tigo.com   # dev
# TIGO_MONEY_BASE_URL=https://secure.tigo.com        # production
TIGO_MONEY_CALLBACK_URL=https://your-domain.com/api/tigo-money/callback
```

### Phone Number Utilities

```typescript
// src/lib/payments/tigo-money-phone.ts

export type PhoneNormalizationResult =
  | { valid: true; e164: string; display: string }
  | { valid: false; reason: string }

/**
 * Normalize a Paraguay Tigo/personal mobile number to E.164 format.
 * Paraguay country code: +595
 * Mobile numbers: start with 09, 8 digits after the leading 0
 * Tigo network prefixes: 0981, 0982, 0983, 0984, 0985, 0986, 0987
 * Personal network prefixes: 0976, 0975, etc. (also valid for Tigo Money)
 */
export function normalizeParaguayPhone(raw: string): PhoneNormalizationResult {
  // Remove all non-digit characters
  const digits = raw.replace(/\D/g, '')

  // Accept formats: 09XXXXXXXX (10 digits), 9XXXXXXXX (9 digits),
  // 595XXXXXXXXX (12 digits with country code)
  let normalized: string

  if (digits.startsWith('595') && digits.length === 12) {
    // Already has country code: 595XXXXXXXXX
    normalized = digits
  } else if (digits.startsWith('09') && digits.length === 10) {
    // Local format: 09XXXXXXXX → 5959XXXXXXXX
    normalized = '595' + digits.slice(1)
  } else if (digits.startsWith('9') && digits.length === 9) {
    // Without leading 0: 9XXXXXXXX → 5959XXXXXXXX
    normalized = '595' + digits
  } else {
    return {
      valid: false,
      reason: 'El número debe tener 10 dígitos (ej: 0981-123-456)',
    }
  }

  // Validate it's a mobile number (Paraguay mobiles start with 5959X)
  if (!normalized.startsWith('5959')) {
    return {
      valid: false,
      reason: 'Solo se aceptan números de teléfono celular de Paraguay',
    }
  }

  const e164 = `+${normalized}`
  // Format for display: +595 981 123 456
  const display = `+595 ${normalized.slice(3, 6)} ${normalized.slice(6, 9)} ${normalized.slice(9)}`

  return { valid: true, e164, display }
}
```

### Tigo Money Service

```typescript
// src/lib/payments/tigo-money-service.ts

const TIGO_BASE_URL = process.env.TIGO_MONEY_BASE_URL!
const TIGO_CLIENT_ID = process.env.TIGO_MONEY_CLIENT_ID!
const TIGO_CLIENT_SECRET = process.env.TIGO_MONEY_CLIENT_SECRET!
const TIGO_MERCHANT_ID = process.env.TIGO_MONEY_MERCHANT_ID!
const TIGO_CALLBACK_URL = process.env.TIGO_MONEY_CALLBACK_URL!

interface TigoToken {
  accessToken: string
  expiresAt: number   // unix timestamp in ms
}

export type TigoPaymentStatus = 'pending' | 'approved' | 'rejected' | 'expired' | 'failed'

export interface TigoPaymentResult {
  transactionId: string
  status: TigoPaymentStatus
  tigoReference?: string   // Tigo's internal reference number
}

export type InitiatePaymentResult =
  | { success: true; transactionId: string; status: TigoPaymentStatus }
  | { success: false; error: string; code?: string }

export class TigoMoneyService {
  private cachedToken: TigoToken | null = null

  private async getAccessToken(): Promise<string> {
    // Return cached token if still valid (with 60s buffer)
    if (this.cachedToken && this.cachedToken.expiresAt > Date.now() + 60_000) {
      return this.cachedToken.accessToken
    }

    const res = await fetch(`${TIGO_BASE_URL}/v3/oauth/accesstoken`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({
        grant_type: 'client_credentials',
        client_id: TIGO_CLIENT_ID,
        client_secret: TIGO_CLIENT_SECRET,
      }),
    })

    if (!res.ok) {
      const body = await res.text()
      throw new Error(`Tigo Money OAuth failed (${res.status}): ${body}`)
    }

    const data = await res.json()
    this.cachedToken = {
      accessToken: data.access_token,
      expiresAt: Date.now() + data.expires_in * 1000,
    }

    return this.cachedToken.accessToken
  }

  async initiatePayment(params: {
    transactionId: string    // our internal UUID
    phoneE164: string        // donor's phone in E.164 (+595...)
    amountPyg: number        // PYG — whole numbers only (no cents)
    description: string      // shown to donor on phone prompt
  }): Promise<InitiatePaymentResult> {
    try {
      const token = await this.getAccessToken()

      const res = await fetch(
        `${TIGO_BASE_URL}/v3/tigo-money/${TIGO_MERCHANT_ID}/payments`,
        {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            MasterMerchant: { Account: TIGO_MERCHANT_ID },
            Subscriber: {
              Account: params.phoneE164,
              CountryCode: '595',
              CountryName: 'Paraguay',
              BusinessName: 'Refugio Animal Paraguay',
            },
            Amount: params.amountPyg.toString(),   // PYG — no decimals
            CurrencyCode: 'PYG',
            DueDate: new Date(Date.now() + 15 * 60 * 1000).toISOString(), // 15 min to approve
            ClientTransactionId: params.transactionId,
            Redirection: { ReturnUrl: TIGO_CALLBACK_URL },
            Originator: { Remarks: params.description },
          }),
        },
      )

      const data = await res.json()

      if (!res.ok) {
        return {
          success: false,
          error: data.Error?.Message ?? 'Payment initiation failed',
          code: data.Error?.Code,
        }
      }

      return {
        success: true,
        transactionId: params.transactionId,
        status: 'pending',   // donor must approve on their phone
      }
    } catch (err) {
      return {
        success: false,
        error: err instanceof Error ? err.message : 'Network error contacting Tigo Money API',
      }
    }
  }

  async checkPaymentStatus(tigoTransactionId: string): Promise<TigoPaymentResult> {
    const token = await this.getAccessToken()

    const res = await fetch(
      `${TIGO_BASE_URL}/v3/tigo-money/${TIGO_MERCHANT_ID}/payments/${tigoTransactionId}`,
      {
        headers: { Authorization: `Bearer ${token}` },
      },
    )

    const data = await res.json()

    const STATUS_MAP: Record<string, TigoPaymentStatus> = {
      PENDING: 'pending',
      SUCCESS: 'approved',
      FAILED: 'failed',
      REJECTED: 'rejected',
      EXPIRED: 'expired',
    }

    return {
      transactionId: tigoTransactionId,
      status: STATUS_MAP[data.Status] ?? 'failed',
      tigoReference: data.TigoReference,
    }
  }
}

export const tigoMoneyService = new TigoMoneyService()
```

### Supabase Migration

```sql
-- Migration: tigo_money_donations table
CREATE TABLE IF NOT EXISTS tigo_money_donations (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tigo_transaction_id   TEXT,                              -- Tigo's reference (set after initiation)
  amount                INTEGER NOT NULL,                  -- PYG whole number (no cents)
  currency              TEXT NOT NULL DEFAULT 'pyg'
                        CHECK (currency = 'pyg'),
  donor_phone_e164      TEXT NOT NULL,                    -- +595XXXXXXXXX
  donor_name            TEXT NOT NULL,
  donor_email           TEXT,                             -- nullable (not required for Tigo)
  donor_user_id         UUID REFERENCES auth.users(id),  -- nullable for anonymous
  campaign_id           UUID REFERENCES campaigns(id),
  status                TEXT NOT NULL DEFAULT 'pending'
                        CHECK (status IN (
                          'pending',       -- awaiting donor approval on phone
                          'approved',      -- donor approved, money transferred
                          'rejected',      -- donor rejected the charge
                          'expired',       -- timed out (15 min approval window)
                          'failed'         -- technical failure
                        )),
  tigo_reference        TEXT,                             -- Tigo's internal number
  failure_reason        TEXT,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_tigo_donations_status ON tigo_money_donations (status, created_at);
CREATE INDEX idx_tigo_donations_phone ON tigo_money_donations (donor_phone_e164);
CREATE INDEX idx_tigo_donations_tigo_id ON tigo_money_donations (tigo_transaction_id);

ALTER TABLE tigo_money_donations ENABLE ROW LEVEL SECURITY;

CREATE POLICY "donors_view_own_tigo_donations"
  ON tigo_money_donations FOR SELECT
  USING (donor_user_id = auth.uid());

CREATE POLICY "staff_manage_tigo_donations"
  ON tigo_money_donations FOR ALL
  USING (
    EXISTS (
      SELECT 1 FROM user_roles
      WHERE user_id = auth.uid() AND role IN ('staff', 'admin')
    )
  );
```

### Unit Tests

```typescript
// src/lib/payments/__tests__/tigo-money-phone.test.ts
import { normalizeParaguayPhone } from '../tigo-money-phone'

describe('normalizeParaguayPhone', () => {
  it('normalizes local format 09XXXXXXXX', () => {
    const result = normalizeParaguayPhone('0981123456')
    expect(result.valid).toBe(true)
    if (result.valid) expect(result.e164).toBe('+595981123456')
  })

  it('normalizes with dashes: 0981-123-456', () => {
    const result = normalizeParaguayPhone('0981-123-456')
    expect(result.valid).toBe(true)
    if (result.valid) expect(result.e164).toBe('+595981123456')
  })

  it('accepts already-prefixed 595XXXXXXXXX', () => {
    const result = normalizeParaguayPhone('595981123456')
    expect(result.valid).toBe(true)
    if (result.valid) expect(result.e164).toBe('+595981123456')
  })

  it('rejects numbers that are too short', () => {
    const result = normalizeParaguayPhone('09811234')
    expect(result.valid).toBe(false)
  })

  it('rejects landline numbers (do not start with 9)', () => {
    const result = normalizeParaguayPhone('0211234567') // Asunción landline
    expect(result.valid).toBe(false)
  })
})
```

## Related Issues

- EPIC-3
- S03
- T02 (implements the UI that uses this service)
