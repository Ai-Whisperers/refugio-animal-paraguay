---
task: T01
story: S02
epic: EPIC-6
title: Setup Twilio
status: ready
priority: medium
created: 2026-03-25T17:13:26.732914
---

# T01: Setup Twilio WhatsApp Integration

## Description

Integrate Twilio's WhatsApp Business API for sending transactional messages to adopters,
donors, and volunteers. Build a thin `sendWhatsApp()` wrapper parallel to the `sendEmail()`
wrapper from S01/T01. WhatsApp messages are queued via the `notification_queue` table
(S01/T03) and processed by the same Route Handler.

**Why Twilio**: Twilio's WhatsApp sandbox is available for development without Meta Business
verification. Production requires an approved WhatsApp Business Account (WBA), which Twilio
facilitates. In Paraguay, WhatsApp is the dominant messaging channel — critical for
volunteer and adopter communication.

**No separate queue**: The `notification_queue` table from S01/T03 handles both email and
WhatsApp rows (`channel` column). The processor Route Handler dispatches to `sendEmail()`
or `sendWhatsApp()` based on the channel.

---

## Acceptance Criteria

- [ ] `twilio` npm package installed
- [ ] `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_WHATSAPP_FROM` documented in `.env.example`
- [ ] `src/lib/whatsapp/send-whatsapp.ts` wrapper created
- [ ] Wrapper returns structured `{ messageId? } | { error? }` — never throws
- [ ] `TWILIO_WHATSAPP_FROM` constant exported for use in templates
- [ ] Processor Route Handler (`S01/T03`) updated to dispatch WhatsApp rows
- [ ] 6 vitest unit tests for the wrapper's happy path and error paths

---

## Implementation Notes

### 1. Install dependency

```bash
npm install twilio
```

### 2. Environment variables

`.env.example`:
```
# WhatsApp — Twilio
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
# Twilio WhatsApp sender (sandbox: whatsapp:+14155238886, production: your approved number)
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
```

**Sandbox setup** (development only):
1. Go to Twilio Console → Messaging → Try it out → Send a WhatsApp message
2. Join the sandbox by sending the join code from your WhatsApp to `+1 415 523 8886`
3. Use `whatsapp:+14155238886` as the from number during development

**Production setup**:
1. Apply for WhatsApp Business Account via Twilio
2. Get approved number: `whatsapp:+595XXX` (Paraguayan number preferred)
3. Update `TWILIO_WHATSAPP_FROM` in production environment

### 3. WhatsApp wrapper — `src/lib/whatsapp/send-whatsapp.ts`

```typescript
import twilio from 'twilio';

// Lazy-initialized Twilio client
let _client: twilio.Twilio | null = null;

function getTwilioClient(): twilio.Twilio {
  if (!_client) {
    const accountSid = process.env.TWILIO_ACCOUNT_SID;
    const authToken = process.env.TWILIO_AUTH_TOKEN;

    if (!accountSid || !authToken) {
      throw new Error(
        'TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN environment variables are required'
      );
    }

    _client = twilio(accountSid, authToken);
  }
  return _client;
}

export const WHATSAPP_FROM =
  process.env.TWILIO_WHATSAPP_FROM ?? 'whatsapp:+14155238886';

export interface WhatsAppPayload {
  /** Recipient phone number in E.164 format, prefixed with 'whatsapp:' */
  to: string;
  /** Message body — plain text, max ~1600 chars for WhatsApp */
  body: string;
}

export interface SendWhatsAppResult {
  messageId?: string;
  error?: string;
}

/**
 * Send a WhatsApp message via Twilio.
 *
 * The `to` number must be formatted as 'whatsapp:+595981234567'.
 * Returns { messageId } (Twilio SID) on success or { error } on failure.
 * Never throws — callers decide whether the error is fatal.
 */
export async function sendWhatsApp(
  payload: WhatsAppPayload
): Promise<SendWhatsAppResult> {
  try {
    const client = getTwilioClient();
    const message = await client.messages.create({
      from: WHATSAPP_FROM,
      to: payload.to,
      body: payload.body,
    });

    return { messageId: message.sid };
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    return { error: message };
  }
}

/**
 * Format a local Paraguayan phone number to WhatsApp E.164 format.
 *
 * Input:  '0981 234 567' or '0981234567'
 * Output: 'whatsapp:+595981234567'
 *
 * Returns null if the number cannot be normalized.
 */
export function formatParaguayanWhatsApp(localPhone: string): string | null {
  // Strip all non-digit characters
  const digits = localPhone.replace(/\D/g, '');

  // Paraguayan mobile: starts with 09XX (10 digits total)
  if (digits.startsWith('0') && digits.length === 10) {
    // Remove leading 0, add country code +595
    return `whatsapp:+595${digits.slice(1)}`;
  }

  // Already has country code: 595XXXXXXXXX (12 digits)
  if (digits.startsWith('595') && digits.length === 12) {
    return `whatsapp:+${digits}`;
  }

  return null;
}
```

### 4. Update processor to handle WhatsApp rows

In `src/app/api/notifications/process/route.ts` (created in S01/T03), replace the
placeholder WhatsApp handler:

