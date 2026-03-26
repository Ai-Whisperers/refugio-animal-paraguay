---
task: T02
story: S03
epic: EPIC-2
title: Configure transactional email notifications via Resend
status: ready
priority: medium
agent_type: fullstack
created: 2026-03-25T17:13:26.728264
---

# T02: Configure transactional email notifications via Resend

## Description

Implement a Supabase Edge Function `send-adoption-email` that sends transactional emails via **Resend** when an adoption application status changes. The function is triggered by the same Supabase Database Webhook as S03/T01. Each status transition maps to a distinct email template rendered as HTML. The function shares the webhook payload structure with T01 but handles email delivery independently.

## Context

- **Resend** — NOT SendGrid, NOT Mailgun, NOT nodemailer. Resend has a native `fetch`-compatible REST API suitable for Deno Edge Functions
- Edge Function runs in Deno — use `fetch()` directly, no npm packages
- Environment secret: `RESEND_API_KEY` stored in Supabase Edge Function secrets
- Sender address: `adopciones@refugioanimalpy.org` (must be verified in Resend)
- Recipient: `adoption_applications.data->>'adopter'->>'email'`
- Status transitions that trigger emails: `submitted`, `under_review`, `approved`, `rejected`
- `withdrawn` and `draft` do not trigger emails

## Files to create

```
supabase/functions/send-adoption-email/index.ts   # Edge Function
supabase/functions/send-adoption-email/templates.ts  # HTML email templates
supabase/functions/send-adoption-email/types.ts   # Shared types (same as T01)
```

---

## Files to create

### `supabase/functions/send-adoption-email/types.ts`

```typescript
export interface WebhookPayload {
  type: 'UPDATE' | 'INSERT'
  table: string
  schema: string
  record: ApplicationRecord
  old_record: ApplicationRecord | null
}

export interface ApplicationRecord {
  id: string
  status: string
  adopter_id: string
  submitted_at: string | null
  data: {
    adopter?: {
      fullName?: string
      email?: string
    }
  }
}

export interface EmailPayload {
  from: string
  to: string
  subject: string
  html: string
}
```

---

### `supabase/functions/send-adoption-email/templates.ts`

```typescript
export interface TemplateContext {
  recipientName: string
  applicationId: string
}

export function renderUnderReviewEmail(ctx: TemplateContext): { subject: string; html: string } {
  return {
    subject: 'Refugio Animal PY — Su solicitud está en revisión',
    html: `
      <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto; padding: 24px;">
        <h2 style="color: #1a1a1a;">Su solicitud está siendo revisada</h2>
        <p>Hola <strong>${ctx.recipientName}</strong>,</p>
        <p>
          Hemos recibido su solicitud de adopción y nuestro equipo ya está trabajando en revisarla.
          Le notificaremos el resultado a la brevedad.
        </p>
        <p style="color: #666; font-size: 13px;">ID de solicitud: ${ctx.applicationId}</p>
        <hr style="border: none; border-top: 1px solid #eee; margin: 24px 0;" />
        <p style="color: #666; font-size: 12px;">Refugio Animal Paraguay</p>
      </div>
    `,
  }
}

export function renderApprovedEmail(ctx: TemplateContext): { subject: string; html: string } {
  return {
    subject: '¡Su solicitud de adopción fue aprobada! — Refugio Animal PY',
    html: `
      <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto; padding: 24px;">
        <h2 style="color: #16a34a;">¡Solicitud aprobada!</h2>
        <p>Hola <strong>${ctx.recipientName}</strong>,</p>
        <p>
          Nos alegra informarle que su solicitud de adopción ha sido <strong>aprobada</strong>.
          Un miembro de nuestro equipo se comunicará con usted para coordinar los próximos pasos.
        </p>
        <p style="color: #666; font-size: 13px;">ID de solicitud: ${ctx.applicationId}</p>
        <hr style="border: none; border-top: 1px solid #eee; margin: 24px 0;" />
        <p style="color: #666; font-size: 12px;">Refugio Animal Paraguay</p>
      </div>
    `,
  }
}

export function renderRejectedEmail(ctx: TemplateContext): { subject: string; html: string } {
  return {
    subject: 'Actualización sobre su solicitud — Refugio Animal PY',
    html: `
      <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto; padding: 24px;">
        <h2 style="color: #1a1a1a;">Actualización sobre su solicitud</h2>
        <p>Hola <strong>${ctx.recipientName}</strong>,</p>
        <p>
          Lamentablemente, su solicitud de adopción no pudo ser aprobada en esta oportunidad.
          Si tiene preguntas, puede contactarnos directamente y estaremos felices de orientarle.
        </p>
        <p style="color: #666; font-size: 13px;">ID de solicitud: ${ctx.applicationId}</p>
        <hr style="border: none; border-top: 1px solid #eee; margin: 24px 0;" />
        <p style="color: #666; font-size: 12px;">Refugio Animal Paraguay</p>
      </div>
    `,
  }
}

export function renderSubmittedEmail(ctx: TemplateContext): { subject: string; html: string } {
  return {
    subject: 'Recibimos su solicitud de adopción — Refugio Animal PY',
    html: `
      <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto; padding: 24px;">
        <h2 style="color: #1a1a1a;">Solicitud recibida</h2>
        <p>Hola <strong>${ctx.recipientName}</strong>,</p>
        <p>
          Hemos recibido su solicitud de adopción correctamente. La revisaremos y le responderemos
          a la brevedad posible.
        </p>
        <p style="color: #666; font-size: 13px;">ID de solicitud: ${ctx.applicationId}</p>
        <hr style="border: none; border-top: 1px solid #eee; margin: 24px 0;" />
        <p style="color: #666; font-size: 12px;">Refugio Animal Paraguay</p>
      </div>
    `,
  }
}
```

