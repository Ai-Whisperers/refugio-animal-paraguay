---
task: T01
story: S04
epic: EPIC-3
title: Create donation history view
status: ready
priority: medium
created: 2026-03-25T17:13:26.729684
---

# T01: Create donation history view

## Description

Build a donor-facing donation history page at `/account/donations` that aggregates records from all three payment methods — Stripe (`donations`), SEPA bank transfer (`bank_transfer_donations`), and Tigo Money (`tigo_money_donations`) — into a single chronological list. The page shows each donation's method, amount, currency, status, and date. Access is restricted to authenticated donors who can only see their own records.

## Acceptance Criteria

- [ ] Page at `/account/donations` is a Server Component that fetches all three payment tables
- [ ] Only shows donations belonging to `auth.uid()` — no cross-donor data leakage
- [ ] Amounts formatted correctly: EUR as `€X.XX`, PYG as `₲X,XXX` (no decimals)
- [ ] Status badge rendered per payment method's status vocabulary
- [ ] Donations sorted newest-first
- [ ] Empty state rendered when donor has no donations
- [ ] Loading skeleton displayed during data fetch (Suspense boundary)
- [ ] Page is accessible (WCAG 2.1 AA): status badges have aria-labels, amounts have lang attribute)
- [ ] No hardcoded colors — CSS vars only

## Implementation Notes

### Route and File Structure

```
src/app/account/donations/
  page.tsx                        ← Server Component (data fetch + layout)
  loading.tsx                     ← Skeleton (auto-used by Next.js Suspense)
  _components/
    DonationHistoryList.tsx       ← Renders sorted unified list
    DonationRow.tsx               ← Single row: method icon, amount, status, date
    DonationStatusBadge.tsx       ← Status pill with per-method color mapping
    EmptyDonationState.tsx        ← Empty state illustration + CTA
```

### Data Model — Unified Donation Record

Define a canonical type that normalizes across all three payment methods:

```typescript
// src/types/donation-history.ts

export type PaymentMethod = 'stripe' | 'sepa' | 'tigo_money'
export type DonationCurrency = 'eur' | 'pyg'

export interface UnifiedDonation {
  id: string
  method: PaymentMethod
  amount: number          // EUR stored as cents (divide by 100); PYG stored as whole integer
  currency: DonationCurrency
  status: string          // raw status from each table — badge maps to display
  createdAt: string       // ISO 8601
  campaignName: string | null
}
```

### Supabase Query — Three Tables, One Donor

`page.tsx` is a Server Component. It creates a Supabase server client, gets the authenticated user, then queries all three tables in parallel:

```typescript
// src/app/account/donations/page.tsx
import { createClient } from '@/lib/supabase/server'
import { redirect } from 'next/navigation'
import { DonationHistoryList } from './_components/DonationHistoryList'
import type { UnifiedDonation } from '@/types/donation-history'

export default async function DonationHistoryPage() {
  const supabase = createClient()

  const { data: { user } } = await supabase.auth.getUser()
  if (!user) {
    redirect('/auth/login?next=/account/donations')
  }

  const [stripeResult, sepaResult, tigoResult] = await Promise.all([
    supabase
      .from('donations')
      .select('id, amount_cents, currency, status, created_at, campaign_name')
      .eq('donor_user_id', user.id)
      .order('created_at', { ascending: false }),

    supabase
      .from('bank_transfer_donations')
      .select('id, amount_cents, currency, status, created_at, campaign_name')
      .eq('donor_user_id', user.id)
      .order('created_at', { ascending: false }),

    supabase
      .from('tigo_money_donations')
      .select('id, amount, currency, status, created_at, campaign_name')
      .eq('donor_user_id', user.id)
      .order('created_at', { ascending: false }),
  ])

  // Normalize into unified shape
  const stripeDonations: UnifiedDonation[] = (stripeResult.data ?? []).map(d => ({
    id: d.id,
    method: 'stripe',
    amount: d.amount_cents,   // EUR cents — display layer divides by 100
    currency: d.currency,
    status: d.status,
    createdAt: d.created_at,
    campaignName: d.campaign_name ?? null,
  }))

  const sepaDonations: UnifiedDonation[] = (sepaResult.data ?? []).map(d => ({
    id: d.id,
    method: 'sepa',
    amount: d.amount_cents,   // EUR cents
    currency: d.currency,
    status: d.status,
    createdAt: d.created_at,
    campaignName: d.campaign_name ?? null,
  }))

  const tigoDonations: UnifiedDonation[] = (tigoResult.data ?? []).map(d => ({
    id: d.id,
    method: 'tigo_money',
    amount: d.amount,         // PYG whole integer — display layer does NOT divide
    currency: d.currency,
    status: d.status,
    createdAt: d.created_at,
    campaignName: d.campaign_name ?? null,
  }))

  // Merge and sort newest-first
  const allDonations = [...stripeDonations, ...sepaDonations, ...tigoDonations]
    .sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime())

  return (
    <main className="max-w-3xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-semibold text-[var(--text-primary)] mb-6">
        Mis Donaciones
      </h1>
      <DonationHistoryList donations={allDonations} />
    </main>
  )
}
```

