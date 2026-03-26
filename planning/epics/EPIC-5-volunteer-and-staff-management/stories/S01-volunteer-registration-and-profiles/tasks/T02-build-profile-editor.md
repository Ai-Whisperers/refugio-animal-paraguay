---
task: T02
story: S01
epic: EPIC-5
title: Build profile editor
status: ready
priority: medium
created: 2026-03-25T17:13:26.731399
---

# T02: Build profile editor

## Description

Build a protected profile editor at `/volunteers/profile/edit` where `active` volunteers can update their phone, availability, skills, and motivation. Changes are saved via a Server Action that enforces RLS (volunteers may only update their own row).

## Acceptance Criteria

- [ ] Page at `/volunteers/profile/edit` requires authentication; non-volunteers redirect to `/`
- [ ] Only volunteers with `status = 'active'` may access the editor; `pending_review` / `rejected` / `inactive` see a status message instead
- [ ] Form pre-fills with current profile data fetched server-side
- [ ] Editable fields: phone, availability (checkboxes), skills (checkboxes), motivation
- [ ] On submit: updates `volunteer_profiles` row; redirects to `/volunteers/profile` with success indicator
- [ ] Duplicate or invalid inputs show Spanish error messages
- [ ] Unit tests cover the update validation helper

## Implementation Notes

### Update validation helper

**`src/lib/volunteers/validate-update.ts`**

```typescript
import type { AvailabilityValue, SkillValue } from './constants'

export interface UpdateInput {
  phone: string
  availability: AvailabilityValue[]
  skills: SkillValue[]
  motivation: string
}

export interface UpdateErrors {
  availability?: string
}

export function validateUpdateInput(input: UpdateInput): UpdateErrors {
  const errors: UpdateErrors = {}
  if (input.availability.length === 0) {
    errors.availability = 'Seleccioná al menos una disponibilidad.'
  }
  return errors
}

export function hasUpdateErrors(errors: UpdateErrors): boolean {
  return Object.keys(errors).length > 0
}
```

### Unit tests

**`src/lib/volunteers/__tests__/validate-update.test.ts`**

```typescript
import { describe, it, expect } from 'vitest'
import { validateUpdateInput, hasUpdateErrors } from '../validate-update'
import type { UpdateInput } from '../validate-update'

const base: UpdateInput = {
  phone: '0981 123 456',
  availability: ['saturday_all_day'],
  skills: ['dog_handling'],
  motivation: 'Me encantan los animales.',
}

describe('validateUpdateInput', () => {
  it('returns no errors for valid input', () => {
    expect(hasUpdateErrors(validateUpdateInput(base))).toBe(false)
  })
  it('requires at least one availability slot', () => {
    expect(validateUpdateInput({ ...base, availability: [] }).availability).toBeDefined()
  })
  it('accepts empty skills array', () => {
    expect(hasUpdateErrors(validateUpdateInput({ ...base, skills: [] }))).toBe(false)
  })
  it('accepts empty phone', () => {
    expect(hasUpdateErrors(validateUpdateInput({ ...base, phone: '' }))).toBe(false)
  })
  it('accepts empty motivation', () => {
    expect(hasUpdateErrors(validateUpdateInput({ ...base, motivation: '' }))).toBe(false)
  })
})
```

### Server Action

**`src/app/actions/update-volunteer-profile.ts`**

```typescript
'use server'

import { createRouteHandlerClient } from '@supabase/auth-helpers-nextjs'
import { cookies } from 'next/headers'
import { redirect } from 'next/navigation'
import { validateUpdateInput, hasUpdateErrors } from '@/lib/volunteers/validate-update'
import type { UpdateInput } from '@/lib/volunteers/validate-update'

export async function updateVolunteerProfile(
  input: UpdateInput,
): Promise<{ error?: string }> {
  const errors = validateUpdateInput(input)
  if (hasUpdateErrors(errors)) return { error: Object.values(errors)[0] }

  const supabase = createRouteHandlerClient({ cookies })

  const {
    data: { user },
  } = await supabase.auth.getUser()
  if (!user) return { error: 'Sesión expirada. Iniciá sesión de nuevo.' }

  // Confirm the volunteer is active before allowing edits
  const { data: profile } = await supabase
    .from('volunteer_profiles')
    .select('status')
    .eq('id', user.id)
    .single()

  if (!profile || profile.status !== 'active') {
    return { error: 'Solo los voluntarios activos pueden editar su perfil.' }
  }

  const { error: updateError } = await supabase
    .from('volunteer_profiles')
    .update({
      phone: input.phone || null,
      availability: input.availability,
      skills: input.skills,
      motivation: input.motivation || null,
      updated_at: new Date().toISOString(),
    })
    .eq('id', user.id)

  if (updateError) return { error: 'Error al guardar los cambios. Intentá de nuevo.' }

  redirect('/volunteers/profile?updated=1')
}
```

### Profile editor form

**`src/app/volunteers/profile/edit/VolunteerProfileEditForm.tsx`**

