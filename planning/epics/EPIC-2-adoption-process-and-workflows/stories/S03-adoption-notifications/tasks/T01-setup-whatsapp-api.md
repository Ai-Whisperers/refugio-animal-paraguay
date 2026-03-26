---
task: T01
story: S03
epic: EPIC-2
title: Integrate Meta Cloud API for WhatsApp adoption notifications
status: ready
priority: medium
agent_type: fullstack
created: 2026-03-25T17:13:26.728203
---

# T01: Integrate Meta Cloud API for WhatsApp adoption notifications

## Description

Implement a Supabase Edge Function `send-whatsapp-notification` that calls the **Meta Cloud API** (WhatsApp Business Platform) to send templated notifications when an adoption application status changes. The Edge Function is triggered by a Supabase Database Webhook on the `adoption_applications` table. Use HSM (Highly Structured Message) templates — the only messages allowed outside the 24-hour session window.

## Context

- **Meta Cloud API** — NOT Twilio, NOT 360dialog. Use `https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages`
- Edge Function runs in Deno — no Node.js APIs, use `fetch()` directly
- Environment secrets stored in Supabase project secrets (not `.env`): `WHATSAPP_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`
- Trigger: Supabase Database Webhook fires on `UPDATE` of `adoption_applications.status`
- Templates must be pre-approved in Meta Business Manager — we send template name + variables, not free-form text
- Adopter phone number comes from `adoption_applications.data->>'adopter'->>'phone'` (Paraguay format: `+595...`)
- Paraguayan numbers must be sent in E.164 format: `+595XXXXXXXXX`

## Files to create

```
supabase/functions/send-whatsapp-notification/index.ts  # Edge Function
supabase/functions/send-whatsapp-notification/types.ts  # Type definitions
```

## Supabase Database Webhook config (in Supabase dashboard)

```
Table: adoption_applications
Events: UPDATE
HTTP endpoint: https://<project>.supabase.co/functions/v1/send-whatsapp-notification
HTTP method: POST
Headers: Authorization: Bearer <SUPABASE_SERVICE_ROLE_KEY>
```

---

## Files to create

### `supabase/functions/send-whatsapp-notification/types.ts`

```typescript
export interface WebhookPayload {
  type: 'UPDATE'
  table: string
  schema: string
  record: ApplicationRecord
  old_record: ApplicationRecord
}

export interface ApplicationRecord {
  id: string
  status: string
  adopter_id: string
  data: {
    adopter?: {
      fullName?: string
      phone?: string
    }
  }
}

export interface WhatsAppTextMessage {
  messaging_product: 'whatsapp'
  to: string
  type: 'template'
  template: {
    name: string
    language: { code: string }
    components: WhatsAppTemplateComponent[]
  }
}

export interface WhatsAppTemplateComponent {
  type: 'body'
  parameters: Array<{ type: 'text'; text: string }>
}
```

---

### `supabase/functions/send-whatsapp-notification/index.ts`

```typescript
import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import type { WebhookPayload, WhatsAppTextMessage } from './types.ts'

const WHATSAPP_TOKEN = Deno.env.get('WHATSAPP_TOKEN')!
const PHONE_NUMBER_ID = Deno.env.get('WHATSAPP_PHONE_NUMBER_ID')!
const META_API_URL = `https://graph.facebook.com/v19.0/${PHONE_NUMBER_ID}/messages`

// Template names pre-approved in Meta Business Manager
const STATUS_TEMPLATES: Record<string, string | null> = {
  under_review: 'adopcion_en_revision',   // "Hola {{1}}, su solicitud está en revisión."
  approved: 'adopcion_aprobada',          // "¡Felicidades {{1}}! Su solicitud fue aprobada."
  rejected: 'adopcion_rechazada',         // "Hola {{1}}, su solicitud no fue aprobada en esta oportunidad."
  submitted: null,   // No WhatsApp notification on submit — email only
  withdrawn: null,
  draft: null,
}

function toE164Paraguay(phone: string): string | null {
  // Strip all non-digit characters
  const digits = phone.replace(/\D/g, '')

  // Already in international format without +
  if (digits.startsWith('595') && digits.length >= 11) {
    return `+${digits}`
  }
  // Local format starting with 09...
  if (digits.startsWith('09') && digits.length >= 10) {
    return `+595${digits.slice(1)}`
  }
  // Local format starting with 9... (without leading 0)
  if (digits.startsWith('9') && digits.length >= 9) {
    return `+595${digits}`
  }
  return null
}

