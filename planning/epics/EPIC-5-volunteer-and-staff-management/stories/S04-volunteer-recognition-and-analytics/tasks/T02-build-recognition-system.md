---
task: T02
story: S04
epic: EPIC-5
title: Build recognition system
status: ready
priority: medium
created: 2026-03-25T17:13:26.732248
---

# T02: Build recognition system

## Description

Award milestone badges to volunteers automatically when they cross hour thresholds, and display a recognition board that admins can use to acknowledge individual volunteers. Badges are computed from `volunteer_profiles.hours_total` and stored as a separate `volunteer_badges` table for history.

## Acceptance Criteria

- [ ] Milestone badges are awarded automatically when `hours_total` crosses defined thresholds
- [ ] Badge award is idempotent — re-running never creates duplicate badges
- [ ] Admin can manually award a "Special Recognition" badge with a custom note
- [ ] Recognition board at `/admin/volunteers/recognition` lists all badge awards
- [ ] Volunteer can see their own badges on their dashboard
- [ ] Badge award logic is unit-tested (milestone thresholds + deduplication)
- [ ] All data served via Server Components

## Implementation Notes

### Tech Stack Constraints

- **Supabase only** — No Prisma, no ORM.
- **Next.js 14 App Router** — Server Components; Server Actions for mutations.
- **Tailwind CSS 3.4.19 pinned** — CSS vars only.
- `supabaseAdmin` for badge writes; RLS for volunteer self-reads.
- Badge award triggered from the `sync_volunteer_hours_total` trigger (or a dedicated Server Action for manual awards).

---

### Step 1 — Database migration

**File**: `supabase/migrations/20260401000016_volunteer_badges.sql`

```sql
-- Badge type enum
create type public.badge_type as enum (
  'hours_10',
  'hours_50',
  'hours_100',
  'hours_250',
  'hours_500',
  'special'
);

-- Badge award records
create table public.volunteer_badges (
  id           uuid         primary key default gen_random_uuid(),
  volunteer_id uuid         not null references auth.users(id) on delete cascade,
  badge        public.badge_type not null,
  awarded_at   timestamptz  not null default now(),
  note         text,                          -- optional admin note (special badge)
  awarded_by   uuid         references auth.users(id),  -- null for auto-awarded
  unique (volunteer_id, badge)               -- idempotent: one of each badge per volunteer
);

-- Index for volunteer lookup
create index volunteer_badges_volunteer_id_idx
  on public.volunteer_badges (volunteer_id, awarded_at desc);

-- RLS
alter table public.volunteer_badges enable row level security;

-- Volunteers see their own badges
create policy "Volunteers can read own badges"
  on public.volunteer_badges for select
  to authenticated
  using (volunteer_id = auth.uid());

-- Extend the hours sync trigger to also award milestone badges
create or replace function public.sync_volunteer_hours_total()
returns trigger
language plpgsql
security definer
as $$
declare
  v_id   uuid;
  v_total numeric;
begin
  v_id := coalesce(new.volunteer_id, old.volunteer_id);

  -- Recompute total
  select coalesce(sum(hours), 0)
  into v_total
  from public.volunteer_hours
  where volunteer_id = v_id;

  -- Update denormalized total
  update public.volunteer_profiles
  set hours_total = v_total
  where id = v_id;

  -- Award milestone badges (ON CONFLICT DO NOTHING = idempotent)
  if v_total >= 10 then
    insert into public.volunteer_badges (volunteer_id, badge)
    values (v_id, 'hours_10')
    on conflict (volunteer_id, badge) do nothing;
  end if;

  if v_total >= 50 then
    insert into public.volunteer_badges (volunteer_id, badge)
    values (v_id, 'hours_50')
    on conflict (volunteer_id, badge) do nothing;
  end if;

  if v_total >= 100 then
    insert into public.volunteer_badges (volunteer_id, badge)
    values (v_id, 'hours_100')
    on conflict (volunteer_id, badge) do nothing;
  end if;

  if v_total >= 250 then
    insert into public.volunteer_badges (volunteer_id, badge)
    values (v_id, 'hours_250')
    on conflict (volunteer_id, badge) do nothing;
  end if;

  if v_total >= 500 then
    insert into public.volunteer_badges (volunteer_id, badge)
    values (v_id, 'hours_500')
    on conflict (volunteer_id, badge) do nothing;
  end if;

  return coalesce(new, old);
end;
$$;
```

> Note: This migration replaces the trigger function defined in `000015`. The `create or replace` ensures the extended function takes effect without re-creating the trigger binding.

---

### Step 2 — Badge constants and label helpers

**File**: `src/lib/badges/badge-config.ts`

