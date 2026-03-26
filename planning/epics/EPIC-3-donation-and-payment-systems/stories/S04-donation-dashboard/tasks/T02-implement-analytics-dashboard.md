---
task: T02
story: S04
epic: EPIC-3
title: Implement analytics dashboard
status: ready
priority: medium
created: 2026-03-25T17:13:26.729742
---

# T02: Implement analytics dashboard

## Description

Build a staff/admin-only analytics dashboard at `/admin/donations/analytics` that aggregates donation data across all three payment methods (Stripe, SEPA, Tigo Money) and presents totals broken down by currency (EUR / PYG), payment method, time period (current month, last 30 days, last 12 months, all time), and campaign. All aggregations run as Supabase queries (no client-side math on large datasets). The page is a Server Component; filter controls are Client Components that trigger server re-renders via URL search params.

## Acceptance Criteria

- [ ] Page at `/admin/donations/analytics` requires `role = 'admin' OR role = 'staff'` — unauthorized users redirected to `/`
- [ ] Total donations and total amount displayed per payment method
- [ ] Totals broken down by currency (EUR shown as `€X.XX`, PYG shown as `₲X,XXX`)
- [ ] Period selector (current month / last 30 days / last 12 months / all time) updates displayed totals
- [ ] Campaign breakdown table shows per-campaign totals
- [ ] "Success rate" metric per payment method (approved/completed ÷ total)
- [ ] All amounts computed server-side — no large dataset sent to the client
- [ ] Loading skeleton during data fetch
- [ ] No hardcoded colors — CSS vars only

## Implementation Notes

### Route and File Structure

```
src/app/admin/donations/analytics/
  page.tsx                           ← Server Component (reads searchParams, fetches data)
  loading.tsx                        ← Skeleton
  _components/
    PeriodSelector.tsx               ← Client Component — updates URL param ?period=
    SummaryCards.tsx                 ← Server Component — totals grid
    MethodBreakdownTable.tsx         ← Per-method: count, total, success rate
    CampaignBreakdownTable.tsx       ← Per-campaign totals
    CurrencySummary.tsx              ← EUR vs PYG totals side by side
```

### Auth Guard — Staff/Admin Only

```typescript
// src/app/admin/donations/analytics/page.tsx
import { createClient } from '@/lib/supabase/server'
import { redirect } from 'next/navigation'

export default async function DonationAnalyticsPage({
  searchParams,
}: {
  searchParams: { period?: string }
}) {
  const supabase = createClient()

  const { data: { user } } = await supabase.auth.getUser()
  if (!user) redirect('/auth/login?next=/admin/donations/analytics')

  const { data: profile } = await supabase
    .from('profiles')
    .select('role')
    .eq('user_id', user.id)
    .single()

  if (!profile || !['staff', 'admin'].includes(profile.role)) {
    redirect('/')
  }

  const period = parsePeriod(searchParams.period ?? 'current_month')
  // ... fetch analytics data, render page
}
```

### Period Parsing

```typescript
// src/lib/analytics-period.ts

export type AnalyticsPeriod = 'current_month' | 'last_30_days' | 'last_12_months' | 'all_time'

export interface DateRange {
  from: string | null  // ISO 8601, null = no lower bound
  to: string | null    // ISO 8601, null = no upper bound (now)
}

export function parsePeriod(raw: string): AnalyticsPeriod {
  const valid: AnalyticsPeriod[] = ['current_month', 'last_30_days', 'last_12_months', 'all_time']
  return valid.includes(raw as AnalyticsPeriod) ? (raw as AnalyticsPeriod) : 'current_month'
}

export function periodToDateRange(period: AnalyticsPeriod): DateRange {
  const now = new Date()

  switch (period) {
    case 'current_month': {
      const from = new Date(now.getFullYear(), now.getMonth(), 1)
      return { from: from.toISOString(), to: null }
    }
    case 'last_30_days': {
      const from = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000)
      return { from: from.toISOString(), to: null }
    }
    case 'last_12_months': {
      const from = new Date(now.getFullYear() - 1, now.getMonth(), 1)
      return { from: from.toISOString(), to: null }
    }
    case 'all_time':
      return { from: null, to: null }
  }
}
```

### Aggregation Strategy

Run server-side aggregation with Supabase RPC (PostgreSQL functions) rather than fetching all rows and summing in TypeScript. This is critical for large datasets.

