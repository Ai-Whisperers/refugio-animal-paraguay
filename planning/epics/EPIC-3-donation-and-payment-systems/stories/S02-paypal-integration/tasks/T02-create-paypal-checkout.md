---
task: T02
story: S02
epic: EPIC-3
title: Create EU bank transfer (SEPA) donation flow UI
status: ready
priority: medium
created: 2026-03-25T17:13:26.729237
---

# T02: Create EU Bank Transfer (SEPA) Donation Flow UI

## Description

Build the donor-facing UI for SEPA/EU bank transfer donations. After a donor selects "Bank Transfer (EU/SEPA)" as their payment method and submits their details, they receive clear transfer instructions: bank account details, the exact amount, and a unique payment reference code they must include in the bank transfer description. A Server Action persists the pending donation record.

> **Tech note**: This story was originally labeled "PayPal checkout" but reframed as SEPA. See T01 for context.

## Acceptance Criteria

- [ ] `BankTransferForm` client component captures donor name and email
- [ ] Server Action `createBankTransferDonation()` in `src/app/(donations)/donate/actions.ts`
- [ ] After submission, donor sees a `BankTransferInstructions` page with all transfer details
- [ ] Payment reference code displayed prominently — donors must include it in transfer
- [ ] Bank details (IBAN, BIC, account name) rendered server-side only (not exposed to client JS)
- [ ] Email confirmation sent to donor after form submission (via Resend)
- [ ] Transfer instructions accessible at `/donate/transferencia-bancaria/[reference]`
- [ ] Pending transfer persisted in `bank_transfer_donations` table (T01 schema)
- [ ] All CSS uses `var(--*)` pattern — no hardcoded colors

## Implementation Notes

### Server Action

```typescript
// Addition to src/app/(donations)/donate/actions.ts

'use server'

import { createClient } from '@/lib/supabase/server'
import { bankTransferService } from '@/lib/payments/bank-transfer-service'
import { validateIBAN } from '@/lib/payments/iban-validator'
import { revalidatePath } from 'next/cache'
import { redirect } from 'next/navigation'

export interface CreateBankTransferResult {
  success: boolean
  reference?: string
  error?: string
}

export async function createBankTransferDonation(
  amount: number,
  donorName: string,
  donorEmail: string,
  campaignId?: string,
): Promise<CreateBankTransferResult> {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()

  // Generate reference and expiry
  const reference = bankTransferService.generatePaymentReference()
  const expiresAt = new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString()

  const { error } = await supabase.from('bank_transfer_donations').insert({
    payment_reference: reference,
    amount: Math.round(amount * 100),   // store in euro cents
    currency: 'eur',
    donor_name: donorName,
    donor_email: donorEmail,
    donor_user_id: user?.id ?? null,    // nullable for anonymous donors
    campaign_id: campaignId ?? null,
    status: 'pending_transfer',
    expires_at: expiresAt,
  })

  if (error) {
    console.error('Failed to create bank transfer donation:', error)
    return { success: false, error: 'Failed to save donation record. Please try again.' }
  }

  // Send confirmation email with transfer instructions
  await sendBankTransferConfirmationEmail({
    donorEmail,
    donorName,
    reference,
    amount,
    expiresAt,
  })

  // redirect() must be outside try/catch — it throws internally
  revalidatePath('/donate')
  redirect(`/donate/transferencia-bancaria/${reference}`)
}

async function sendBankTransferConfirmationEmail(params: {
  donorEmail: string
  donorName: string
  reference: string
  amount: number
  expiresAt: string
}): Promise<void> {
  const bankDetails = bankTransferService.getBankDetails()

  try {
    const res = await fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${process.env.RESEND_API_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        from: 'Refugio Animal Paraguay <donaciones@refugio-animal.org>',
        to: params.donorEmail,
        subject: `Instrucciones de transferencia — ${params.reference}`,
        html: buildTransferInstructionsEmailHtml({ ...params, bankDetails }),
      }),
    })

    if (!res.ok) {
      throw new Error(`Resend API returned ${res.status}`)
    }
  } catch (err) {
    // Email failure should not block the donor flow — log and continue
    console.error('Failed to send bank transfer confirmation email:', {
      donorEmail: params.donorEmail,
      reference: params.reference,
      error: err instanceof Error ? err.message : String(err),
    })
  }
}
```