async function sendWhatsAppTemplate(
  to: string,
  templateName: string,
  recipientName: string,
): Promise<void> {
  const message: WhatsAppTextMessage = {
    messaging_product: 'whatsapp',
    to,
    type: 'template',
    template: {
      name: templateName,
      language: { code: 'es' },
      components: [
        {
          type: 'body',
          parameters: [{ type: 'text', text: recipientName }],
        },
      ],
    },
  }

  const response = await fetch(META_API_URL, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${WHATSAPP_TOKEN}`,
    },
    body: JSON.stringify(message),
  })

  if (!response.ok) {
    const body = await response.text()
    console.error('WhatsApp API error', { status: response.status, body })
    throw new Error(`WhatsApp API returned ${response.status}`)
  }
}

serve(async (req) => {
  try {
    const payload: WebhookPayload = await req.json()

    // Only process status change updates
    const newStatus = payload.record.status
    const oldStatus = payload.old_record.status

    if (newStatus === oldStatus) {
      return new Response('No status change', { status: 200 })
    }

    const templateName = STATUS_TEMPLATES[newStatus]
    if (!templateName) {
      return new Response('No template for this status', { status: 200 })
    }

    const adopter = payload.record.data?.adopter
    if (!adopter?.phone) {
      console.warn('No phone number on application', { id: payload.record.id })
      return new Response('No phone number', { status: 200 })
    }

    const e164Phone = toE164Paraguay(adopter.phone)
    if (!e164Phone) {
      console.warn('Could not normalize phone to E.164', { phone: adopter.phone })
      return new Response('Invalid phone format', { status: 200 })
    }

    const recipientName = adopter.fullName ?? 'Solicitante'

    await sendWhatsAppTemplate(e164Phone, templateName, recipientName)

    return new Response('Notification sent', { status: 200 })
  } catch (err) {
    console.error('send-whatsapp-notification failed', err)
    // Return 200 to prevent webhook retry loops — failures are logged only
    return new Response('Error logged', { status: 200 })
  }
})
```

---

## Required Supabase secrets

Set these in the Supabase dashboard under **Project Settings → Edge Functions → Secrets**:

```
WHATSAPP_TOKEN          — Meta permanent access token from Business Manager
WHATSAPP_PHONE_NUMBER_ID — Phone Number ID from the WhatsApp Business app
```

---

## Meta template setup (manual prerequisite)

Before deploying, create and get approved in Meta Business Manager:

| Template name           | Language | Body text (Spanish) |
|------------------------|----------|---------------------|
| `adopcion_en_revision` | es       | Hola {{1}}, su solicitud de adopción está siendo revisada. Le informaremos pronto. |
| `adopcion_aprobada`    | es       | ¡Felicidades {{1}}! Su solicitud de adopción fue aprobada. El refugio se comunicará con usted. |
| `adopcion_rechazada`   | es       | Hola {{1}}, lamentablemente su solicitud no fue aprobada en esta oportunidad. Puede contactarnos para más información. |

Templates take 1-3 business days for Meta approval. Development can proceed with test phone numbers.

---

## Acceptance Criteria

- [ ] Edge Function deploys: `supabase functions deploy send-whatsapp-notification`
- [ ] Function only fires on status change — skips if `newStatus === oldStatus`
- [ ] Sends correct template for `under_review`, `approved`, `rejected` statuses
- [ ] `submitted`, `withdrawn`, `draft` statuses produce no WhatsApp message (200 response, no API call)
- [ ] Phone normalized to E.164 format (`+595XXXXXXXXX`) before API call
- [ ] Missing or invalid phone: logs warning, returns 200 — does NOT throw
- [ ] Meta API error: logs error, returns 200 — does NOT trigger webhook retry
- [ ] `WHATSAPP_TOKEN` and `WHATSAPP_PHONE_NUMBER_ID` read from Deno env, not hardcoded
- [ ] TypeScript: no type errors

## Implementation Notes

- **Return 200 even on error** — Supabase Database Webhooks retry on non-2xx responses. Notification failures are not worth retrying — they would spam the user on transient Meta API errors. Log errors, return 200.
- **Template-only messages** — The 24-hour session window restriction means free-form messages can only be sent within 24h of a user-initiated conversation. For status notifications (which staff trigger, not users), only pre-approved HSM templates are safe.
- **`toE164Paraguay`** normalizes the Paraguayan phone from the form (which accepts `09XXXXXXXX` or `+595XXXXXXXXX` patterns) into the E.164 format Meta requires.
- **Deno imports** — Edge Functions use Deno. Import from `https://deno.land/std@0.168.0/...` — not from `node_modules`.

## Related

- Depends on: S02/T02 (status changes trigger the webhook), S01/T01 (`adoption_applications.data` JSONB with `adopter.phone`)
- T02 (same story) handles email notifications for the same status changes
- Part of: S03 — Adoption Notifications
