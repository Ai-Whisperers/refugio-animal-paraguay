---
task: T02
story: S03
epic: EPIC-3
title: Implement Tigo Money Donation Flow UI
status: ready
priority: medium
created: 2026-03-25T17:13:26.729494
---

# T02: Implement Tigo Money Donation Flow UI

## Description

Build the donor-facing UI for Tigo Money donations. The donor enters their Paraguayan mobile number and selects an amount in PYG. A Server Action normalizes the phone number to E.164, calls `TigoMoneyService.initiatePayment()`, and inserts a `tigo_money_donations` record. The donor is redirected to a pending page instructing them to approve the charge on their phone. A Supabase Edge Function handles the Tigo Money callback webhook to update donation status when the donor approves or rejects.

**PYG context**: Guaraní has no decimal places. All amounts are whole numbers (₲50,000 = 50000, never 50000.00). Preset amounts reflect realistic micro-donation ranges for Paraguay.

## Acceptance Criteria

- [ ] `TigoMoneyForm` client component at `src/components/donations/TigoMoneyForm.tsx`
- [ ] PYG preset amounts: ₲50,000 / ₲100,000 / ₲250,000 / ₲500,000
- [ ] Paraguay phone input with `0981-XXX-XXX` placeholder and live format hint
- [ ] Server Action `createTigoMoneyDonation()` in `src/app/(donations)/donate/actions.ts`
- [ ] Phone normalized via `normalizeParaguayPhone()` before API call — rejects non-Paraguay numbers
- [ ] `tigo_money_donations` row inserted with status `pending` before redirect
- [ ] Pending status page at `/donate/tigo-money/[id]` shows approval instructions
- [ ] 15-minute countdown timer visible on pending page
- [ ] Supabase Edge Function `tigo-money-webhook` updates donation status on callback
- [ ] `useTransition` used for pending state (not `useState<boolean>`)
- [ ] All CSS uses `var(--*)` — no hardcoded colors

## Implementation Notes

### Server Action

```typescript
// Addition to src/app/(donations)/donate/actions.ts
'use server'

import { createClient } from '@/lib/supabase/server'
import { tigoMoneyService } from '@/lib/payments/tigo-money-service'
import { normalizeParaguayPhone } from '@/lib/payments/tigo-money-phone'
import { revalidatePath } from 'next/cache'
import { redirect } from 'next/navigation'

export interface CreateTigoMoneyDonationResult {
  success: boolean
  error?: string
}

export async function createTigoMoneyDonation(
  rawPhone: string,
  amountPyg: number,
  donorName: string,
  campaignId?: string,
): Promise<CreateTigoMoneyDonationResult> {
  // Normalize and validate phone
  const phoneResult = normalizeParaguayPhone(rawPhone)
  if (!phoneResult.valid) {
    return { success: false, error: phoneResult.reason }
  }

  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()

  // Generate internal transaction ID before calling Tigo
  const { createId } = await import('@paralleldrive/cuid2')
  const transactionId = createId()

  // Call Tigo Money API — initiates push charge to donor's phone
  const tigoResult = await tigoMoneyService.initiatePayment({
    transactionId,
    phoneE164: phoneResult.e164,
    amountPyg,
    description: `Donación Refugio Animal Paraguay — ${donorName}`,
  })

  if (!tigoResult.success) {
    return { success: false, error: tigoResult.error }
  }

  // Persist the pending donation record
  const { data: donation, error: insertError } = await supabase
    .from('tigo_money_donations')
    .insert({
      tigo_transaction_id: transactionId,
      amount: amountPyg,        // PYG whole number — no division
      currency: 'pyg',
      donor_phone_e164: phoneResult.e164,
      donor_name: donorName,
      donor_user_id: user?.id ?? null,
      campaign_id: campaignId ?? null,
      status: 'pending',
    })
    .select('id')
    .single()

  if (insertError || !donation) {
    console.error('Failed to insert tigo_money_donations record:', insertError)
    return { success: false, error: 'No se pudo registrar la donación. Intente nuevamente.' }
  }

  revalidatePath('/donate')
  redirect(`/donate/tigo-money/${donation.id}`)
}
```

### Form Component