### Amount Formatting

PYG has no decimal places. EUR is stored in cents and displayed with 2 decimal places. Use a single formatter function:

```typescript
// src/lib/format-donation-amount.ts

export function formatDonationAmount(
  amount: number,
  currency: 'eur' | 'pyg'
): string {
  if (currency === 'pyg') {
    // amount is already whole guaraní — no division
    return `₲${amount.toLocaleString('es-PY')}`
  }
  // EUR is stored as cents — divide by 100
  return `€${(amount / 100).toFixed(2)}`
}
```

### Status Badge — Per-Method Vocabulary Mapping

Each payment method uses different status strings. The badge normalizes to four display states:

```typescript
// src/app/account/donations/_components/DonationStatusBadge.tsx
'use client'

import type { PaymentMethod } from '@/types/donation-history'

interface StatusDisplay {
  label: string
  className: string
}

// Maps raw DB status → display config, keyed by method
const STATUS_DISPLAY: Record<PaymentMethod, Record<string, StatusDisplay>> = {
  stripe: {
    succeeded:           { label: 'Completado',  className: 'bg-[var(--status-success-bg)] text-[var(--status-success-text)]' },
    payment_failed:      { label: 'Fallido',     className: 'bg-[var(--status-error-bg)] text-[var(--status-error-text)]' },
    pending:             { label: 'Pendiente',   className: 'bg-[var(--status-warning-bg)] text-[var(--status-warning-text)]' },
    refunded:            { label: 'Reembolsado', className: 'bg-[var(--status-neutral-bg)] text-[var(--status-neutral-text)]' },
  },
  sepa: {
    pending_bank_transfer: { label: 'Esperando transferencia', className: 'bg-[var(--status-warning-bg)] text-[var(--status-warning-text)]' },
    transfer_received:     { label: 'Recibido',   className: 'bg-[var(--status-success-bg)] text-[var(--status-success-text)]' },
    confirmed:             { label: 'Confirmado', className: 'bg-[var(--status-success-bg)] text-[var(--status-success-text)]' },
    failed:                { label: 'Fallido',    className: 'bg-[var(--status-error-bg)] text-[var(--status-error-text)]' },
    expired:               { label: 'Vencido',   className: 'bg-[var(--status-error-bg)] text-[var(--status-error-text)]' },
  },
  tigo_money: {
    pending:  { label: 'Esperando aprobación', className: 'bg-[var(--status-warning-bg)] text-[var(--status-warning-text)]' },
    approved: { label: 'Aprobado',  className: 'bg-[var(--status-success-bg)] text-[var(--status-success-text)]' },
    failed:   { label: 'Fallido',   className: 'bg-[var(--status-error-bg)] text-[var(--status-error-text)]' },
    expired:  { label: 'Vencido',   className: 'bg-[var(--status-error-bg)] text-[var(--status-error-text)]' },
    rejected: { label: 'Rechazado', className: 'bg-[var(--status-error-bg)] text-[var(--status-error-text)]' },
  },
}

const FALLBACK_DISPLAY: StatusDisplay = {
  label: 'Desconocido',
  className: 'bg-[var(--status-neutral-bg)] text-[var(--status-neutral-text)]',
}

interface Props {
  method: PaymentMethod
  status: string
}

export function DonationStatusBadge({ method, status }: Props) {
  const display = STATUS_DISPLAY[method]?.[status] ?? FALLBACK_DISPLAY
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${display.className}`}
      aria-label={`Estado: ${display.label}`}
    >
      {display.label}
    </span>
  )
}
```

### Method Icon/Label

```typescript
// src/app/account/donations/_components/DonationMethodLabel.tsx

import type { PaymentMethod } from '@/types/donation-history'

const METHOD_META: Record<PaymentMethod, { label: string; icon: string }> = {
  stripe:     { label: 'Tarjeta de crédito', icon: '💳' },
  sepa:       { label: 'Transferencia SEPA', icon: '🏦' },
  tigo_money: { label: 'Tigo Money',         icon: '📱' },
}

export function DonationMethodLabel({ method }: { method: PaymentMethod }) {
  const { label, icon } = METHOD_META[method]
  return (
    <span className="flex items-center gap-1.5 text-sm text-[var(--text-secondary)]">
      <span aria-hidden="true">{icon}</span>
      {label}
    </span>
  )
}
```

### DonationRow Component

```typescript
// src/app/account/donations/_components/DonationRow.tsx