```typescript
'use client'

import { useTransition, useState } from 'react'
import { updateVolunteerProfile } from '@/app/actions/update-volunteer-profile'
import { AVAILABILITY_OPTIONS, SKILL_OPTIONS } from '@/lib/volunteers/constants'
import type { AvailabilityValue, SkillValue } from '@/lib/volunteers/constants'
import type { VolunteerProfile } from '@/lib/volunteers/types'

interface Props {
  profile: VolunteerProfile
}

export function VolunteerProfileEditForm({ profile }: Props) {
  const [isPending, startTransition] = useTransition()
  const [serverError, setServerError] = useState<string | null>(null)
  const [availability, setAvailability] = useState<AvailabilityValue[]>(
    profile.availability as AvailabilityValue[],
  )
  const [skills, setSkills] = useState<SkillValue[]>(
    profile.skills as SkillValue[],
  )

  function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const fd = new FormData(e.currentTarget)
    startTransition(async () => {
      const result = await updateVolunteerProfile({
        phone: fd.get('phone') as string,
        availability,
        skills,
        motivation: fd.get('motivation') as string,
      })
      if (result?.error) setServerError(result.error)
    })
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6 max-w-xl mx-auto">
      {serverError && (
        <p role="alert" className="rounded bg-[var(--color-danger-subtle)] p-3 text-sm text-[var(--color-danger)]">
          {serverError}
        </p>
      )}

      <div>
        <label htmlFor="phone" className="block text-sm font-medium text-[var(--text-primary)]">
          Teléfono
        </label>
        <input
          id="phone"
          name="phone"
          type="tel"
          defaultValue={profile.phone ?? ''}
          className="mt-1 w-full rounded border border-[var(--border)] bg-[var(--bg-input)] px-3 py-2 text-sm"
        />
      </div>

      <fieldset>
        <legend className="text-sm font-medium text-[var(--text-primary)]">
          Disponibilidad * (seleccioná al menos una)
        </legend>
        <div className="mt-2 grid grid-cols-2 gap-2">
          {AVAILABILITY_OPTIONS.map(opt => (
            <label key={opt.value} className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={availability.includes(opt.value)}
                onChange={() =>
                  setAvailability(prev =>
                    prev.includes(opt.value)
                      ? prev.filter(v => v !== opt.value)
                      : [...prev, opt.value],
                  )
                }
              />
              {opt.label}
            </label>
          ))}
        </div>
      </fieldset>

      <fieldset>
        <legend className="text-sm font-medium text-[var(--text-primary)]">Habilidades</legend>
        <div className="mt-2 grid grid-cols-2 gap-2">
          {SKILL_OPTIONS.map(opt => (
            <label key={opt.value} className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={skills.includes(opt.value)}
                onChange={() =>
                  setSkills(prev =>
                    prev.includes(opt.value)
                      ? prev.filter(v => v !== opt.value)
                      : [...prev, opt.value],
                  )
                }
              />
              {opt.label}
            </label>
          ))}
        </div>
      </fieldset>

      <div>
        <label htmlFor="motivation" className="block text-sm font-medium text-[var(--text-primary)]">
          ¿Por qué querés ser voluntario/a?
        </label>
        <textarea
          id="motivation"
          name="motivation"
          rows={4}
          defaultValue={profile.motivation ?? ''}
          className="mt-1 w-full rounded border border-[var(--border)] bg-[var(--bg-input)] px-3 py-2 text-sm"
        />
      </div>

      <button
        type="submit"
        disabled={isPending}
        className="w-full rounded bg-[var(--color-primary)] px-4 py-2 text-sm font-semibold text-[var(--color-primary-text)] hover:bg-[var(--color-primary-hover)] disabled:opacity-50"
      >
        {isPending ? 'Guardando…' : 'Guardar cambios'}
      </button>
    </form>
  )
}
```

### Profile types

**`src/lib/volunteers/types.ts`**

```typescript
export interface VolunteerProfile {
  id: string
  full_name: string
  phone: string | null
  availability: string[]
  skills: string[]
  motivation: string | null
  status: 'pending_review' | 'active' | 'inactive' | 'rejected'
  hours_total: number
  notes: string | null
  created_at: string
  updated_at: string
}
```

### Pages

**`src/app/volunteers/profile/edit/page.tsx`**