#### PostgreSQL Aggregation Function

Create via migration:

```sql
-- migrations/YYYYMMDDHHMMSS_donation_analytics_fn.sql

create or replace function get_donation_analytics(
  p_from timestamptz default null,
  p_to   timestamptz default now()
)
returns json
language sql
stable
security definer
as $$
  select json_build_object(
    'stripe', (
      select json_build_object(
        'total_count',     count(*),
        'total_eur_cents', coalesce(sum(case when currency = 'eur' then amount_cents else 0 end), 0),
        'success_count',   count(*) filter (where status = 'succeeded'),
        'by_campaign',     (
          select json_agg(row_to_json(r))
          from (
            select
              coalesce(campaign_name, 'Sin campaña') as campaign,
              count(*) as count,
              sum(amount_cents) as total_cents,
              currency
            from donations d2
            where d2.created_at >= coalesce(p_from, '-infinity'::timestamptz)
              and d2.created_at <= p_to
            group by campaign_name, currency
          ) r
        )
      )
      from donations
      where created_at >= coalesce(p_from, '-infinity'::timestamptz)
        and created_at <= p_to
    ),
    'sepa', (
      select json_build_object(
        'total_count',     count(*),
        'total_eur_cents', coalesce(sum(case when currency = 'eur' then amount_cents else 0 end), 0),
        'success_count',   count(*) filter (where status in ('confirmed', 'transfer_received')),
        'by_campaign',     (
          select json_agg(row_to_json(r))
          from (
            select
              coalesce(campaign_name, 'Sin campaña') as campaign,
              count(*) as count,
              sum(amount_cents) as total_cents,
              currency
            from bank_transfer_donations d2
            where d2.created_at >= coalesce(p_from, '-infinity'::timestamptz)
              and d2.created_at <= p_to
            group by campaign_name, currency
          ) r
        )
      )
      from bank_transfer_donations
      where created_at >= coalesce(p_from, '-infinity'::timestamptz)
        and created_at <= p_to
    ),
    'tigo_money', (
      select json_build_object(
        'total_count',     count(*),
        'total_pyg',       coalesce(sum(case when currency = 'pyg' then amount else 0 end), 0),
        'success_count',   count(*) filter (where status = 'approved'),
        'by_campaign',     (
          select json_agg(row_to_json(r))
          from (
            select
              coalesce(campaign_name, 'Sin campaña') as campaign,
              count(*) as count,
              sum(amount) as total_pyg,
              currency
            from tigo_money_donations d2
            where d2.created_at >= coalesce(p_from, '-infinity'::timestamptz)
              and d2.created_at <= p_to
            group by campaign_name, currency
          ) r
        )
      )
      from tigo_money_donations
      where created_at >= coalesce(p_from, '-infinity'::timestamptz)
        and created_at <= p_to
    )
  );
$$;

-- Grant to authenticated users — RLS on the underlying tables still applies
-- But because this is security definer it bypasses RLS.
-- Only grant to staff/admin roles (enforced at the application layer before calling this).
grant execute on function get_donation_analytics(timestamptz, timestamptz) to authenticated;
```

#### Calling the RPC from the Server Component

```typescript
// In page.tsx, after auth guard:

const { from, to } = periodToDateRange(period)

const { data: analytics, error } = await supabase.rpc('get_donation_analytics', {
  p_from: from,
  p_to: to ?? new Date().toISOString(),
})

if (error) {
  // Log server-side, show safe fallback to user
  console.error('[DonationAnalytics] RPC error:', error.message)
  // render error state
}
```

### TypeScript Types for Analytics Result

```typescript
// src/types/donation-analytics.ts

export interface CampaignBreakdown {
  campaign: string
  count: number
  total_cents?: number   // EUR methods
  total_pyg?: number     // Tigo Money
  currency: string
}

export interface MethodAnalytics {
  total_count: number
  success_count: number
  total_eur_cents?: number   // Stripe, SEPA
  total_pyg?: number         // Tigo Money
  by_campaign: CampaignBreakdown[] | null
}

export interface DonationAnalytics {
  stripe: MethodAnalytics
  sepa: MethodAnalytics
  tigo_money: MethodAnalytics
}
```

### Summary Cards Component

Shows four top-level numbers: total EUR raised, total PYG raised, total donations, overall success rate.