import { formatDonationAmount } from '@/lib/format-donation-amount'
import { DonationStatusBadge } from './DonationStatusBadge'
import { DonationMethodLabel } from './DonationMethodLabel'
import type { UnifiedDonation } from '@/types/donation-history'

interface Props {
  donation: UnifiedDonation
}

export function DonationRow({ donation }: Props) {
  const formattedAmount = formatDonationAmount(donation.amount, donation.currency)
  const formattedDate = new Date(donation.createdAt).toLocaleDateString('es-PY', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  })

  return (
    <li className="flex items-center justify-between gap-4 py-4 border-b border-[var(--border-muted)] last:border-0">
      <div className="flex flex-col gap-1">
        <DonationMethodLabel method={donation.method} />
        {donation.campaignName && (
          <span className="text-xs text-[var(--text-tertiary)]">{donation.campaignName}</span>
        )}
        <time
          dateTime={donation.createdAt}
          className="text-xs text-[var(--text-tertiary)]"
        >
          {formattedDate}
        </time>
      </div>

      <div className="flex flex-col items-end gap-1 shrink-0">
        <span
          className="text-base font-semibold text-[var(--text-primary)]"
          lang={donation.currency === 'eur' ? 'de' : 'es-PY'}
        >
          {formattedAmount}
        </span>
        <DonationStatusBadge method={donation.method} status={donation.status} />
      </div>
    </li>
  )
}
```

### DonationHistoryList Component

```typescript
// src/app/account/donations/_components/DonationHistoryList.tsx

import { DonationRow } from './DonationRow'
import { EmptyDonationState } from './EmptyDonationState'
import type { UnifiedDonation } from '@/types/donation-history'

interface Props {
  donations: UnifiedDonation[]
}

export function DonationHistoryList({ donations }: Props) {
  if (donations.length === 0) {
    return <EmptyDonationState />
  }

  return (
    <ul
      className="divide-y divide-[var(--border-muted)] rounded-lg border border-[var(--border-default)] bg-[var(--bg-card)] px-4"
      aria-label="Historial de donaciones"
    >
      {donations.map(donation => (
        <DonationRow key={`${donation.method}-${donation.id}`} donation={donation} />
      ))}
    </ul>
  )
}
```

### Empty State Component

```typescript
// src/app/account/donations/_components/EmptyDonationState.tsx

import Link from 'next/link'

export function EmptyDonationState() {
  return (
    <div className="flex flex-col items-center gap-4 py-16 text-center">
      <span className="text-5xl" aria-hidden="true">🐾</span>
      <p className="text-[var(--text-secondary)]">
        Todavía no has realizado ninguna donación.
      </p>
      <Link
        href="/donate"
        className="rounded-md bg-[var(--brand-primary)] px-4 py-2 text-sm font-medium text-white hover:bg-[var(--brand-primary-hover)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-[var(--brand-primary)]"
      >
        Hacer una donación
      </Link>
    </div>
  )
}
```

### Loading Skeleton (`loading.tsx`)

Next.js automatically uses `loading.tsx` as the Suspense fallback for the route segment:

```typescript
// src/app/account/donations/loading.tsx

export default function DonationHistoryLoading() {
  return (
    <main className="max-w-3xl mx-auto px-4 py-8">
      <div className="h-8 w-40 rounded bg-[var(--bg-skeleton)] animate-pulse mb-6" />
      <ul className="rounded-lg border border-[var(--border-default)] bg-[var(--bg-card)] px-4">
        {Array.from({ length: 5 }).map((_, i) => (
          <li
            key={i}
            className="flex items-center justify-between gap-4 py-4 border-b border-[var(--border-muted)] last:border-0"
          >
            <div className="flex flex-col gap-2">
              <div className="h-4 w-32 rounded bg-[var(--bg-skeleton)] animate-pulse" />
              <div className="h-3 w-20 rounded bg-[var(--bg-skeleton)] animate-pulse" />
            </div>
            <div className="flex flex-col items-end gap-2">
              <div className="h-5 w-16 rounded bg-[var(--bg-skeleton)] animate-pulse" />
              <div className="h-4 w-20 rounded-full bg-[var(--bg-skeleton)] animate-pulse" />
            </div>
          </li>
        ))}
      </ul>
    </main>
  )
}
```

### RLS — Supabase Row-Level Security

The three payment tables must have RLS policies allowing donors to read only their own rows. If not already set, apply via migration:

```sql
-- migrations/YYYYMMDDHHMMSS_donation_rls_policies.sql

-- donations (Stripe)
alter table donations enable row level security;

