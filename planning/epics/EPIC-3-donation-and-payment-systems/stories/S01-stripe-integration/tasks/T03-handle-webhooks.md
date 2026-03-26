---
task: T03
story: S01
epic: EPIC-3
title: Handle Stripe webhooks
status: ready
priority: medium
created: 2026-03-25T17:13:26.728981
---

# T03: Handle Stripe Webhooks

## Description

Implement a Supabase Edge Function that receives Stripe webhook events, verifies the signature, and updates `donations.status` in Supabase. This closes the payment lifecycle loop opened in T02 — when Stripe confirms payment success or failure, the donation record is updated accordingly.

## Acceptance Criteria

- [ ] Edge Function deployed at `supabase/functions/stripe-webhook/`
- [ ] Stripe signature verified on every request — unverified requests rejected with 401
- [ ] `payment_intent.succeeded` → sets `donations.status = 'succeeded'`
- [ ] `payment_intent.payment_failed` → sets `donations.status = 'failed'`
- [ ] Always returns HTTP 200 (prevents Stripe retry loops on non-payment errors)
- [ ] Service role key used for DB writes (bypasses RLS)
- [ ] Webhook secret stored in Supabase secrets, not hardcoded
- [ ] Unit tests covering signature verification, event routing, DB update

## Implementation Notes

### Architecture

```
Stripe Event (payment_intent.succeeded)
  → POST https://[project].supabase.co/functions/v1/stripe-webhook
  → Supabase Edge Function (Deno)
      → Verify signature (stripe.webhooks.constructEvent)
      → Route event type
      → Update donations table via service role key
      → Return 200
```

### File Structure

```
supabase/
└── functions/
    └── stripe-webhook/
        └── index.ts
```

### Supabase Secrets (set via CLI before deploying)

```bash
supabase secrets set STRIPE_SECRET_KEY=sk_live_...
supabase secrets set STRIPE_WEBHOOK_SECRET=whsec_...
# SUPABASE_SERVICE_ROLE_KEY is auto-injected by Supabase runtime
```

### Edge Function Implementation

```typescript
// supabase/functions/stripe-webhook/index.ts
import Stripe from 'https://esm.sh/stripe@14.21.0?target=deno'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const STRIPE_WEBHOOK_SECRET = Deno.env.get('STRIPE_WEBHOOK_SECRET')!
const STRIPE_SECRET_KEY = Deno.env.get('STRIPE_SECRET_KEY')!
const SUPABASE_URL = Deno.env.get('SUPABASE_URL')!
const SUPABASE_SERVICE_ROLE_KEY = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!

const stripe = new Stripe(STRIPE_SECRET_KEY, {
  apiVersion: '2024-06-20',
  httpClient: Stripe.createFetchHttpClient(),
})

// Service role client — bypasses RLS for internal updates
const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

Deno.serve(async (req: Request): Promise<Response> => {
  // Only accept POST requests
  if (req.method !== 'POST') {
    return new Response('Method not allowed', { status: 405 })
  }

  const body = await req.text()
  const sig = req.headers.get('stripe-signature')

  if (!sig) {
    return new Response('Missing stripe-signature header', { status: 400 })
  }

  let event: Stripe.Event

  try {
    event = await stripe.webhooks.constructEventAsync(body, sig, STRIPE_WEBHOOK_SECRET)
  } catch (err) {
    // Signature verification failed — reject the request
    console.error('Webhook signature verification failed:', err)
    return new Response('Invalid signature', { status: 401 })
  }

  // Route event to handler — return 200 even if handler fails
  // to prevent Stripe from retrying non-payment errors
  try {
    await handleStripeEvent(event)
  } catch (err) {
    console.error(`Failed to handle event ${event.type}:`, err)
    // Still return 200 — Stripe will retry if we return non-2xx
  }

  return new Response(JSON.stringify({ received: true }), {
    status: 200,
    headers: { 'Content-Type': 'application/json' },
  })
})

async function handleStripeEvent(event: Stripe.Event): Promise<void> {
  switch (event.type) {
    case 'payment_intent.succeeded':
      await handlePaymentIntentSucceeded(event.data.object as Stripe.PaymentIntent)
      break

    case 'payment_intent.payment_failed':
      await handlePaymentIntentFailed(event.data.object as Stripe.PaymentIntent)
      break

    default:
      // Unhandled event types — log and ignore (return 200 above)
      console.log(`Unhandled event type: ${event.type}`)
  }
}

async function handlePaymentIntentSucceeded(
  paymentIntent: Stripe.PaymentIntent,
): Promise<void> {
  const { error } = await supabase
    .from('donations')
    .update({
      status: 'succeeded',
      stripe_charge_id: paymentIntent.latest_charge as string | null,
      updated_at: new Date().toISOString(),
    })
    .eq('stripe_payment_intent_id', paymentIntent.id)

  if (error) {
    // Log and re-throw — caller handles the 200 response regardless
    console.error('Failed to update donation to succeeded:', {
      payment_intent_id: paymentIntent.id,
      error: error.message,
    })
    throw error
  }

  console.log(`Donation succeeded for intent ${paymentIntent.id}`)
}

async function handlePaymentIntentFailed(
  paymentIntent: Stripe.PaymentIntent,
): Promise<void> {
  const failureCode = paymentIntent.last_payment_error?.code ?? 'unknown'
  const failureMessage = paymentIntent.last_payment_error?.message ?? null

  const { error } = await supabase
    .from('donations')
    .update({
      status: 'failed',
      failure_code: failureCode,
      failure_message: failureMessage,
      updated_at: new Date().toISOString(),
    })
    .eq('stripe_payment_intent_id', paymentIntent.id)

  if (error) {
    console.error('Failed to update donation to failed:', {
      payment_intent_id: paymentIntent.id,
      error: error.message,
    })
    throw error
  }

  console.log(`Donation failed for intent ${paymentIntent.id}, code: ${failureCode}`)
}
```