```typescript
// src/app/admin/donations/analytics/_components/SummaryCards.tsx

import type { DonationAnalytics } from '@/types/donation-analytics'
import { formatDonationAmount } from '@/lib/format-donation-amount'

interface Props {
  analytics: DonationAnalytics
}

export function SummaryCards({ analytics }: Props) {
  const totalEurCents =
    (analytics.stripe.total_eur_cents ?? 0) +
    (analytics.sepa.total_eur_cents ?? 0)

  const totalPyg = analytics.tigo_money.total_pyg ?? 0

  const totalCount =
    analytics.stripe.total_count +
    analytics.sepa.total_count +
    analytics.tigo_money.total_count

  const totalSuccess =
    analytics.stripe.success_count +
    analytics.sepa.success_count +
    analytics.tigo_money.success_count

  const successRate = totalCount > 0
    ? Math.round((totalSuccess / totalCount) * 100)
    : 0

  const cards = [
    { label: 'Total recaudado (EUR)', value: formatDonationAmount(totalEurCents, 'eur') },
    { label: 'Total recaudado (PYG)', value: formatDonationAmount(totalPyg, 'pyg') },
    { label: 'Donaciones totales',    value: totalCount.toString() },
    { label: 'Tasa de éxito',         value: `${successRate}%` },
  ]

  return (
    <dl className="grid grid-cols-2 gap-4 sm:grid-cols-4">
      {cards.map(card => (
        <div
          key={card.label}
          className="rounded-lg border border-[var(--border-default)] bg-[var(--bg-card)] p-4"
        >
          <dt className="text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wide">
            {card.label}
          </dt>
          <dd className="mt-1 text-2xl font-semibold text-[var(--text-primary)]">
            {card.value}
          </dd>
        </div>
      ))}
    </dl>
  )
}
```

### Method Breakdown Table

```typescript
// src/app/admin/donations/analytics/_components/MethodBreakdownTable.tsx

import type { DonationAnalytics } from '@/types/donation-analytics'
import { formatDonationAmount } from '@/lib/format-donation-amount'

interface Props {
  analytics: DonationAnalytics
}

interface MethodRow {
  method: string
  count: number
  total: string
  successRate: string
}

export function MethodBreakdownTable({ analytics }: Props) {
  const rows: MethodRow[] = [
    {
      method: 'Stripe (tarjeta)',
      count: analytics.stripe.total_count,
      total: formatDonationAmount(analytics.stripe.total_eur_cents ?? 0, 'eur'),
      successRate: rateLabel(analytics.stripe.success_count, analytics.stripe.total_count),
    },
    {
      method: 'Transferencia SEPA',
      count: analytics.sepa.total_count,
      total: formatDonationAmount(analytics.sepa.total_eur_cents ?? 0, 'eur'),
      successRate: rateLabel(analytics.sepa.success_count, analytics.sepa.total_count),
    },
    {
      method: 'Tigo Money',
      count: analytics.tigo_money.total_count,
      total: formatDonationAmount(analytics.tigo_money.total_pyg ?? 0, 'pyg'),
      successRate: rateLabel(analytics.tigo_money.success_count, analytics.tigo_money.total_count),
    },
  ]

  return (
    <section aria-labelledby="method-breakdown-heading">
      <h2
        id="method-breakdown-heading"
        className="text-base font-semibold text-[var(--text-primary)] mb-3"
      >
        Por método de pago
      </h2>
      <div className="overflow-x-auto rounded-lg border border-[var(--border-default)]">
        <table className="min-w-full divide-y divide-[var(--border-muted)]">
          <thead className="bg-[var(--bg-table-header)]">
            <tr>
              {['Método', 'Donaciones', 'Total', 'Tasa de éxito'].map(h => (
                <th
                  key={h}
                  scope="col"
                  className="px-4 py-3 text-left text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider"
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-[var(--border-muted)] bg-[var(--bg-card)]">
            {rows.map(row => (
              <tr key={row.method}>
                <td className="px-4 py-3 text-sm text-[var(--text-primary)] font-medium">{row.method}</td>
                <td className="px-4 py-3 text-sm text-[var(--text-secondary)] tabular-nums">{row.count}</td>
                <td className="px-4 py-3 text-sm text-[var(--text-primary)] font-mono tabular-nums">{row.total}</td>
                <td className="px-4 py-3 text-sm text-[var(--text-secondary)] tabular-nums">{row.successRate}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}

function rateLabel(success: number, total: number): string {
  if (total === 0) return '—'
  return `${Math.round((success / total) * 100)}%`
}
```