```typescript
// src/components/donations/TigoMoneyForm.tsx
'use client'

import { useState, useTransition } from 'react'
import { createTigoMoneyDonation } from '@/app/(donations)/donate/actions'

interface TigoMoneyFormProps {
  preselectedAmount?: number
  campaignId?: string
}

const PRESET_AMOUNTS_PYG = [50_000, 100_000, 250_000, 500_000] as const

function formatPyg(amount: number): string {
  return `₲${amount.toLocaleString('es-PY')}`
}

export function TigoMoneyForm({ preselectedAmount, campaignId }: TigoMoneyFormProps) {
  const [isPending, startTransition] = useTransition()
  const [amount, setAmount] = useState<number | ''>(preselectedAmount ?? '')
  const [phone, setPhone] = useState('')
  const [donorName, setDonorName] = useState('')
  const [error, setError] = useState<string | null>(null)

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)

    if (!amount || amount < 1000) {
      setError('El monto mínimo es ₲1.000')
      return
    }

    if (!phone.trim()) {
      setError('Ingresa tu número de teléfono')
      return
    }

    startTransition(async () => {
      const result = await createTigoMoneyDonation(
        phone.trim(),
        amount,
        donorName.trim(),
        campaignId,
      )
      // On success, Server Action redirects — we only reach here on error
      if (!result.success) {
        setError(result.error ?? 'Error al procesar. Intente nuevamente.')
      }
    })
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-6">
      {/* Amount Presets */}
      <div className="flex flex-col gap-2">
        <label className="text-sm font-medium text-[var(--text-primary)]">
          Monto (PYG)
        </label>
        <div className="flex gap-2 flex-wrap">
          {PRESET_AMOUNTS_PYG.map((preset) => (
            <button
              key={preset}
              type="button"
              onClick={() => setAmount(preset)}
              className={[
                'px-4 py-2 rounded-lg border text-sm font-medium transition-colors',
                amount === preset
                  ? 'bg-[var(--color-primary)] text-white border-[var(--color-primary)]'
                  : 'bg-[var(--bg-card)] text-[var(--text-secondary)] border-[var(--border-color)] hover:border-[var(--color-primary)]',
              ].join(' ')}
            >
              {formatPyg(preset)}
            </button>
          ))}
        </div>
        <input
          type="number"
          min="1000"
          step="1"
          value={amount}
          onChange={(e) => setAmount(e.target.value === '' ? '' : parseInt(e.target.value, 10))}
          placeholder="Otro monto en ₲..."
          className="w-full px-4 py-3 rounded-lg border border-[var(--border-color)] bg-[var(--bg-input)] text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]"
          required
        />
      </div>

      {/* Donor Name */}
      <div>
        <label className="block text-sm font-medium text-[var(--text-primary)] mb-1">
          Nombre completo
        </label>
        <input
          type="text"
          value={donorName}
          onChange={(e) => setDonorName(e.target.value)}
          placeholder="Tu nombre"
          className="w-full px-4 py-3 rounded-lg border border-[var(--border-color)] bg-[var(--bg-input)] text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]"
          required
        />
      </div>

      {/* Phone Input */}
      <div>
        <label className="block text-sm font-medium text-[var(--text-primary)] mb-1">
          Número de Tigo Money
        </label>
        <input
          type="tel"
          value={phone}
          onChange={(e) => setPhone(e.target.value)}
          placeholder="0981-123-456"
          className="w-full px-4 py-3 rounded-lg border border-[var(--border-color)] bg-[var(--bg-input)] text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]"
          required
        />
        <p className="text-xs text-[var(--text-muted)] mt-1">
          Número de celular Tigo Paraguay (ej: 0981-XXX-XXX)
        </p>
      </div>

      {error && (
        <p className="text-sm text-[var(--color-error)] bg-[var(--bg-error-subtle)] px-4 py-3 rounded-lg">
          {error}
        </p>
      )}

      <button
        type="submit"
        disabled={isPending}
        className="w-full py-4 px-6 bg-[var(--color-primary)] hover:bg-[var(--color-primary-hover)] disabled:opacity-50 text-white font-semibold rounded-lg transition-colors"
      >
        {isPending ? 'Enviando cobro...' : 'Donar con Tigo Money'}
      </button>

      <p className="text-xs text-[var(--text-muted)] text-center">
        Recibirás una notificación en tu teléfono para aprobar el cobro.
        Tienes 15 minutos para confirmar.
      </p>
    </form>
  )
}
```