### Form Component

```typescript
// src/components/donations/BankTransferForm.tsx
'use client'

import { useState, useTransition } from 'react'
import { createBankTransferDonation } from '@/app/(donations)/donate/actions'

interface BankTransferFormProps {
  preselectedAmount?: number
  campaignId?: string
}

export function BankTransferForm({ preselectedAmount, campaignId }: BankTransferFormProps) {
  const [isPending, startTransition] = useTransition()
  const [amount, setAmount] = useState<string>(preselectedAmount?.toString() ?? '')
  const [donorName, setDonorName] = useState('')
  const [donorEmail, setDonorEmail] = useState('')
  const [error, setError] = useState<string | null>(null)

  const PRESET_AMOUNTS_EUR = [25, 50, 100, 250] as const

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)

    const parsedAmount = parseFloat(amount)
    if (isNaN(parsedAmount) || parsedAmount < 5) {
      setError('El monto mínimo de donación es €5.00')
      return
    }

    startTransition(async () => {
      const result = await createBankTransferDonation(
        parsedAmount,
        donorName.trim(),
        donorEmail.trim(),
        campaignId,
      )
      // On success, the Server Action redirects — we only land here on error
      if (!result.success) {
        setError(result.error ?? 'Ocurrió un error. Por favor intente nuevamente.')
      }
    })
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-6">
      {/* Amount Presets */}
      <div className="flex flex-col gap-2">
        <label className="text-sm font-medium text-[var(--text-primary)]">
          Monto (EUR)
        </label>
        <div className="flex gap-2 flex-wrap">
          {PRESET_AMOUNTS_EUR.map((preset) => (
            <button
              key={preset}
              type="button"
              onClick={() => setAmount(preset.toString())}
              className={[
                'px-4 py-2 rounded-lg border text-sm font-medium transition-colors',
                amount === preset.toString()
                  ? 'bg-[var(--color-primary)] text-white border-[var(--color-primary)]'
                  : 'bg-[var(--bg-card)] text-[var(--text-secondary)] border-[var(--border-color)] hover:border-[var(--color-primary)]',
              ].join(' ')}
            >
              €{preset}
            </button>
          ))}
        </div>
        <input
          type="number"
          min="5"
          step="0.01"
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
          placeholder="Otro monto..."
          className="w-full px-4 py-3 rounded-lg border border-[var(--border-color)] bg-[var(--bg-input)] text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]"
          required
        />
      </div>

      {/* Donor Details */}
      <div className="flex flex-col gap-4">
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
        <div>
          <label className="block text-sm font-medium text-[var(--text-primary)] mb-1">
            Correo electrónico
          </label>
          <input
            type="email"
            value={donorEmail}
            onChange={(e) => setDonorEmail(e.target.value)}
            placeholder="tu@email.com"
            className="w-full px-4 py-3 rounded-lg border border-[var(--border-color)] bg-[var(--bg-input)] text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]"
            required
          />
        </div>
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
        {isPending ? 'Procesando...' : 'Ver instrucciones de transferencia'}
      </button>

      <p className="text-xs text-[var(--text-muted)] text-center">
        Recibirás las instrucciones de transferencia por email.
        Las transferencias SEPA se procesan en 1-3 días hábiles.
      </p>
    </form>
  )
}
```

### Transfer Instructions Page (Server Component)