### Campaign Breakdown Table

Merges campaign data from all three methods into a unified per-campaign view. Since EUR and PYG can't be summed, campaigns are grouped by currency:

```typescript
// src/app/admin/donations/analytics/_components/CampaignBreakdownTable.tsx

import type { DonationAnalytics, CampaignBreakdown } from '@/types/donation-analytics'
import { formatDonationAmount } from '@/lib/format-donation-amount'

interface Props {
  analytics: DonationAnalytics
}

interface MergedCampaignRow {
  campaign: string
  eurCents: number
  pyg: number
  count: number
}

export function CampaignBreakdownTable({ analytics }: Props) {
  // Merge all campaigns from all methods into a single map keyed by campaign name
  const campaignMap = new Map<string, MergedCampaignRow>()

  function mergeCampaigns(campaigns: CampaignBreakdown[] | null, isEur: boolean) {
    if (!campaigns) return
    for (const c of campaigns) {
      const existing = campaignMap.get(c.campaign) ?? {
        campaign: c.campaign,
        eurCents: 0,
        pyg: 0,
        count: 0,
      }
      existing.count += c.count
      if (isEur) {
        existing.eurCents += c.total_cents ?? 0
      } else {
        existing.pyg += c.total_pyg ?? 0
      }
      campaignMap.set(c.campaign, existing)
    }
  }

  mergeCampaigns(analytics.stripe.by_campaign, true)
  mergeCampaigns(analytics.sepa.by_campaign, true)
  mergeCampaigns(analytics.tigo_money.by_campaign, false)

  const rows = Array.from(campaignMap.values())
    .sort((a, b) => b.count - a.count)

  if (rows.length === 0) {
    return (
      <p className="text-sm text-[var(--text-secondary)]">
        Sin datos de campaña para el período seleccionado.
      </p>
    )
  }

  return (
    <section aria-labelledby="campaign-breakdown-heading">
      <h2
        id="campaign-breakdown-heading"
        className="text-base font-semibold text-[var(--text-primary)] mb-3"
      >
        Por campaña
      </h2>
      <div className="overflow-x-auto rounded-lg border border-[var(--border-default)]">
        <table className="min-w-full divide-y divide-[var(--border-muted)]">
          <thead className="bg-[var(--bg-table-header)]">
            <tr>
              {['Campaña', 'Donaciones', 'Total EUR', 'Total PYG'].map(h => (
                <th
                  key={h}
                  scope="col"
                  className="px-4 py-3 text-left text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider"
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-[var(--border-muted)] bg-[var(--bg-card)]">
            {rows.map(row => (
              <tr key={row.campaign}>
                <td className="px-4 py-3 text-sm text-[var(--text-primary)] font-medium">{row.campaign}</td>
                <td className="px-4 py-3 text-sm text-[var(--text-secondary)] tabular-nums">{row.count}</td>
                <td className="px-4 py-3 text-sm text-[var(--text-primary)] font-mono tabular-nums">
                  {row.eurCents > 0 ? formatDonationAmount(row.eurCents, 'eur') : '—'}
                </td>
                <td className="px-4 py-3 text-sm text-[var(--text-primary)] font-mono tabular-nums">
                  {row.pyg > 0 ? formatDonationAmount(row.pyg, 'pyg') : '—'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}
```

### Period Selector — Client Component with URL State

The period selector updates the URL search param `?period=` without a full page reload. The Server Component re-runs on navigation, picking up the new value from `searchParams`.

```typescript
// src/app/admin/donations/analytics/_components/PeriodSelector.tsx
'use client'

import { useRouter, usePathname, useSearchParams } from 'next/navigation'
import type { AnalyticsPeriod } from '@/lib/analytics-period'

const PERIOD_OPTIONS: { value: AnalyticsPeriod; label: string }[] = [
  { value: 'current_month',  label: 'Este mes' },
  { value: 'last_30_days',   label: 'Últimos 30 días' },
  { value: 'last_12_months', label: 'Últimos 12 meses' },
  { value: 'all_time',       label: 'Todo el tiempo' },
]

interface Props {
  currentPeriod: AnalyticsPeriod
}

export function PeriodSelector({ currentPeriod }: Props) {
  const router = useRouter()
  const pathname = usePathname()
  const searchParams = useSearchParams()

  function handleChange(value: string) {
    const params = new URLSearchParams(searchParams.toString())
    params.set('period', value)
    router.push(`${pathname}?${params.toString()}`)
  }

  return (
    <div className="flex items-center gap-2">
      <label
        htmlFor="period-select"
        className="text-sm text-[var(--text-secondary)] shrink-0"
      >
        Período:
      </label>
      <select
        id="period-select"
        value={currentPeriod}
        onChange={e => handleChange(e.target.value)}
        className="rounded-md border border-[var(--border-default)] bg-[var(--bg-input)] px-3 py-1.5 text-sm text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--brand-primary)]"
      >
        {PERIOD_OPTIONS.map(opt => (
          <option key={opt.value} value={opt.value}>{opt.label}</option>
        ))}
      </select>
    </div>
  )
}
```

