---
task: T02
story: S01
epic: EPIC-3
title: Create payment form
status: ready
priority: medium
created: 2026-03-25T17:13:26.728922
---

# T02: Create Payment Form

## Description

Build the donation payment form using Stripe Elements (Stripe.js) embedded in a Next.js Client Component. The form captures donor details and card information, calls a Server Action to create a PaymentIntent server-side, then confirms the payment client-side using the returned `clientSecret`. Supports EUR, PYG, and USD with a currency selector. Displays real-time validation errors from Stripe.

## Context

**Files to create/modify**:
- `src/app/(donations)/donate/page.tsx` — Server Component page wrapper
- `src/app/(donations)/donate/DonationForm.tsx` — Client Component with Stripe Elements
- `src/app/(donations)/donate/actions.ts` — Server Actions: `createDonationIntent`, `saveDonationRecord`
- `src/components/ui/CurrencySelector.tsx` — Reusable currency picker
- `src/components/ui/AmountPresets.tsx` — Quick-select preset amounts

**Environment variables** (from T01):
- `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` — exposed to client via `NEXT_PUBLIC_` prefix
- `STRIPE_SECRET_KEY` — server-only (used in Server Action)

**Architecture references**:
- `stripePaymentService.createPaymentIntent()` from T01
- Supabase `donations` table for persisting payment records
- `(await supabase.auth.getUser()).data.user?.id` for authenticated donor ID
- Server Actions (`'use server'`) for all mutations — no API routes
- `useTransition` for pending state on form submission — NOT `useState<boolean>`

## Implementation

### 1. Server Action — Create PaymentIntent

```typescript
// src/app/(donations)/donate/actions.ts
'use server'

import { createClient } from '@/lib/supabase/server'
import { stripePaymentService } from '@/services/payment/stripe-service'
import { revalidatePath } from 'next/cache'

export type CreateDonationIntentResult =
  | { success: true; clientSecret: string; intentId: string }
  | { success: false; error: string }

export async function createDonationIntent(
  amount: number,
  currency: 'eur' | 'pyg' | 'usd',
  donorName: string,
  donorEmail: string,
  campaignId?: string,
): Promise<CreateDonationIntentResult> {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()

  const result = await stripePaymentService.createPaymentIntent({
    amount,
    currency,
    description: `Refugio Animal Paraguay — Donación${campaignId ? ` (Campaña ${campaignId})` : ''}`,
    metadata: {
      donorName,
      donorEmail,
      campaignId: campaignId ?? '',
      donorUserId: user?.id ?? 'anonymous',
    },
  })

  if (!result.success) {
    return { success: false, error: result.error }
  }

  return {
    success: true,
    clientSecret: result.data.clientSecret,
    intentId: result.data.id,
  }
}

export async function saveDonationRecord(
  intentId: string,
  amount: number,
  currency: 'eur' | 'pyg' | 'usd',
  donorName: string,
  donorEmail: string,
): Promise<{ success: boolean; error?: string }> {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()

  const { error } = await supabase.from('donations').insert({
    stripe_intent_id: intentId,
    donor_user_id: user?.id ?? null,
    donor_name: donorName,
    donor_email: donorEmail,
    amount_cents: amount,
    currency,
    status: 'pending', // Stripe webhook (T03) updates this to 'succeeded' or 'failed'
  })

  if (error) {
    console.error('[saveDonationRecord] Supabase insert failed:', error)
    return { success: false, error: error.message }
  }

  revalidatePath('/donate')
  return { success: true }
}
```

### 2. Donation Page (Server Component)

