---
task: T01
story: S01
epic: EPIC-6
title: Setup email provider
status: ready
priority: medium
created: 2026-03-25T17:13:26.732609
---

# T01: Setup email provider

## Description

Integrate Resend as the email provider for transactional emails (adoption confirmations,
donation receipts, volunteer notifications). Implement a thin `sendEmail()` wrapper around
the Resend SDK, configure environment variables, and establish the fire-and-forget pattern
used by all Server Actions.

**Provider choice**: Resend — simple REST API, excellent deliverability, generous free tier,
no SendGrid/Mailgun complexity. Works directly from Next.js Server Actions and Supabase Edge
Functions without an external queue.

**No queue**: Email sends are inline in Server Actions. Resend handles retries at the SDK
level. If a non-critical email fails, we log the error and continue. If a critical email
fails (adoption confirmation), we surface the error to the admin UI but do not block the
database operation.

---

## Acceptance Criteria

- [ ] `RESEND_API_KEY` environment variable documented in `.env.example`
- [ ] `src/lib/email/send-email.ts` wrapper created with typed `EmailPayload` interface
- [ ] Wrapper function handles Resend SDK errors and returns structured `{ error? }` result
- [ ] `FROM_EMAIL` constant defined and used everywhere (no hardcoded from-addresses)
- [ ] Vitest unit tests for the wrapper's error-handling paths (mock Resend SDK)
- [ ] Resend SDK installed (`resend` npm package)
- [ ] `src/lib/email/__tests__/send-email.test.ts` with 6 passing tests

---

## Implementation Notes

### 1. Install dependency

```bash
npm install resend
```

### 2. Environment variables

`.env.example`:
```
# Email — Resend (https://resend.com)
RESEND_API_KEY=re_your_api_key_here
FROM_EMAIL=no-reply@refugioanimalpy.org
```

`.env.local` (developer's actual key, never committed):
```
RESEND_API_KEY=re_live_xxxxxxxxxxxxxxxxxxxx
FROM_EMAIL=no-reply@refugioanimalpy.org
```

### 3. Email wrapper — `src/lib/email/send-email.ts`

```typescript
import { Resend } from 'resend';

// Single Resend client instance — lazy-initialized to avoid build-time errors
// when RESEND_API_KEY is not set in all environments.
let _resend: Resend | null = null;

function getResendClient(): Resend {
  if (!_resend) {
    const apiKey = process.env.RESEND_API_KEY;
    if (!apiKey) {
      throw new Error('RESEND_API_KEY environment variable is not set');
    }
    _resend = new Resend(apiKey);
  }
  return _resend;
}

export const FROM_EMAIL =
  process.env.FROM_EMAIL ?? 'no-reply@refugioanimalpy.org';

export interface EmailPayload {
  to: string | string[];
  subject: string;
  html: string;
  /** Optional plain-text fallback (improves deliverability) */
  text?: string;
  /** Reply-to address, e.g. the staff member who approved adoption */
  replyTo?: string;
}

export interface SendEmailResult {
  messageId?: string;
  error?: string;
}

/**
 * Send a transactional email via Resend.
 *
 * Returns { messageId } on success or { error } on failure.
 * Never throws — callers decide whether the error is fatal.
 *
 * Usage in a Server Action:
 *   const result = await sendEmail({ to, subject, html });
 *   if (result.error) {
 *     console.error('[sendEmail] Failed:', result.error);
 *     // surface to UI or ignore depending on criticality
 *   }
 */
export async function sendEmail(
  payload: EmailPayload
): Promise<SendEmailResult> {
  try {
    const resend = getResendClient();
    const { data, error } = await resend.emails.send({
      from: FROM_EMAIL,
      to: payload.to,
      subject: payload.subject,
      html: payload.html,
      text: payload.text,
      reply_to: payload.replyTo,
    });

    if (error) {
      return { error: error.message };
    }

    return { messageId: data?.id };
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    return { error: message };
  }
}
```

### 4. Unit tests — `src/lib/email/__tests__/send-email.test.ts`

The tests mock the `resend` module so no real HTTP calls are made.

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest';

// Mock the Resend SDK before importing the module under test
vi.mock('resend', () => {
  const mockSend = vi.fn();
  return {
    Resend: vi.fn().mockImplementation(() => ({
      emails: { send: mockSend },
    })),
    __mockSend: mockSend,
  };
});

// Import after mock is set up
import { sendEmail } from '../send-email';
import * as ResendModule from 'resend';

// Helper to access the mocked send function
function getMockSend() {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  return (ResendModule as any).__mockSend as ReturnType<typeof vi.fn>;
}

const VALID_PAYLOAD = {
  to: 'adopter@example.com',
  subject: 'Confirmación de adopción',
  html: '<p>Su solicitud fue aprobada</p>',
};

describe('sendEmail', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    process.env.RESEND_API_KEY = 're_test_key';
    process.env.FROM_EMAIL = 'test@example.org';
  });

  it('returns messageId on successful send', async () => {
    getMockSend().mockResolvedValueOnce({
      data: { id: 'msg_abc123' },
      error: null,
    });

    const result = await sendEmail(VALID_PAYLOAD);

    expect(result.messageId).toBe('msg_abc123');
    expect(result.error).toBeUndefined();
  });

  it('returns error string when Resend API returns an error object', async () => {
    getMockSend().mockResolvedValueOnce({
      data: null,
      error: { message: 'Invalid API key' },
    });

    const result = await sendEmail(VALID_PAYLOAD);

    expect(result.error).toBe('Invalid API key');
    expect(result.messageId).toBeUndefined();
  });

  it('returns error string when SDK throws an exception', async () => {
    getMockSend().mockRejectedValueOnce(new Error('Network timeout'));

    const result = await sendEmail(VALID_PAYLOAD);

    expect(result.error).toBe('Network timeout');
    expect(result.messageId).toBeUndefined();
  });

  it('never throws — returns error object instead', async () => {
    getMockSend().mockRejectedValueOnce(new Error('ECONNREFUSED'));

    await expect(sendEmail(VALID_PAYLOAD)).resolves.not.toThrow();
    const result = await sendEmail(VALID_PAYLOAD);
    expect(result.error).toBeDefined();
  });

  it('passes replyTo address to Resend when provided', async () => {
    getMockSend().mockResolvedValueOnce({
      data: { id: 'msg_xyz' },
      error: null,
    });

    await sendEmail({ ...VALID_PAYLOAD, replyTo: 'staff@refugio.org' });

    expect(getMockSend()).toHaveBeenCalledWith(
      expect.objectContaining({ reply_to: 'staff@refugio.org' })
    );
  });

  it('returns error when RESEND_API_KEY is not set', async () => {
    delete process.env.RESEND_API_KEY;
    // Reset the cached client so it re-checks the env var
    vi.resetModules();
    const { sendEmail: freshSendEmail } = await import('../send-email');

    const result = await freshSendEmail(VALID_PAYLOAD);

    expect(result.error).toMatch(/RESEND_API_KEY/);
  });
});
```

### 5. Fire-and-forget pattern for non-critical emails

In Server Actions, email is a side effect. Non-critical emails (e.g. volunteer
shift reminder) should not block or surface errors to the user:

```typescript
// src/app/actions/some-action.ts
'use server';