### Full Page Assembly

```typescript
// src/app/admin/donations/analytics/page.tsx (complete)

import { createClient } from '@/lib/supabase/server'
import { redirect } from 'next/navigation'
import { parsePeriod, periodToDateRange } from '@/lib/analytics-period'
import { SummaryCards } from './_components/SummaryCards'
import { MethodBreakdownTable } from './_components/MethodBreakdownTable'
import { CampaignBreakdownTable } from './_components/CampaignBreakdownTable'
import { PeriodSelector } from './_components/PeriodSelector'
import type { DonationAnalytics } from '@/types/donation-analytics'

export default async function DonationAnalyticsPage({
  searchParams,
}: {
  searchParams: { period?: string }
}) {
  const supabase = createClient()

  const { data: { user } } = await supabase.auth.getUser()
  if (!user) redirect('/auth/login?next=/admin/donations/analytics')

  const { data: profile } = await supabase
    .from('profiles')
    .select('role')
    .eq('user_id', user.id)
    .single()

  if (!profile || !['staff', 'admin'].includes(profile.role)) {
    redirect('/')
  }

  const period = parsePeriod(searchParams.period ?? 'current_month')
  const { from, to } = periodToDateRange(period)

  const { data: analytics, error } = await supabase.rpc('get_donation_analytics', {
    p_from: from,
    p_to: to ?? new Date().toISOString(),
  })

  if (error || !analytics) {
    return (
      <main className="max-w-5xl mx-auto px-4 py-8">
        <p className="text-[var(--status-error-text)]">
          Error al cargar los datos. Intente de nuevo.
        </p>
      </main>
    )
  }

  const typedAnalytics = analytics as DonationAnalytics

  return (
    <main className="max-w-5xl mx-auto px-4 py-8 space-y-8">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <h1 className="text-2xl font-semibold text-[var(--text-primary)]">
          Analíticas de Donaciones
        </h1>
        <PeriodSelector currentPeriod={period} />
      </div>

      <SummaryCards analytics={typedAnalytics} />

      <MethodBreakdownTable analytics={typedAnalytics} />

      <CampaignBreakdownTable analytics={typedAnalytics} />
    </main>
  )
}
```

### Loading Skeleton (`loading.tsx`)

```typescript
// src/app/admin/donations/analytics/loading.tsx

export default function AnalyticsLoading() {
  return (
    <main className="max-w-5xl mx-auto px-4 py-8 space-y-8">
      <div className="flex justify-between items-center">
        <div className="h-8 w-56 rounded bg-[var(--bg-skeleton)] animate-pulse" />
        <div className="h-8 w-40 rounded bg-[var(--bg-skeleton)] animate-pulse" />
      </div>

      {/* Summary cards skeleton */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="rounded-lg border border-[var(--border-default)] bg-[var(--bg-card)] p-4 space-y-2">
            <div className="h-3 w-24 rounded bg-[var(--bg-skeleton)] animate-pulse" />
            <div className="h-7 w-20 rounded bg-[var(--bg-skeleton)] animate-pulse" />
          </div>
        ))}
      </div>

      {/* Table skeleton */}
      <div className="rounded-lg border border-[var(--border-default)] overflow-hidden">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="flex gap-8 px-4 py-3 border-b border-[var(--border-muted)] last:border-0">
            <div className="h-4 w-32 rounded bg-[var(--bg-skeleton)] animate-pulse" />
            <div className="h-4 w-12 rounded bg-[var(--bg-skeleton)] animate-pulse" />
            <div className="h-4 w-20 rounded bg-[var(--bg-skeleton)] animate-pulse" />
            <div className="h-4 w-12 rounded bg-[var(--bg-skeleton)] animate-pulse" />
          </div>
        ))}
      </div>
    </main>
  )
}
```