create policy "donors can view own stripe donations"
  on donations for select
  using (
    donor_user_id = auth.uid()
    or exists (
      select 1 from profiles
      where profiles.user_id = auth.uid()
        and profiles.role in ('staff', 'admin')
    )
  );

-- bank_transfer_donations (SEPA)
alter table bank_transfer_donations enable row level security;

create policy "donors can view own sepa donations"
  on bank_transfer_donations for select
  using (
    donor_user_id = auth.uid()
    or exists (
      select 1 from profiles
      where profiles.user_id = auth.uid()
        and profiles.role in ('staff', 'admin')
    )
  );

-- tigo_money_donations
alter table tigo_money_donations enable row level security;

create policy "donors can view own tigo donations"
  on tigo_money_donations for select
  using (
    donor_user_id = auth.uid()
    or exists (
      select 1 from profiles
      where profiles.user_id = auth.uid()
        and profiles.role in ('staff', 'admin')
    )
  );
```

Note: `donor_user_id` is nullable (anonymous donations). The policy correctly handles this — `null = auth.uid()` evaluates to `null` (falsy), so anonymous donations are never exposed to donors. Staff/admin can see all records via the `profiles.role` check.

### Anonymous Donation Handling

Donors who gave anonymously (no account) won't see those records if they later create an account. This is intentional — anonymous donations are not linkable after the fact. If the product wants to support claiming anonymous donations, that is a separate feature (out of scope for this task).

### Required CSS Variables

These variables must be defined in `src/app/globals.css` (or equivalent theme file):

```css
:root {
  /* Status badge backgrounds */
  --status-success-bg: #dcfce7;
  --status-success-text: #166534;
  --status-warning-bg: #fef9c3;
  --status-warning-text: #713f12;
  --status-error-bg: #fee2e2;
  --status-error-text: #991b1b;
  --status-neutral-bg: #f3f4f6;
  --status-neutral-text: #374151;

  /* Skeleton animation */
  --bg-skeleton: #e5e7eb;
}
```

### Unit Tests

```typescript
// tests/unit/lib/format-donation-amount.test.ts
import { formatDonationAmount } from '@/lib/format-donation-amount'

describe('formatDonationAmount', () => {
  it('formats EUR cents with 2 decimal places and € symbol', () => {
    expect(formatDonationAmount(5000, 'eur')).toBe('€50.00')
    expect(formatDonationAmount(999, 'eur')).toBe('€9.99')
    expect(formatDonationAmount(100000, 'eur')).toBe('€1000.00')
  })

  it('formats PYG as whole integer with ₲ symbol and no decimal places', () => {
    expect(formatDonationAmount(50000, 'pyg')).toContain('₲')
    expect(formatDonationAmount(50000, 'pyg')).toContain('50')
    // PYG is NOT divided by 100
    expect(formatDonationAmount(50000, 'pyg')).not.toContain('500')
  })

  it('does NOT divide PYG amount by 100', () => {
    // ₲50,000 stays as 50,000 — not converted to 500.00
    const result = formatDonationAmount(50000, 'pyg')
    expect(result).not.toBe('₲500.00')
    expect(result).not.toBe('€500.00')
  })
})
```

```typescript
// tests/unit/components/DonationStatusBadge.test.tsx
import { render, screen } from '@testing-library/react'
import { DonationStatusBadge } from '@/app/account/donations/_components/DonationStatusBadge'

describe('DonationStatusBadge', () => {
  it('renders Stripe succeeded as Completado', () => {
    render(<DonationStatusBadge method="stripe" status="succeeded" />)
    expect(screen.getByText('Completado')).toBeInTheDocument()
  })

  it('renders Tigo Money approved as Aprobado', () => {
    render(<DonationStatusBadge method="tigo_money" status="approved" />)
    expect(screen.getByText('Aprobado')).toBeInTheDocument()
  })

  it('renders SEPA pending_bank_transfer with warning styling', () => {
    render(<DonationStatusBadge method="sepa" status="pending_bank_transfer" />)
    const badge = screen.getByRole('generic', { name: /estado/i })
    expect(badge).toHaveClass('bg-[var(--status-warning-bg)]')
  })

  it('falls back to Desconocido for unknown status', () => {
    render(<DonationStatusBadge method="stripe" status="unknown_status" />)
    expect(screen.getByText('Desconocido')).toBeInTheDocument()
  })
})
```

## Related Issues

- EPIC-3
- S04
- T01-integrate-tigo-money-api (normalizeParaguayPhone, tigo_money_donations schema)
- T02-implement-local-payment-flow (tigo_money_donations insert pattern)
- S01/T02 (donations table schema — Stripe)
- S02 (bank_transfer_donations table schema — SEPA)