### Database Schema Requirements

The `donations` table must have these columns (add via migration if missing):

```sql
-- Migration: add webhook fields to donations
ALTER TABLE donations
  ADD COLUMN IF NOT EXISTS stripe_charge_id TEXT,
  ADD COLUMN IF NOT EXISTS failure_code TEXT,
  ADD COLUMN IF NOT EXISTS failure_message TEXT;

-- Index for webhook lookups by payment intent ID
CREATE INDEX IF NOT EXISTS idx_donations_stripe_payment_intent_id
  ON donations (stripe_payment_intent_id);
```

### Stripe Dashboard Configuration

1. Go to Stripe Dashboard → Developers → Webhooks
2. Add endpoint: `https://[project-ref].supabase.co/functions/v1/stripe-webhook`
3. Select events to listen for:
   - `payment_intent.succeeded`
   - `payment_intent.payment_failed`
4. Copy the signing secret → `STRIPE_WEBHOOK_SECRET`

### Deploy Command

```bash
supabase functions deploy stripe-webhook --no-verify-jwt
```

`--no-verify-jwt` is required — Stripe cannot provide a Supabase JWT. Authentication is handled by the `stripe-signature` header verification instead.

### Testing with Stripe CLI (local)

```bash
# Forward Stripe events to local Supabase
stripe listen --forward-to localhost:54321/functions/v1/stripe-webhook

# Trigger a test event
stripe trigger payment_intent.succeeded
stripe trigger payment_intent.payment_failed
```

### Unit Test Pattern

```typescript
// supabase/functions/stripe-webhook/index.test.ts
import { assertEquals } from 'https://deno.land/std@0.168.0/testing/asserts.ts'

Deno.test('rejects requests without stripe-signature header', async () => {
  const req = new Request('http://localhost/stripe-webhook', {
    method: 'POST',
    body: '{}',
  })
  const res = await handleRequest(req)
  assertEquals(res.status, 400)
})

Deno.test('rejects requests with invalid signature', async () => {
  const req = new Request('http://localhost/stripe-webhook', {
    method: 'POST',
    headers: { 'stripe-signature': 'invalid' },
    body: '{}',
  })
  const res = await handleRequest(req)
  assertEquals(res.status, 401)
})

Deno.test('returns 200 even when DB update fails', async () => {
  // Mock a valid event but broken DB connection
  // Verifies we never return non-2xx to Stripe
  // ...
})
```

## Related Issues

- EPIC-3
- S01
- T02 (creates donation records that this webhook updates)