import { sendEmail } from '@/lib/email/send-email';

export async function approveAdoptionRequest(requestId: string) {
  // ... database operations ...

  // Non-blocking: fire email and log failure without surfacing to user
  sendEmail({
    to: adopter.email,
    subject: 'Tu solicitud de adopción fue aprobada',
    html: buildAdoptionApprovalEmail(adopter, animal),
  }).then((result) => {
    if (result.error) {
      console.error('[approveAdoptionRequest] Email failed:', {
        requestId,
        error: result.error,
      });
    }
  });

  revalidatePath('/admin/adoptions');
  return { success: true };
}
```

For **critical** emails (e.g. donation receipt), await and surface:

```typescript
const emailResult = await sendEmail({
  to: donor.email,
  subject: 'Recibo de tu donación',
  html: buildDonationReceiptEmail(donor, donation),
});

if (emailResult.error) {
  // Log but do not roll back the donation — email is not transactional
  console.error('[processDonation] Receipt email failed:', emailResult.error);
  return { success: true, emailWarning: 'No se pudo enviar el recibo por email' };
}
```

### 6. Integration test note

The `send-email.ts` wrapper is intentionally thin — all business logic (template
building, recipient selection) lives in the caller. Unit tests mock the Resend SDK.
A real integration test against Resend would require a test API key and is not
included here; use Resend's dashboard to verify email delivery in staging.

---

## Files to Create / Modify

| Path | Action | Notes |
|------|--------|-------|
| `package.json` | Modify | Add `resend` dependency |
| `.env.example` | Modify | Add `RESEND_API_KEY`, `FROM_EMAIL` |
| `src/lib/email/send-email.ts` | Create | Wrapper with `sendEmail()` + `FROM_EMAIL` |
| `src/lib/email/__tests__/send-email.test.ts` | Create | 6 vitest unit tests |

---

## Definition of Done

- [ ] `npm install resend` added to dependencies
- [ ] `.env.example` documents both email env vars
- [ ] `sendEmail()` wrapper created, never throws, returns `{ messageId? } | { error? }`
- [ ] `FROM_EMAIL` exported constant used everywhere — no hardcoded from-addresses
- [ ] All 6 unit tests pass with `npm run test`
- [ ] Fire-and-forget pattern documented in comments for Server Action callers