### Pending Status Page (Server Component)

```typescript
// src/app/(donations)/donate/tigo-money/[id]/page.tsx
import { createClient } from '@/lib/supabase/server'
import { notFound } from 'next/navigation'
import { TigoMoneyPendingClient } from '@/components/donations/TigoMoneyPendingClient'

interface Props {
  params: { id: string }
}

export default async function TigoMoneyPendingPage({ params }: Props) {
  const supabase = await createClient()

  const { data: donation } = await supabase
    .from('tigo_money_donations')
    .select('id, amount, currency, donor_name, donor_phone_e164, status, created_at')
    .eq('id', params.id)
    .single()

  if (!donation) {
    notFound()
  }

  // 15-minute approval window expires from created_at
  const expiresAt = new Date(donation.created_at).getTime() + 15 * 60 * 1000

  return (
    <div className="max-w-md mx-auto px-4 py-12">
      <TigoMoneyPendingClient
        donationId={donation.id}
        amountPyg={donation.amount}
        donorName={donation.donor_name}
        phoneDisplay={donation.donor_phone_e164}
        status={donation.status}
        expiresAt={expiresAt}
      />
    </div>
  )
}
```

### Pending Status Client Component (with countdown + polling)

```typescript
// src/components/donations/TigoMoneyPendingClient.tsx
'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import type { TigoPaymentStatus } from '@/lib/payments/tigo-money-service'

interface TigoMoneyPendingClientProps {
  donationId: string
  amountPyg: number
  donorName: string
  phoneDisplay: string
  status: TigoPaymentStatus
  expiresAt: number  // unix timestamp in ms
}

const STATUS_CONFIG: Record<TigoPaymentStatus, { icon: string; title: string; description: string; variant: 'pending' | 'success' | 'error' }> = {
  pending: {
    icon: '📱',
    title: 'Aprueba el pago en tu teléfono',
    description: 'Revisa las notificaciones de Tigo Money en tu celular y aprueba el cobro.',
    variant: 'pending',
  },
  approved: {
    icon: '✅',
    title: '¡Donación aprobada!',
    description: '¡Gracias por tu donación! El pago fue procesado con éxito.',
    variant: 'success',
  },
  rejected: {
    icon: '❌',
    title: 'Cobro rechazado',
    description: 'Rechazaste el cobro en Tigo Money. Puedes intentarlo nuevamente.',
    variant: 'error',
  },
  expired: {
    icon: '⏱️',
    title: 'Tiempo agotado',
    description: 'El tiempo para aprobar el cobro expiró. Puedes intentarlo nuevamente.',
    variant: 'error',
  },
  failed: {
    icon: '⚠️',
    title: 'Error técnico',
    description: 'Ocurrió un problema técnico. Por favor intenta nuevamente.',
    variant: 'error',
  },
}

function formatPyg(amount: number): string {
  return `₲${amount.toLocaleString('es-PY')}`
}

function formatCountdown(msRemaining: number): string {
  if (msRemaining <= 0) return '0:00'
  const minutes = Math.floor(msRemaining / 60_000)
  const seconds = Math.floor((msRemaining % 60_000) / 1000)
  return `${minutes}:${seconds.toString().padStart(2, '0')}`
}

export function TigoMoneyPendingClient({
  donationId,
  amountPyg,
  donorName,
  phoneDisplay,
  status: initialStatus,
  expiresAt,
}: TigoMoneyPendingClientProps) {
  const router = useRouter()
  const [status, setStatus] = useState<TigoPaymentStatus>(initialStatus)
  const [msRemaining, setMsRemaining] = useState(Math.max(0, expiresAt - Date.now()))

  // Countdown timer
  useEffect(() => {
    if (status !== 'pending') return

    const interval = setInterval(() => {
      const remaining = Math.max(0, expiresAt - Date.now())
      setMsRemaining(remaining)
      if (remaining === 0) {
        setStatus('expired')
        clearInterval(interval)
      }
    }, 1000)

    return () => clearInterval(interval)
  }, [status, expiresAt])

  // Poll for status updates while pending
  useEffect(() => {
    if (status !== 'pending') return

    const pollInterval = setInterval(async () => {
      try {
        const res = await fetch(`/api/tigo-money/status/${donationId}`)
        if (!res.ok) return
        const data = await res.json()
        if (data.status && data.status !== 'pending') {
          setStatus(data.status)
          clearInterval(pollInterval)
          if (data.status === 'approved') {
            // Refresh page to show thank-you state via Server Component
            router.refresh()
          }
        }
      } catch {
        // Network error during poll — continue polling
      }
    }, 3000)  // poll every 3 seconds

    return () => clearInterval(pollInterval)
  }, [status, donationId, router])

  const config = STATUS_CONFIG[status]

  return (
    <div className="bg-[var(--bg-card)] rounded-2xl p-8 shadow-sm border border-[var(--border-color)]">
      {/* Icon + Title */}
      <div className="text-center mb-6">
        <div className="text-5xl mb-3">{config.icon}</div>
        <h1 className="text-2xl font-bold text-[var(--text-primary)]">
          {config.title}
        </h1>
        <p className="text-[var(--text-secondary)] mt-2">
          {config.description}
        </p>
      </div>

      {/* Donation summary */}
      <div className="bg-[var(--bg-subtle)] rounded-lg p-4 space-y-2 mb-6">
        <div className="flex justify-between text-sm">
          <span className="text-[var(--text-muted)]">Donante</span>
          <span className="font-medium text-[var(--text-primary)]">{donorName}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-[var(--text-muted)]">Teléfono</span>
          <span className="font-mono text-[var(--text-primary)]">{phoneDisplay}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-sm text-[var(--text-muted)]">Monto</span>
          <span className="font-bold text-lg text-[var(--text-primary)]">
            {formatPyg(amountPyg)}
          </span>
        </div>
      </div>

      {/* Countdown — only while pending */}
      {status === 'pending' && (
        <div className="text-center mb-6">
          <p className="text-sm text-[var(--text-muted)] mb-1">Tiempo restante</p>
          <div className={[
            'text-4xl font-mono font-bold tabular-nums',
            msRemaining < 60_000
              ? 'text-[var(--color-error)]'
              : 'text-[var(--text-primary)]',
          ].join(' ')}>
            {formatCountdown(msRemaining)}
          </div>
        </div>
      )}

      {/* Actions */}
      {(status === 'rejected' || status === 'expired' || status === 'failed') && (
        <a
          href="/donate"
          className="block w-full py-3 px-6 bg-[var(--color-primary)] hover:bg-[var(--color-primary-hover)] text-white font-semibold rounded-lg text-center transition-colors"
        >
          Intentar nuevamente
        </a>
      )}

      {status === 'approved' && (
        <a
          href="/"
          className="block w-full py-3 px-6 bg-[var(--color-success)] text-white font-semibold rounded-lg text-center transition-colors"
        >
          Volver al inicio
        </a>
      )}

      {status === 'pending' && (
        <p className="text-xs text-[var(--text-muted)] text-center mt-4">
          Esta página se actualiza automáticamente cuando apruebes el cobro.
        </p>
      )}
    </div>
  )
}
```