---

### `supabase/functions/send-adoption-email/index.ts`

```typescript
import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import type { WebhookPayload, EmailPayload } from './types.ts'
import {
  renderSubmittedEmail,
  renderUnderReviewEmail,
  renderApprovedEmail,
  renderRejectedEmail,
} from './templates.ts'

const RESEND_API_KEY = Deno.env.get('RESEND_API_KEY')!
const FROM_ADDRESS = 'adopciones@refugioanimalpy.org'
const RESEND_URL = 'https://api.resend.com/emails'

type RenderFn = (ctx: { recipientName: string; applicationId: string }) => {
  subject: string
  html: string
}

const STATUS_RENDERERS: Record<string, RenderFn | null> = {
  submitted: renderSubmittedEmail,
  under_review: renderUnderReviewEmail,
  approved: renderApprovedEmail,
  rejected: renderRejectedEmail,
  withdrawn: null,
  draft: null,
}

async function sendEmail(payload: EmailPayload): Promise<void> {
  const response = await fetch(RESEND_URL, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${RESEND_API_KEY}`,
    },
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    const body = await response.text()
    console.error('Resend API error', { status: response.status, body })
    throw new Error(`Resend API returned ${response.status}`)
  }
}

serve(async (req) => {
  try {
    const webhookPayload: WebhookPayload = await req.json()

    const newStatus = webhookPayload.record.status
    const oldStatus = webhookPayload.old_record?.status ?? null

    // Skip if status hasn't changed (UPDATE with same status)
    if (newStatus === oldStatus) {
      return new Response('No status change', { status: 200 })
    }

    const renderer = STATUS_RENDERERS[newStatus]
    if (!renderer) {
      return new Response('No email template for this status', { status: 200 })
    }

    const adopter = webhookPayload.record.data?.adopter
    if (!adopter?.email) {
      console.warn('No email on application', { id: webhookPayload.record.id })
      return new Response('No email address', { status: 200 })
    }

    const recipientName = adopter.fullName ?? 'Solicitante'
    const { subject, html } = renderer({
      recipientName,
      applicationId: webhookPayload.record.id,
    })

    await sendEmail({
      from: FROM_ADDRESS,
      to: adopter.email,
      subject,
      html,
    })

    return new Response('Email sent', { status: 200 })
  } catch (err) {
    console.error('send-adoption-email failed', err)
    // Return 200 to prevent webhook retry loops
    return new Response('Error logged', { status: 200 })
  }
})
```

---

## Required Supabase secrets

Set in Supabase dashboard under **Project Settings → Edge Functions → Secrets**:

```
RESEND_API_KEY  — API key from resend.com dashboard
```

## Required Resend setup (manual prerequisites)

1. Create account at resend.com
2. Verify domain `refugioanimalpy.org` (add DNS TXT records)
3. Create API key with "Sending access" scope
4. Confirm sender `adopciones@refugioanimalpy.org` is on the verified domain

---

## Acceptance Criteria

- [ ] Edge Function deploys: `supabase functions deploy send-adoption-email`
- [ ] Sends email for `submitted`, `under_review`, `approved`, `rejected` status transitions
- [ ] `withdrawn` and `draft` produce no email (200 response, no Resend call)
- [ ] No email sent when `newStatus === oldStatus`
- [ ] Missing email address: logs warning, returns 200 — does NOT throw
- [ ] Resend API error: logs error, returns 200 — does NOT trigger webhook retry
- [ ] `RESEND_API_KEY` read from Deno env, not hardcoded
- [ ] Each status has a distinct subject line and HTML body
- [ ] HTML emails include the application ID for traceability
- [ ] TypeScript: no type errors

## Implementation Notes

- **Return 200 even on error** — same reasoning as T01. Notification failures should not cause Supabase to retry the webhook indefinitely.
- **Inline styles only** — email clients (especially Outlook) strip `<style>` tags. All styling must be inline `style=""` attributes.
- **No external images** — avoid CDN-hosted images in email bodies; many email clients block them by default.
- **`submitted` status** — triggered on INSERT (when the Server Action in S01/T03 inserts the row). The webhook must also listen for `INSERT` events, not just `UPDATE`, to catch the initial submission confirmation email.
- **Template function isolation** — each status renderer is a pure function in `templates.ts`. This makes them testable without Deno or Supabase dependencies.

## Related

- Depends on: S01/T03 (inserts the row and triggers `submitted` status), S02/T02 (triggers `under_review`/`approved`/`rejected` status changes)
- T01 (same story) handles WhatsApp for the same status changes
- Part of: S03 — Adoption Notifications