### Required CSS Variables

Ensure these are defined in addition to the status vars from T01:

```css
:root {
  --bg-table-header: #f9fafb;
  --bg-input: #ffffff;
}
```

### Key Implementation Notes

**EUR and PYG are never mixed:** Summary cards show EUR total and PYG total as two separate figures. There is no conversion rate — the shelter deals with both currencies independently. Do not add any EUR↔PYG conversion logic.

**`security definer` function:** The `get_donation_analytics` RPC uses `security definer` to read across all donation tables without RLS interference. This is intentional — the auth guard in the page.tsx ensures only staff/admin can invoke it. If the function must be callable by non-staff (it shouldn't be), remove `security definer` and ensure tables have appropriate `select` policies for the `authenticated` role.

**searchParams in Next.js 14:** `searchParams` is available as a prop on page.tsx Server Components (App Router). It does not require `useSearchParams()` — that hook is only needed in Client Components.

**PeriodSelector wraps `useSearchParams`:** Since `useSearchParams()` requires a Client Component, `PeriodSelector` is `'use client'`. It uses `router.push` (soft navigation) so the server component re-executes with the new `searchParams` without a full HTML reload.

### Unit Tests

```typescript
// tests/unit/lib/analytics-period.test.ts
import { parsePeriod, periodToDateRange } from '@/lib/analytics-period'

describe('parsePeriod', () => {
  it('returns the value unchanged for valid periods', () => {
    expect(parsePeriod('current_month')).toBe('current_month')
    expect(parsePeriod('all_time')).toBe('all_time')
  })

  it('falls back to current_month for invalid input', () => {
    expect(parsePeriod('invalid')).toBe('current_month')
    expect(parsePeriod('')).toBe('current_month')
  })
})

describe('periodToDateRange', () => {
  it('returns null to for all_time', () => {
    const { from, to } = periodToDateRange('all_time')
    expect(from).toBeNull()
    expect(to).toBeNull()
  })

  it('returns a from date 30 days ago for last_30_days', () => {
    const { from } = periodToDateRange('last_30_days')
    const fromDate = new Date(from!)
    const diffMs = Date.now() - fromDate.getTime()
    const diffDays = diffMs / (1000 * 60 * 60 * 24)
    expect(diffDays).toBeCloseTo(30, 0)
  })
})
```

```typescript
// tests/unit/components/SummaryCards.test.tsx
import { render, screen } from '@testing-library/react'
import { SummaryCards } from '@/app/admin/donations/analytics/_components/SummaryCards'
import type { DonationAnalytics } from '@/types/donation-analytics'

const mockAnalytics: DonationAnalytics = {
  stripe:     { total_count: 10, success_count: 9, total_eur_cents: 50000, by_campaign: null },
  sepa:       { total_count: 5,  success_count: 4, total_eur_cents: 30000, by_campaign: null },
  tigo_money: { total_count: 8,  success_count: 7, total_pyg: 500000,      by_campaign: null },
}

describe('SummaryCards', () => {
  it('shows combined EUR total from Stripe and SEPA', () => {
    render(<SummaryCards analytics={mockAnalytics} />)
    // €800.00 = (50000 + 30000) / 100
    expect(screen.getByText('€800.00')).toBeInTheDocument()
  })

  it('shows PYG total from Tigo Money', () => {
    render(<SummaryCards analytics={mockAnalytics} />)
    // ₲500,000 (no division)
    expect(screen.getByText(/₲/)).toBeInTheDocument()
  })

  it('shows total donation count across all methods', () => {
    render(<SummaryCards analytics={mockAnalytics} />)
    expect(screen.getByText('23')).toBeInTheDocument()  // 10+5+8
  })

  it('shows success rate as percentage', () => {
    render(<SummaryCards analytics={mockAnalytics} />)
    // (9+4+7)/23 = 87%
    expect(screen.getByText('87%')).toBeInTheDocument()
  })
})
```

## Related Issues

- EPIC-3
- S04
- T01-create-donation-history-view (shares formatDonationAmount, UnifiedDonation types)
- S01/T01 (donations table schema)
- S02/T01 (bank_transfer_donations schema)
- S03/T01 (tigo_money_donations schema)