```typescript
import { createServerComponentClient } from '@supabase/auth-helpers-nextjs'
import { cookies } from 'next/headers'
import { redirect } from 'next/navigation'
import { VolunteerProfileEditForm } from './VolunteerProfileEditForm'
import type { VolunteerProfile } from '@/lib/volunteers/types'

export default async function VolunteerProfileEditPage() {
  const supabase = createServerComponentClient({ cookies })

  const {
    data: { user },
  } = await supabase.auth.getUser()
  if (!user) redirect('/login')

  const { data: profile } = await supabase
    .from('volunteer_profiles')
    .select('*')
    .eq('id', user.id)
    .single<VolunteerProfile>()

  if (!profile) redirect('/')

  if (profile.status !== 'active') {
    const STATUS_MESSAGE: Record<string, string> = {
      pending_review: 'Tu solicitud está siendo revisada. Podrás editar tu perfil cuando sea aprobada.',
      inactive: 'Tu cuenta está inactiva. Contactá al equipo para reactivarla.',
      rejected: 'Tu solicitud no fue aprobada.',
    }
    return (
      <main className="min-h-screen bg-[var(--bg-page)] flex items-center justify-center px-4">
        <p className="text-[var(--text-secondary)] text-center max-w-sm">
          {STATUS_MESSAGE[profile.status] ?? 'Estado desconocido.'}
        </p>
      </main>
    )
  }

  return (
    <main className="min-h-screen bg-[var(--bg-page)] py-12 px-4">
      <div className="mx-auto max-w-xl">
        <h1 className="mb-2 text-3xl font-bold text-[var(--text-primary)]">Editar perfil</h1>
        <p className="mb-8 text-[var(--text-secondary)]">
          Actualizá tu disponibilidad, habilidades y datos de contacto.
        </p>
        <VolunteerProfileEditForm profile={profile} />
      </div>
    </main>
  )
}
```

**`src/app/volunteers/profile/page.tsx`**

```typescript
import { createServerComponentClient } from '@supabase/auth-helpers-nextjs'
import { cookies } from 'next/headers'
import { redirect } from 'next/navigation'
import Link from 'next/link'
import { AVAILABILITY_OPTIONS, SKILL_OPTIONS } from '@/lib/volunteers/constants'
import type { VolunteerProfile } from '@/lib/volunteers/types'

export default async function VolunteerProfilePage({
  searchParams,
}: {
  searchParams: { updated?: string }
}) {
  const supabase = createServerComponentClient({ cookies })

  const {
    data: { user },
  } = await supabase.auth.getUser()
  if (!user) redirect('/login')

  const { data: profile } = await supabase
    .from('volunteer_profiles')
    .select('*')
    .eq('id', user.id)
    .single<VolunteerProfile>()

  if (!profile) redirect('/')

  const availabilityLabels = AVAILABILITY_OPTIONS.filter(o =>
    profile.availability.includes(o.value),
  ).map(o => o.label)

  const skillLabels = SKILL_OPTIONS.filter(o =>
    profile.skills.includes(o.value),
  ).map(o => o.label)

  return (
    <main className="min-h-screen bg-[var(--bg-page)] py-12 px-4">
      <div className="mx-auto max-w-xl space-y-6">
        {searchParams.updated === '1' && (
          <p className="rounded bg-[var(--color-success-subtle)] p-3 text-sm text-[var(--color-success)]">
            Perfil actualizado correctamente.
          </p>
        )}

        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold text-[var(--text-primary)]">{profile.full_name}</h1>
          {profile.status === 'active' && (
            <Link
              href="/volunteers/profile/edit"
              className="rounded bg-[var(--color-primary)] px-3 py-1.5 text-sm font-medium text-[var(--color-primary-text)] hover:bg-[var(--color-primary-hover)]"
            >
              Editar
            </Link>
          )}
        </div>

        <dl className="space-y-3 text-sm">
          <div>
            <dt className="font-medium text-[var(--text-secondary)]">Estado</dt>
            <dd className="text-[var(--text-primary)] capitalize">{profile.status.replace('_', ' ')}</dd>
          </div>
          {profile.phone && (
            <div>
              <dt className="font-medium text-[var(--text-secondary)]">Teléfono</dt>
              <dd className="text-[var(--text-primary)]">{profile.phone}</dd>
            </div>
          )}
          <div>
            <dt className="font-medium text-[var(--text-secondary)]">Disponibilidad</dt>
            <dd className="text-[var(--text-primary)]">{availabilityLabels.join(', ') || '—'}</dd>
          </div>
          <div>
            <dt className="font-medium text-[var(--text-secondary)]">Habilidades</dt>
            <dd className="text-[var(--text-primary)]">{skillLabels.join(', ') || '—'}</dd>
          </div>
          <div>
            <dt className="font-medium text-[var(--text-secondary)]">Horas acumuladas</dt>
            <dd className="text-[var(--text-primary)]">{profile.hours_total}</dd>
          </div>
          {profile.motivation && (
            <div>
              <dt className="font-medium text-[var(--text-secondary)]">Motivación</dt>
              <dd className="text-[var(--text-primary)]">{profile.motivation}</dd>
            </div>
          )}
        </dl>
      </div>
    </main>
  )
}
```

### File checklist

| File | Action |
|------|--------|
| `src/lib/volunteers/types.ts` | Create |
| `src/lib/volunteers/validate-update.ts` | Create |
| `src/lib/volunteers/__tests__/validate-update.test.ts` | Create |
| `src/app/actions/update-volunteer-profile.ts` | Create |
| `src/app/volunteers/profile/edit/VolunteerProfileEditForm.tsx` | Create |
| `src/app/volunteers/profile/edit/page.tsx` | Create |
| `src/app/volunteers/profile/page.tsx` | Create |

## Related Issues

- EPIC-5
- S01