```typescript
// src/app/(donations)/donate/page.tsx
import { DonationForm } from './DonationForm'

export const metadata = {
  title: 'Donar — Refugio Animal Paraguay',
  description: 'Apoya a los animales del refugio con tu donación',
}

export default function DonatePage() {
  return (
    <main className="min-h-screen bg-[var(--bg-page)] py-12">
      <div className="mx-auto max-w-lg px-4">
        <div className="rounded-2xl bg-[var(--bg-card)] p-8 shadow-sm">
          <h1 className="mb-2 text-2xl font-bold text-[var(--text-primary)]">
            Hacer una donación
          </h1>
          <p className="mb-8 text-sm text-[var(--text-secondary)]">
            Tu apoyo cambia vidas. Cada donación va directamente al cuidado de los animales.
          </p>
          <DonationForm />
        </div>
      </div>
    </main>
  )
}
```

### 3. DonationForm Client Component

```typescript
// src/app/(donations)/donate/DonationForm.tsx
'use client'

import { useState, useTransition } from 'react'
import { loadStripe } from '@stripe/stripe-js'
import {
  Elements,
  PaymentElement,
  useStripe,
  useElements,
} from '@stripe/react-stripe-js'
import { createDonationIntent, saveDonationRecord } from './actions'
import { AmountPresets } from '@/components/ui/AmountPresets'
import { CurrencySelector } from '@/components/ui/CurrencySelector'

const stripePromise = loadStripe(process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY!)

const CURRENCY_MINIMUMS: Record<string, number> = {
  eur: 100,   // €1.00
  usd: 100,   // $1.00
  pyg: 1000,  // ₲1,000
}

export function DonationForm() {
  const [clientSecret, setClientSecret] = useState<string | null>(null)
  const [intentId, setIntentId] = useState<string | null>(null)
  const [amount, setAmount] = useState<number>(2500) // €25.00 default
  const [currency, setCurrency] = useState<'eur' | 'pyg' | 'usd'>('eur')
  const [donorName, setDonorName] = useState('')
  const [donorEmail, setDonorEmail] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isPending, startTransition] = useTransition()

  const handleContinue = () => {
    setError(null)

    if (amount < CURRENCY_MINIMUMS[currency]) {
      setError(`El monto mínimo es ${CURRENCY_MINIMUMS[currency] / 100} ${currency.toUpperCase()}`)
      return
    }
    if (!donorName.trim() || !donorEmail.trim()) {
      setError('Por favor completa tu nombre y correo electrónico.')
      return
    }

    startTransition(async () => {
      const result = await createDonationIntent(amount, currency, donorName, donorEmail)
      if (!result.success) {
        setError(result.error)
        return
      }
      setClientSecret(result.clientSecret)
      setIntentId(result.intentId)
    })
  }

  if (clientSecret) {
    return (
      <Elements
        stripe={stripePromise}
        options={{ clientSecret, appearance: { theme: 'stripe' } }}
      >
        <CheckoutForm
          intentId={intentId!}
          amount={amount}
          currency={currency}
          donorName={donorName}
          donorEmail={donorEmail}
        />
      </Elements>
    )
  }

  return (
    <div className="space-y-6">
      <CurrencySelector value={currency} onChange={setCurrency} />
      <AmountPresets currency={currency} value={amount} onChange={setAmount} />

      <div className="space-y-4">
        <div>
          <label className="mb-1 block text-sm font-medium text-[var(--text-primary)]">
            Nombre completo
          </label>
          <input
            type="text"
            value={donorName}
            onChange={(e) => setDonorName(e.target.value)}
            placeholder="María González"
            className="w-full rounded-lg border border-[var(--border)] bg-[var(--bg-input)] px-3 py-2 text-sm text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none focus:ring-2 focus:ring-[var(--ring)]"
          />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-[var(--text-primary)]">
            Correo electrónico
          </label>
          <input
            type="email"
            value={donorEmail}
            onChange={(e) => setDonorEmail(e.target.value)}
            placeholder="maria@ejemplo.com"
            className="w-full rounded-lg border border-[var(--border)] bg-[var(--bg-input)] px-3 py-2 text-sm text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none focus:ring-2 focus:ring-[var(--ring)]"
          />
        </div>
      </div>

      {error && (
        <p className="rounded-lg bg-red-50 px-4 py-2 text-sm text-red-700">{error}</p>
      )}

      <button
        onClick={handleContinue}
        disabled={isPending}
        className="w-full rounded-lg bg-[var(--color-primary)] px-4 py-3 text-sm font-semibold text-white transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {isPending ? 'Procesando...' : 'Continuar al pago'}
      </button>
    </div>
  )
}

interface CheckoutFormProps {
  intentId: string
  amount: number
  currency: 'eur' | 'pyg' | 'usd'
  donorName: string
  donorEmail: string
}

function CheckoutForm({ intentId, amount, currency, donorName, donorEmail }: CheckoutFormProps) {
  const stripe = useStripe()
  const elements = useElements()
  const [error, setError] = useState<string | null>(null)
  const [isPending, startTransition] = useTransition()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!stripe || !elements) return
    setError(null)

    startTransition(async () => {
      // Persist the record first; webhook (T03) will update status async
      await saveDonationRecord(intentId, amount, currency, donorName, donorEmail)

      const { error: stripeError } = await stripe.confirmPayment({
        elements,
        confirmParams: {
          return_url: `${window.location.origin}/donate/gracias`,
          payment_method_data: {
            billing_details: { name: donorName, email: donorEmail },
          },
        },
      })

      // confirmPayment redirects on success — only reaches here on error
      if (stripeError) {
        setError(stripeError.message ?? 'Error al procesar el pago. Intenta nuevamente.')
      }
    })
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <PaymentElement />
      {error && (
        <p className="rounded-lg bg-red-50 px-4 py-2 text-sm text-red-700">{error}</p>
      )}
      <button
        type="submit"
        disabled={!stripe || isPending}
        className="w-full rounded-lg bg-[var(--color-primary)] px-4 py-3 text-sm font-semibold text-white transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {isPending ? 'Procesando...' : `Donar ${amount / 100} ${currency.toUpperCase()}`}
      </button>
    </form>
  )
}
```