```typescript
// src/app/(donations)/donate/transferencia-bancaria/[reference]/page.tsx
import { createClient } from '@/lib/supabase/server'
import { bankTransferService } from '@/lib/payments/bank-transfer-service'
import { notFound } from 'next/navigation'
import { CopyButton } from '@/components/ui/CopyButton'

interface Props {
  params: { reference: string }
}

export default async function BankTransferInstructionsPage({ params }: Props) {
  const supabase = await createClient()

  const { data: donation } = await supabase
    .from('bank_transfer_donations')
    .select('payment_reference, amount, currency, donor_name, expires_at, status')
    .eq('payment_reference', params.reference)
    .single()

  if (!donation) {
    notFound()
  }

  // Bank details fetched server-side — never exposed to client bundle
  const bankDetails = bankTransferService.getBankDetails()
  const amountEur = (donation.amount / 100).toFixed(2)
  const expiryDate = new Date(donation.expires_at).toLocaleDateString('es-PY', {
    day: '2-digit', month: 'long', year: 'numeric',
  })

  return (
    <div className="max-w-lg mx-auto px-4 py-12">
      <div className="bg-[var(--bg-card)] rounded-2xl p-8 shadow-sm border border-[var(--border-color)]">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="text-4xl mb-3">🏦</div>
          <h1 className="text-2xl font-bold text-[var(--text-primary)]">
            Instrucciones de Transferencia
          </h1>
          <p className="text-[var(--text-secondary)] mt-2">
            Realiza la transferencia desde tu banco online para completar tu donación.
          </p>
        </div>

        {/* Transfer Details */}
        <div className="space-y-4">
          <TransferDetailRow label="Beneficiario" value={bankDetails.accountName} />
          <TransferDetailRow
            label="IBAN"
            value={bankDetails.iban}
            copyable
          />
          <TransferDetailRow label="BIC / SWIFT" value={bankDetails.bic} copyable />
          <TransferDetailRow
            label="Monto exacto"
            value={`€${amountEur}`}
            highlight
          />
          <TransferDetailRow
            label="Concepto / Referencia"
            value={donation.payment_reference}
            copyable
            highlight
            helpText="Es obligatorio incluir este código exacto en el concepto de la transferencia."
          />
        </div>

        {/* Important notice */}
        <div className="mt-6 p-4 bg-[var(--bg-warning-subtle)] rounded-lg border border-[var(--border-warning)]">
          <p className="text-sm text-[var(--text-warning)] font-medium">
            ⚠️ Importante
          </p>
          <ul className="mt-2 text-sm text-[var(--text-secondary)] list-disc list-inside space-y-1">
            <li>Incluye el código de referencia exacto en el concepto</li>
            <li>Transfiere el monto exacto indicado</li>
            <li>Las transferencias SEPA tardan 1-3 días hábiles</li>
            <li>Este enlace expira el {expiryDate}</li>
          </ul>
        </div>

        <p className="mt-6 text-sm text-[var(--text-muted)] text-center">
          Te enviaremos una confirmación a tu correo cuando recibamos tu transferencia.
        </p>
      </div>
    </div>
  )
}

function TransferDetailRow({
  label,
  value,
  copyable = false,
  highlight = false,
  helpText,
}: {
  label: string
  value: string
  copyable?: boolean
  highlight?: boolean
  helpText?: string
}) {
  return (
    <div className={[
      'p-4 rounded-lg border',
      highlight
        ? 'bg-[var(--bg-highlight)] border-[var(--border-highlight)]'
        : 'bg-[var(--bg-subtle)] border-[var(--border-color)]',
    ].join(' ')}>
      <p className="text-xs font-medium text-[var(--text-muted)] uppercase tracking-wide">
        {label}
      </p>
      <div className="flex items-center justify-between mt-1">
        <p className={[
          'font-mono text-base',
          highlight
            ? 'font-bold text-[var(--text-primary)]'
            : 'text-[var(--text-primary)]',
        ].join(' ')}>
          {value}
        </p>
        {copyable && <CopyButton value={value} />}
      </div>
      {helpText && (
        <p className="text-xs text-[var(--text-muted)] mt-1">{helpText}</p>
      )}
    </div>
  )
}
```

### CopyButton Component (shared UI)

```typescript
// src/components/ui/CopyButton.tsx
'use client'

import { useState } from 'react'

export function CopyButton({ value }: { value: string }) {
  const [copied, setCopied] = useState(false)

  async function handleCopy() {
    await navigator.clipboard.writeText(value)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <button
      type="button"
      onClick={handleCopy}
      className="text-xs px-2 py-1 rounded bg-[var(--bg-card)] border border-[var(--border-color)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors"
    >
      {copied ? '✓ Copiado' : 'Copiar'}
    </button>
  )
}
```

## Related Issues

- EPIC-3
- S02
- T01 (provides `BankTransferService` and schema)