```typescript
export type BadgeType =
  | 'hours_10'
  | 'hours_50'
  | 'hours_100'
  | 'hours_250'
  | 'hours_500'
  | 'special'

export interface BadgeConfig {
  label: string
  description: string
  icon: string       // emoji — simple, no external assets
  threshold?: number // undefined for 'special'
}

export const BADGE_CONFIG: Record<BadgeType, BadgeConfig> = {
  hours_10: {
    label: '10 horas',
    description: '¡Completaste tus primeras 10 horas!',
    icon: '🌱',
    threshold: 10,
  },
  hours_50: {
    label: '50 horas',
    description: 'Voluntario dedicado — 50 horas contribuidas',
    icon: '⭐',
    threshold: 50,
  },
  hours_100: {
    label: '100 horas',
    description: '¡Cien horas al servicio de los animales!',
    icon: '🏅',
    threshold: 100,
  },
  hours_250: {
    label: '250 horas',
    description: 'Voluntario experto — 250 horas',
    icon: '🥈',
    threshold: 250,
  },
  hours_500: {
    label: '500 horas',
    description: '¡Leyenda del refugio — 500 horas!',
    icon: '🏆',
    threshold: 500,
  },
  special: {
    label: 'Reconocimiento especial',
    description: 'Reconocimiento otorgado por el equipo del refugio',
    icon: '🎖️',
    threshold: undefined,
  },
}

export function getBadgeLabel(badge: BadgeType): string {
  return BADGE_CONFIG[badge]?.label ?? badge
}

export function getBadgeIcon(badge: BadgeType): string {
  return BADGE_CONFIG[badge]?.icon ?? '🎗️'
}

/**
 * Returns which milestone badges should be active for a given hours_total.
 * Used for unit tests and for checking eligibility without a DB round-trip.
 */
export function computeEarnedMilestoneBadges(hoursTotal: number): BadgeType[] {
  return (Object.entries(BADGE_CONFIG) as [BadgeType, BadgeConfig][])
    .filter(([, cfg]) => cfg.threshold !== undefined && hoursTotal >= cfg.threshold!)
    .map(([badge]) => badge)
}
```

---

### Step 3 — Unit tests

**File**: `src/lib/badges/__tests__/badge-config.test.ts`

```typescript
import { describe, it, expect } from 'vitest'
import { computeEarnedMilestoneBadges } from '../badge-config'

describe('computeEarnedMilestoneBadges', () => {
  it('returns empty array for 0 hours', () => {
    expect(computeEarnedMilestoneBadges(0)).toHaveLength(0)
  })

  it('returns hours_10 badge at exactly 10 hours', () => {
    const badges = computeEarnedMilestoneBadges(10)
    expect(badges).toContain('hours_10')
    expect(badges).not.toContain('hours_50')
  })

  it('returns hours_10 badge for any hours >= 10', () => {
    expect(computeEarnedMilestoneBadges(15)).toContain('hours_10')
  })

  it('returns hours_10 and hours_50 at 50 hours', () => {
    const badges = computeEarnedMilestoneBadges(50)
    expect(badges).toContain('hours_10')
    expect(badges).toContain('hours_50')
    expect(badges).not.toContain('hours_100')
  })

  it('returns all 5 milestone badges at 500 hours', () => {
    const badges = computeEarnedMilestoneBadges(500)
    expect(badges).toContain('hours_10')
    expect(badges).toContain('hours_50')
    expect(badges).toContain('hours_100')
    expect(badges).toContain('hours_250')
    expect(badges).toContain('hours_500')
  })

  it('does not include special badge (manually awarded only)', () => {
    expect(computeEarnedMilestoneBadges(1000)).not.toContain('special')
  })

  it('returns hours_10 through hours_100 at 150 hours', () => {
    const badges = computeEarnedMilestoneBadges(150)
    expect(badges).toContain('hours_100')
    expect(badges).not.toContain('hours_250')
  })
})
```

---

### Step 4 — Server Action for manual special badge

**File**: `src/app/actions/volunteer-badge-actions.ts`

```typescript
'use server'

import { createRouteHandlerClient } from '@supabase/auth-helpers-nextjs'
import { cookies } from 'next/headers'
import { revalidatePath } from 'next/cache'
import { redirect } from 'next/navigation'
import { isAdmin } from '@/lib/auth/is-admin'
import { supabaseAdmin } from '@/lib/supabase/admin'

export async function awardSpecialBadge(
  volunteerId: string,
  note: string
): Promise<{ error?: string }> {
  const supabase = createRouteHandlerClient({ cookies })
  const { data: { user } } = await supabase.auth.getUser()

  if (!user) redirect('/auth/login')
  if (!(await isAdmin(user.id))) return { error: 'Sin autorización' }

  if (!note.trim()) return { error: 'La nota es requerida para el reconocimiento especial' }

  // Special badge: unique constraint allows only one — remove old if re-awarding
  await supabaseAdmin
    .from('volunteer_badges')
    .delete()
    .eq('volunteer_id', volunteerId)
    .eq('badge', 'special')

  const { error } = await supabaseAdmin
    .from('volunteer_badges')
    .insert({
      volunteer_id: volunteerId,
      badge: 'special',
      note: note.trim(),
      awarded_by: user.id,
    })

  if (error) return { error: 'No se pudo otorgar el reconocimiento' }

  revalidatePath(`/admin/volunteers/${volunteerId}`)
  revalidatePath('/admin/volunteers/recognition')
  return {}
}
```