### 4. Amount Presets Component

```typescript
// src/components/ui/AmountPresets.tsx
'use client'

const PRESETS: Record<string, number[]> = {
  eur: [1000, 2500, 5000, 10000],       // €10, €25, €50, €100
  usd: [1000, 2500, 5000, 10000],
  pyg: [50000, 100000, 250000, 500000], // ₲50K, ₲100K, ₲250K, ₲500K
}

const CURRENCY_SYMBOLS: Record<string, string> = { eur: '€', usd: '$', pyg: '₲' }
const CURRENCY_DIVISORS: Record<string, number> = { eur: 100, usd: 100, pyg: 1 }

interface AmountPresetsProps {
  currency: 'eur' | 'pyg' | 'usd'
  value: number
  onChange: (amount: number) => void
}

export function AmountPresets({ currency, value, onChange }: AmountPresetsProps) {
  const symbol = CURRENCY_SYMBOLS[currency]
  const presets = PRESETS[currency]
  const divisor = CURRENCY_DIVISORS[currency]

  return (
    <div className="space-y-2">
      <label className="block text-sm font-medium text-[var(--text-primary)]">Monto</label>
      <div className="grid grid-cols-4 gap-2">
        {presets.map((preset) => (
          <button
            key={preset}
            type="button"
            onClick={() => onChange(preset)}
            className={`rounded-lg border px-3 py-2 text-sm font-medium transition ${
              value === preset
                ? 'border-[var(--color-primary)] bg-[var(--color-primary)] text-white'
                : 'border-[var(--border)] bg-[var(--bg-card)] text-[var(--text-primary)] hover:border-[var(--color-primary)]'
            }`}
          >
            {symbol}{(preset / divisor).toLocaleString()}
          </button>
        ))}
      </div>
      <input
        type="number"
        value={value / divisor}
        onChange={(e) => onChange(Math.round(Number(e.target.value) * divisor))}
        placeholder="Otro monto"
        min={0}
        className="w-full rounded-lg border border-[var(--border)] bg-[var(--bg-input)] px-3 py-2 text-sm text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--ring)]"
      />
    </div>
  )
}
```