### Status Poll API Route

```typescript
// src/app/api/tigo-money/status/[id]/route.ts
import { createClient } from '@/lib/supabase/server'
import { NextResponse } from 'next/server'

export async function GET(
  _req: Request,
  { params }: { params: { id: string } },
) {
  const supabase = await createClient()

  const { data, error } = await supabase
    .from('tigo_money_donations')
    .select('status')
    .eq('id', params.id)
    .single()

  if (error || !data) {
    return NextResponse.json({ error: 'Not found' }, { status: 404 })
  }

  return NextResponse.json({ status: data.status })
}
```

### Tigo Money Webhook Edge Function

```typescript
// supabase/functions/tigo-money-webhook/index.ts
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const SUPABASE_URL = Deno.env.get('SUPABASE_URL')!
const SUPABASE_SERVICE_ROLE_KEY = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!

// Service role client — bypasses RLS for status updates
const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

// Tigo Money status codes → internal status
const STATUS_MAP: Record<string, string> = {
  SUCCESS: 'approved',
  FAILED: 'failed',
  REJECTED: 'rejected',
  EXPIRED: 'expired',
}

Deno.serve(async (req: Request): Promise<Response> => {
  if (req.method !== 'POST') {
    return new Response('Method not allowed', { status: 405 })
  }

  let body: Record<string, unknown>

  try {
    body = await req.json()
  } catch {
    return new Response('Invalid JSON', { status: 400 })
  }

  const clientTransactionId = body.ClientTransactionId as string | undefined
  const tigoStatus = body.Status as string | undefined
  const tigoReference = body.TigoReference as string | undefined
  const failureReason = body.FailureReason as string | undefined

  if (!clientTransactionId || !tigoStatus) {
    return new Response('Missing required fields', { status: 400 })
  }

  const internalStatus = STATUS_MAP[tigoStatus]

  if (!internalStatus) {
    // Unknown status — log and acknowledge to prevent Tigo retries
    console.warn(`Unknown Tigo status: ${tigoStatus} for transaction ${clientTransactionId}`)
    return new Response(JSON.stringify({ received: true }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    })
  }

  const { error } = await supabase
    .from('tigo_money_donations')
    .update({
      status: internalStatus,
      tigo_reference: tigoReference ?? null,
      failure_reason: failureReason ?? null,
      updated_at: new Date().toISOString(),
    })
    .eq('tigo_transaction_id', clientTransactionId)

  if (error) {
    console.error('Failed to update tigo_money_donations:', {
      clientTransactionId,
      status: internalStatus,
      error: error.message,
    })
    // Still return 200 — Tigo will retry if we return non-2xx
  }

  return new Response(JSON.stringify({ received: true }), {
    status: 200,
    headers: { 'Content-Type': 'application/json' },
  })
})
```