---

### Step 5 — Recognition board (admin)

**File**: `src/app/admin/volunteers/recognition/page.tsx`

```typescript
import { createServerComponentClient } from '@supabase/auth-helpers-nextjs'
import { cookies } from 'next/headers'
import { redirect } from 'next/navigation'
import { isAdmin } from '@/lib/auth/is-admin'
import { supabaseAdmin } from '@/lib/supabase/admin'
import { getBadgeIcon, getBadgeLabel, type BadgeType } from '@/lib/badges/badge-config'

export default async function VolunteerRecognitionPage() {
  const supabase = createServerComponentClient({ cookies })
  const { data: { user } } = await supabase.auth.getUser()

  if (!user) redirect('/auth/login')
  if (!(await isAdmin(user.id))) redirect('/dashboard')

  // Fetch all badges with volunteer names
  const { data: badges } = await supabaseAdmin
    .from('volunteer_badges')
    .select(`
      id,
      badge,
      awarded_at,
      note,
      volunteer:volunteer_profiles(full_name)
    `)
    .order('awarded_at', { ascending: false })
    .limit(50)

  // Group by badge type for the milestone leaderboard
  const { data: topVolunteers } = await supabaseAdmin
    .from('volunteer_profiles')
    .select('id, full_name, hours_total')
    .eq('status', 'active')
    .order('hours_total', { ascending: false })
    .limit(10)

  return (
    <main className="max-w-4xl mx-auto py-8 px-4">
      <h1 className="text-2xl font-bold text-[var(--text-primary)] mb-6">
        Reconocimientos
      </h1>

      {/* Top volunteers leaderboard */}
      <section className="mb-8">
        <h2 className="text-lg font-semibold text-[var(--text-primary)] mb-3">
          Voluntarios destacados
        </h2>
        <ol className="space-y-2">
          {(topVolunteers ?? []).map((v, i) => (
            <li
              key={v.id}
              className="flex items-center justify-between bg-[var(--bg-card)] border border-[var(--border)] rounded p-3"
            >
              <div className="flex items-center gap-3">
                <span className="text-sm font-bold text-[var(--text-secondary)] w-6">
                  {i + 1}.
                </span>
                <a
                  href={`/admin/volunteers/${v.id}`}
                  className="text-sm text-[var(--text-primary)] hover:text-[var(--color-primary)]"
                >
                  {v.full_name}
                </a>
              </div>
              <span className="text-sm text-[var(--text-secondary)]">
                {v.hours_total ?? 0}h
              </span>
            </li>
          ))}
        </ol>
      </section>

      {/* Recent badge awards */}
      <section>
        <h2 className="text-lg font-semibold text-[var(--text-primary)] mb-3">
          Insignias recientes
        </h2>
        <ul className="space-y-2">
          {(badges ?? []).map((b) => {
            const volunteer = b.volunteer as { full_name: string } | null
            return (
              <li
                key={b.id}
                className="flex items-start gap-3 bg-[var(--bg-card)] border border-[var(--border)] rounded p-3"
              >
                <span className="text-2xl">{getBadgeIcon(b.badge as BadgeType)}</span>
                <div className="flex-1">
                  <p className="text-sm font-medium text-[var(--text-primary)]">
                    {volunteer?.full_name ?? '—'}
                    {' '}
                    <span className="font-normal text-[var(--text-secondary)]">
                      — {getBadgeLabel(b.badge as BadgeType)}
                    </span>
                  </p>
                  {b.note && (
                    <p className="text-xs text-[var(--text-secondary)] mt-0.5">{b.note}</p>
                  )}
                  <p className="text-xs text-[var(--text-secondary)] mt-0.5">
                    {new Date(b.awarded_at).toLocaleDateString('es-PY')}
                  </p>
                </div>
              </li>
            )
          })}
          {(badges ?? []).length === 0 && (
            <li className="text-sm text-[var(--text-secondary)] py-3">
              Aún no se han otorgado insignias
            </li>
          )}
        </ul>
      </section>
    </main>
  )
}
```

---

### Step 6 — Volunteer self-view badges

Add to the volunteer's personal dashboard (`src/app/volunteers/dashboard/page.tsx`). Extend the `Promise.all` with a 5th query:

```typescript
supabase
  .from('volunteer_badges')
  .select('badge, awarded_at, note')
  .order('awarded_at', { ascending: false }),
```

Then render in the JSX:

```tsx
{/* Badges */}
{(myBadges ?? []).length > 0 && (
  <section className="mt-8">
    <h2 className="text-lg font-semibold text-[var(--text-primary)] mb-3">
      Mis insignias
    </h2>
    <div className="flex flex-wrap gap-2">
      {(myBadges ?? []).map((b) => (
        <div
          key={b.badge}
          className="flex items-center gap-1.5 bg-[var(--bg-card)] border border-[var(--border)] rounded-full px-3 py-1 text-sm"
          title={b.note ?? undefined}
        >
          <span>{getBadgeIcon(b.badge as BadgeType)}</span>
          <span className="text-[var(--text-primary)]">
            {getBadgeLabel(b.badge as BadgeType)}
          </span>
        </div>
      ))}
    </div>
  </section>
)}
```

---

### Step 7 — Special badge award form on admin volunteer detail

In `src/app/admin/volunteers/[id]/page.tsx`, add a small form after the badge display:

```typescript
// Client component: src/app/admin/volunteers/[id]/AwardBadgeForm.tsx
'use client'

import { useState, useTransition } from 'react'
import { awardSpecialBadge } from '@/app/actions/volunteer-badge-actions'

interface AwardBadgeFormProps {
  volunteerId: string
}

export function AwardBadgeForm({ volunteerId }: AwardBadgeFormProps) {
  const [isPending, startTransition] = useTransition()
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setError(null)
    setSuccess(false)

    const note = (new FormData(e.currentTarget).get('note') as string).trim()

    startTransition(async () => {
      const result = await awardSpecialBadge(volunteerId, note)
      if (result.error) {
        setError(result.error)
      } else {
        setSuccess(true)
        ;(e.target as HTMLFormElement).reset()
      }
    })
  }

  return (
    <form onSubmit={handleSubmit} className="flex gap-2 items-end mt-3">
      <div className="flex-1">
        <label className="block text-xs text-[var(--text-secondary)] mb-1">
          Motivo del reconocimiento especial
        </label>
        <input
          name="note"
          type="text"
          required
          placeholder="Ej: Excelente dedicación durante la campaña de adopción"
          className="w-full text-sm border border-[var(--border)] rounded px-2 py-1.5 bg-[var(--bg-input)] text-[var(--text-primary)]"
        />
      </div>
      <button
        type="submit"
        disabled={isPending}
        className="px-3 py-1.5 text-sm rounded bg-[var(--color-primary)] text-white hover:bg-[var(--color-primary-hover)] disabled:opacity-50 whitespace-nowrap"
      >
        {isPending ? 'Otorgando…' : '🎖️ Otorgar insignia'}
      </button>
      {error && <p className="text-xs text-[var(--color-error)] ml-2">{error}</p>}
      {success && <p className="text-xs text-[var(--color-success)] ml-2">Insignia otorgada</p>}
    </form>
  )
}
```

---

### Data flow summary

```
Hours logged → trigger fires → sync_volunteer_hours_total()
  → updates volunteer_profiles.hours_total
  → inserts milestone badges (ON CONFLICT DO NOTHING = idempotent)

Admin awards special badge → awardSpecialBadge() Server Action
  → deletes existing special badge (one special per volunteer)
  → inserts new badge with note
  → revalidatePath → recognition board updates

Volunteer visits /volunteers/dashboard
  → parallel queries (RLS scoped): profile + shifts + tasks + hours + badges
  → badges rendered as pill chips

Admin visits /admin/volunteers/recognition
  → leaderboard: top 10 by hours_total
  → badge feed: last 50 awards with volunteer names
```

---

### Files to create/update

| File | Action |
|------|--------|
| `supabase/migrations/20260401000016_volunteer_badges.sql` | CREATE |
| `src/lib/badges/badge-config.ts` | CREATE |
| `src/lib/badges/__tests__/badge-config.test.ts` | CREATE |
| `src/app/actions/volunteer-badge-actions.ts` | CREATE |
| `src/app/admin/volunteers/recognition/page.tsx` | CREATE |
| `src/app/admin/volunteers/[id]/AwardBadgeForm.tsx` | CREATE |
| `src/app/admin/volunteers/[id]/page.tsx` | UPDATE (add badges section + AwardBadgeForm) |
| `src/app/volunteers/dashboard/page.tsx` | UPDATE (add badges query + rendering) |

## Related Issues

- EPIC-5
- S04
- Depends on: S01/T01 (volunteer_profiles), S01/T03 (isAdmin), S04/T01 (volunteer_hours, trigger)