```typescript
// Replace:
// if (row.channel !== 'email') {
//   await markFailed(row.id, 'WhatsApp channel not yet implemented', row.retry_count);
//   return;
// }

// With:
import { sendWhatsApp } from '@/lib/whatsapp/send-whatsapp';

async function processRow(row: NotificationRow): Promise<void> {
  let result: { messageId?: string; error?: string };

  if (row.channel === 'email') {
    result = await sendEmail({
      to: row.recipient,
      subject: row.subject ?? '(sin asunto)',
      html: row.body_html ?? '',
      text: row.body_text ?? undefined,
    });
  } else if (row.channel === 'whatsapp') {
    result = await sendWhatsApp({
      to: row.recipient,  // must be 'whatsapp:+595...'
      body: row.body_text ?? row.body_html ?? '',
    });
  } else {
    await markFailed(row.id, `Unknown channel: ${row.channel}`, row.retry_count);
    return;
  }

  if (result.error) {
    const newRetryCount = row.retry_count + 1;
    if (newRetryCount >= MAX_RETRIES) {
      await markFailed(row.id, result.error, newRetryCount);
    } else {
      await supabaseAdmin
        .from('notification_queue')
        .update({ status: 'pending', retry_count: newRetryCount, last_error: result.error })
        .eq('id', row.id);
    }
    return;
  }

  await supabaseAdmin
    .from('notification_queue')
    .update({ status: 'sent', processed_at: new Date().toISOString(), last_error: null })
    .eq('id', row.id);
}
```

### 5. `enqueueWhatsAppNotification` helper — add to `src/lib/notifications/queue.ts`

```typescript
export interface EnqueueWhatsAppOptions {
  /** Phone in 'whatsapp:+595...' format */
  recipient: string;
  body: string;
  entityType?: string;
  entityId?: string;
}

/**
 * Add a WhatsApp notification to the queue.
 * `recipient` must be formatted as 'whatsapp:+595981234567'.
 */
export async function enqueueWhatsAppNotification(
  options: EnqueueWhatsAppOptions
): Promise<EnqueueResult> {
  const { data, error } = await supabaseAdmin
    .from('notification_queue')
    .insert({
      channel: 'whatsapp',
      status: 'pending',
      recipient: options.recipient,
      body_text: options.body,
      entity_type: options.entityType ?? null,
      entity_id: options.entityId ?? null,
    })
    .select('id')
    .single();

  if (error) {
    return { error: error.message };
  }

  return { queueId: data.id };
}
```

### 6. Unit tests — `src/lib/whatsapp/__tests__/send-whatsapp.test.ts`

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest';

// Mock the twilio module
const mockMessagesCreate = vi.fn();
vi.mock('twilio', () => ({
  default: vi.fn().mockReturnValue({
    messages: { create: mockMessagesCreate },
  }),
}));

import { sendWhatsApp, formatParaguayanWhatsApp } from '../send-whatsapp';

const VALID_PAYLOAD = {
  to: 'whatsapp:+595981234567',
  body: 'Tu turno fue confirmado para mañana a las 8am.',
};

describe('sendWhatsApp', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    process.env.TWILIO_ACCOUNT_SID = 'ACtest';
    process.env.TWILIO_AUTH_TOKEN = 'test-token';
  });

  it('returns messageId (SID) on successful send', async () => {
    mockMessagesCreate.mockResolvedValueOnce({ sid: 'SMabc123def456' });

    const result = await sendWhatsApp(VALID_PAYLOAD);

    expect(result.messageId).toBe('SMabc123def456');
    expect(result.error).toBeUndefined();
  });

  it('returns error string when Twilio throws', async () => {
    mockMessagesCreate.mockRejectedValueOnce(
      new Error('The number +595... is not a valid WhatsApp number')
    );

    const result = await sendWhatsApp(VALID_PAYLOAD);

    expect(result.error).toContain('not a valid WhatsApp number');
    expect(result.messageId).toBeUndefined();
  });

  it('never throws — returns error object instead', async () => {
    mockMessagesCreate.mockRejectedValueOnce(new Error('Network error'));

    await expect(sendWhatsApp(VALID_PAYLOAD)).resolves.not.toThrow();
  });
});

describe('formatParaguayanWhatsApp', () => {
  it('formats a local mobile number to WhatsApp E.164', () => {
    expect(formatParaguayanWhatsApp('0981234567')).toBe('whatsapp:+595981234567');
  });

  it('strips spaces and formats correctly', () => {
    expect(formatParaguayanWhatsApp('0981 234 567')).toBe('whatsapp:+595981234567');
  });

  it('returns null for an unrecognizable number format', () => {
    expect(formatParaguayanWhatsApp('12345')).toBeNull();
  });
});
```

---

## Files to Create / Modify

| Path | Action | Notes |
|------|--------|-------|
| `package.json` | Modify | Add `twilio` dependency |
| `.env.example` | Modify | Add three Twilio env vars |
| `src/lib/whatsapp/send-whatsapp.ts` | Create | Wrapper + `formatParaguayanWhatsApp()` |
| `src/lib/whatsapp/__tests__/send-whatsapp.test.ts` | Create | 6 unit tests |
| `src/lib/notifications/queue.ts` | Modify | Add `enqueueWhatsAppNotification()` |
| `src/app/api/notifications/process/route.ts` | Modify | Add WhatsApp dispatch branch |

---

## Definition of Done

- [ ] `npm install twilio` added to dependencies
- [ ] `.env.example` documents all three Twilio vars with sandbox guidance
- [ ] `sendWhatsApp()` created, never throws, returns structured result
- [ ] `formatParaguayanWhatsApp()` normalizes local PY numbers to `whatsapp:+595...` format
- [ ] `enqueueWhatsAppNotification()` added to queue module
- [ ] Processor Route Handler dispatches WhatsApp rows correctly
- [ ] All 6 unit tests pass