### Deploy Command

```bash
supabase functions deploy tigo-money-webhook --no-verify-jwt
```

`--no-verify-jwt` is required — Tigo Money cannot provide a Supabase JWT. The webhook identity is verified by matching `ClientTransactionId` against known records.

### Environment Variables

Add to `.env.local` and `.env.example`:

```bash
# Already from T01:
# TIGO_MONEY_CLIENT_ID=
# TIGO_MONEY_CLIENT_SECRET=
# TIGO_MONEY_MERCHANT_ID=
# TIGO_MONEY_BASE_URL=
TIGO_MONEY_CALLBACK_URL=https://your-project.supabase.co/functions/v1/tigo-money-webhook
```

### Unit Tests

```typescript
// src/components/donations/__tests__/TigoMoneyForm.test.tsx
import { render, screen, fireEvent } from '@testing-library/react'
import { TigoMoneyForm } from '../TigoMoneyForm'

// Mock the Server Action
jest.mock('@/app/(donations)/donate/actions', () => ({
  createTigoMoneyDonation: jest.fn(),
}))

describe('TigoMoneyForm', () => {
  it('renders PYG preset amount buttons', () => {
    render(<TigoMoneyForm />)
    expect(screen.getByText('₲50.000')).toBeInTheDocument()
    expect(screen.getByText('₲100.000')).toBeInTheDocument()
    expect(screen.getByText('₲250.000')).toBeInTheDocument()
    expect(screen.getByText('₲500.000')).toBeInTheDocument()
  })

  it('shows validation error when amount is too low', async () => {
    render(<TigoMoneyForm />)
    const input = screen.getByPlaceholderText('Otro monto en ₲...')
    fireEvent.change(input, { target: { value: '500' } })
    fireEvent.submit(screen.getByRole('form') ?? document.querySelector('form')!)
    expect(await screen.findByText(/monto mínimo/i)).toBeInTheDocument()
  })

  it('selects preset amount on click', () => {
    render(<TigoMoneyForm />)
    fireEvent.click(screen.getByText('₲100.000'))
    const input = screen.getByPlaceholderText('Otro monto en ₲...') as HTMLInputElement
    expect(input.value).toBe('100000')
  })
})
```

## Related Issues

- EPIC-3
- S03
- T01 (provides `TigoMoneyService` and `normalizeParaguayPhone` used by the Server Action)