### 5. Currency Selector Component

```typescript
// src/components/ui/CurrencySelector.tsx
'use client'

const CURRENCIES = [
  { code: 'eur', label: 'Euro (€)', flag: '🇪🇺' },
  { code: 'usd', label: 'Dólar ($)', flag: '🇺🇸' },
  { code: 'pyg', label: 'Guaraní (₲)', flag: '🇵🇾' },
] as const

interface CurrencySelectorProps {
  value: 'eur' | 'pyg' | 'usd'
  onChange: (currency: 'eur' | 'pyg' | 'usd') => void
}

export function CurrencySelector({ value, onChange }: CurrencySelectorProps) {
  return (
    <div className="space-y-1">
      <label className="block text-sm font-medium text-[var(--text-primary)]">Moneda</label>
      <div className="flex gap-2">
        {CURRENCIES.map(({ code, label, flag }) => (
          <button
            key={code}
            type="button"
            onClick={() => onChange(code)}
            className={`flex flex-1 items-center justify-center gap-1.5 rounded-lg border px-3 py-2 text-xs font-medium transition ${
              value === code
                ? 'border-[var(--color-primary)] bg-[var(--color-primary)] text-white'
                : 'border-[var(--border)] bg-[var(--bg-card)] text-[var(--text-primary)] hover:border-[var(--color-primary)]'
            }`}
          >
            <span>{flag}</span>
            <span>{label}</span>
          </button>
        ))}
      </div>
    </div>
  )
}
```

## Acceptance Criteria

- [ ] `DonationForm` is a Client Component (`'use client'`) using `useTransition` for pending state — no `useState<boolean>` for loading
- [ ] Server Action `createDonationIntent` creates PaymentIntent server-side; `clientSecret` never constructed client-side
- [ ] `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` used to initialize `loadStripe()` on client
- [ ] `Elements` provider wraps `CheckoutForm` with `clientSecret` and appearance options
- [ ] `PaymentElement` renders Stripe's hosted card UI (PCI compliant — card data never touches app server)
- [ ] `stripe.confirmPayment` redirects to `/donate/gracias` on success; error displayed inline on failure
- [ ] `AmountPresets` shows 4 preset amounts per currency with custom amount input field
- [ ] `CurrencySelector` allows switching EUR / USD / PYG before proceeding to checkout
- [ ] Donor name and email collected before Stripe Elements shown; passed as `billing_details`
- [ ] `saveDonationRecord` inserts row into Supabase `donations` table with `status: 'pending'`
- [ ] Minimum amount validation per currency (€1 / $1 / ₲1000) shown as inline error before proceeding
- [ ] All CSS uses `bg-[var(--bg-card)]`, `text-[var(--text-primary)]` CSS vars — no hardcoded colors
- [ ] Anonymous donations supported: `donor_user_id` is nullable in insert
- [ ] Type checking passes with zero type errors
- [ ] Linting passes with zero warnings

## Implementation Notes

**`redirect()` is not used here** — Stripe's `confirmPayment` handles the redirect to `/donate/gracias` via `return_url`. The Server Action returns data, never redirects.

**`useTransition` pattern**: Wraps both the `createDonationIntent` call and the `stripe.confirmPayment` call in `startTransition`. The `isPending` flag drives disabled/loading states on buttons.

**PCI compliance**: Card data never touches the application server. Stripe Elements handles tokenization client-side.

**Status flow**: `pending` (inserted by this task) → `succeeded` or `failed` (updated by Stripe webhook in T03).

**PyG amounts**: Guaraní has no decimal places — divisor is 1, not 100. The `amount_cents` column stores raw Guaraní units for PYG rows.
