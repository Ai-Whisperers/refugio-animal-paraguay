---
task: T01
story: S01
epic: EPIC-5
title: Create volunteer signup form
status: ready
priority: medium
created: 2026-03-25T17:13:26.731341
---

# T01: Create volunteer signup form

## Description

Build a public-facing volunteer registration form that collects contact information, availability, skills, and motivation. On submission it creates a Supabase Auth account and inserts a `volunteer_profiles` row with status `pending_review`.

## Acceptance Criteria

- [ ] `volunteer_profiles` table with RLS: volunteers read/update own row; staff/admin read all
- [ ] Public form at `/volunteers/signup` collects: name, email, password, phone, availability (checkboxes), skills (checkboxes), motivation (textarea)
- [ ] On submit: creates Auth account + `volunteer_profiles` row with status `pending_review`
- [ ] Duplicate email shows a clear Spanish error message
- [ ] Successful submission redirects to `/volunteers/signup/confirmation`
- [ ] Unit tests cover input validation helpers

## Implementation Notes

### Database schema

**Migration**: `supabase/migrations/20260401000011_create_volunteer_profiles.sql`

```sql
create type volunteer_status as enum (
  'pending_review', 'active', 'inactive', 'rejected'
);

create table volunteer_profiles (
  id              uuid primary key references auth.users(id) on delete cascade,
  full_name       text not null,
  phone           text,
  availability    text[] not null default '{}',
  skills          text[] not null default '{}',
  motivation      text,
  status          volunteer_status not null default 'pending_review',
  hours_total     numeric(8,2) not null default 0,
  notes           text,
  created_at      timestamptz not null default now(),
  updated_at      timestamptz not null default now()
);

alter table volunteer_profiles enable row level security;

create policy "volunteer can read own profile"
  on volunteer_profiles for select using (auth.uid() = id);

create policy "volunteer can update own profile"
  on volunteer_profiles for update
  using (auth.uid() = id) with check (auth.uid() = id);

create policy "staff can read volunteer profiles"
  on volunteer_profiles for select
  using ((select role from profiles where id = auth.uid()) in ('staff', 'admin'));

create policy "admin can update volunteer profiles"
  on volunteer_profiles for update
  using ((select role from profiles where id = auth.uid()) = 'admin')
  with check (true);

-- Rollback:
-- drop table if exists volunteer_profiles;
-- drop type if exists volunteer_status;
```

### Constants

**`src/lib/volunteers/constants.ts`**

```typescript
export const AVAILABILITY_OPTIONS = [
  { value: 'monday_morning',    label: 'Lunes mañana' },
  { value: 'monday_afternoon',  label: 'Lunes tarde' },
  { value: 'tuesday_morning',   label: 'Martes mañana' },
  { value: 'tuesday_afternoon', label: 'Martes tarde' },
  { value: 'wednesday_morning', label: 'Miércoles mañana' },
  { value: 'wednesday_afternoon', label: 'Miércoles tarde' },
  { value: 'thursday_morning',  label: 'Jueves mañana' },
  { value: 'thursday_afternoon', label: 'Jueves tarde' },
  { value: 'friday_morning',    label: 'Viernes mañana' },
  { value: 'friday_afternoon',  label: 'Viernes tarde' },
  { value: 'saturday_all_day',  label: 'Sábado (todo el día)' },
  { value: 'sunday_all_day',    label: 'Domingo (todo el día)' },
] as const

export const SKILL_OPTIONS = [
  { value: 'dog_handling',       label: 'Manejo de perros' },
  { value: 'cat_handling',       label: 'Manejo de gatos' },
  { value: 'veterinary_assist',  label: 'Asistencia veterinaria' },
  { value: 'photography',        label: 'Fotografía para adopciones' },
  { value: 'social_media',       label: 'Redes sociales' },
  { value: 'transport',          label: 'Transporte de animales' },
  { value: 'construction',       label: 'Construcción / mantenimiento' },
  { value: 'fundraising',        label: 'Recaudación de fondos' },
  { value: 'admin',              label: 'Administración' },
] as const

export type AvailabilityValue = typeof AVAILABILITY_OPTIONS[number]['value']
export type SkillValue = typeof SKILL_OPTIONS[number]['value']
```

### Validation helper

**`src/lib/volunteers/validate-signup.ts`**

```typescript
import type { AvailabilityValue, SkillValue } from './constants'

export interface SignupInput {
  fullName: string
  email: string
  password: string
  phone: string
  availability: AvailabilityValue[]
  skills: SkillValue[]
  motivation: string
}

export interface SignupErrors {
  fullName?: string
  email?: string
  password?: string
  availability?: string
}

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

export function validateSignupInput(input: SignupInput): SignupErrors {
  const errors: SignupErrors = {}
  if (!input.fullName.trim()) errors.fullName = 'El nombre es obligatorio.'
  if (!EMAIL_RE.test(input.email)) errors.email = 'Ingresá un email válido.'
  if (input.password.length < 8) errors.password = 'La contraseña debe tener al menos 8 caracteres.'
  if (input.availability.length === 0) errors.availability = 'Seleccioná al menos una disponibilidad.'
  return errors
}

export function hasErrors(errors: SignupErrors): boolean {
  return Object.keys(errors).length > 0
}
```

### Server Action

**`src/app/actions/volunteer-signup.ts`**

```typescript
'use server'

import { createRouteHandlerClient } from '@supabase/auth-helpers-nextjs'
import { createClient } from '@supabase/supabase-js'
import { cookies } from 'next/headers'
import { redirect } from 'next/navigation'
import { validateSignupInput, hasErrors } from '@/lib/volunteers/validate-signup'
import type { SignupInput } from '@/lib/volunteers/validate-signup'

const supabaseAdmin = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
)

export async function signupVolunteer(input: SignupInput): Promise<{ error?: string }> {
  const errors = validateSignupInput(input)
  if (hasErrors(errors)) return { error: Object.values(errors)[0] }

  const supabase = createRouteHandlerClient({ cookies })
  const { data: authData, error: authError } = await supabase.auth.signUp({
    email: input.email,
    password: input.password,
  })

  if (authError) {
    if (authError.message.includes('already registered')) {
      return { error: 'Ya existe una cuenta con ese email. Intentá iniciar sesión.' }
    }
    return { error: 'Error al crear la cuenta. Intentá de nuevo.' }
  }

  if (!authData.user) return { error: 'No se pudo crear la cuenta.' }

  const { error: profileError } = await supabaseAdmin
    .from('volunteer_profiles')
    .insert({
      id: authData.user.id,
      full_name: input.fullName,
      phone: input.phone || null,
      availability: input.availability,
      skills: input.skills,
      motivation: input.motivation || null,
      status: 'pending_review',
    })

  if (profileError) {
    await supabaseAdmin.auth.admin.deleteUser(authData.user.id)
    return { error: 'Error al guardar el perfil. Intentá de nuevo.' }
  }

  redirect('/volunteers/signup/confirmation')
}
```

### Form Client Component

**`src/app/volunteers/signup/VolunteerSignupForm.tsx`**

```typescript
'use client'

import { useTransition, useState } from 'react'
import { signupVolunteer } from '@/app/actions/volunteer-signup'
import { AVAILABILITY_OPTIONS, SKILL_OPTIONS } from '@/lib/volunteers/constants'
import type { AvailabilityValue, SkillValue } from '@/lib/volunteers/constants'

export function VolunteerSignupForm() {
  const [isPending, startTransition] = useTransition()
  const [serverError, setServerError] = useState<string | null>(null)
  const [availability, setAvailability] = useState<AvailabilityValue[]>([])
  const [skills, setSkills] = useState<SkillValue[]>([])

  function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const fd = new FormData(e.currentTarget)
    startTransition(async () => {
      const result = await signupVolunteer({
        fullName: fd.get('fullName') as string,
        email: fd.get('email') as string,
        password: fd.get('password') as string,
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
        <label htmlFor="fullName" className="block text-sm font-medium text-[var(--text-primary)]">
          Nombre completo *
        </label>
        <input id="fullName" name="fullName" type="text" required
          className="mt-1 w-full rounded border border-[var(--border)] bg-[var(--bg-input)] px-3 py-2 text-sm" />
      </div>

      <div>
        <label htmlFor="email" className="block text-sm font-medium text-[var(--text-primary)]">
          Email *
        </label>
        <input id="email" name="email" type="email" required
          className="mt-1 w-full rounded border border-[var(--border)] bg-[var(--bg-input)] px-3 py-2 text-sm" />
      </div>

      <div>
        <label htmlFor="password" className="block text-sm font-medium text-[var(--text-primary)]">
          Contraseña * (mínimo 8 caracteres)
        </label>
        <input id="password" name="password" type="password" required minLength={8}
          className="mt-1 w-full rounded border border-[var(--border)] bg-[var(--bg-input)] px-3 py-2 text-sm" />
      </div>

      <div>
        <label htmlFor="phone" className="block text-sm font-medium text-[var(--text-primary)]">
          Teléfono
        </label>
        <input id="phone" name="phone" type="tel"
          className="mt-1 w-full rounded border border-[var(--border)] bg-[var(--bg-input)] px-3 py-2 text-sm" />
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
                    prev.includes(opt.value) ? prev.filter(v => v !== opt.value) : [...prev, opt.value]
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
                    prev.includes(opt.value) ? prev.filter(v => v !== opt.value) : [...prev, opt.value]
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
        <textarea id="motivation" name="motivation" rows={4}
          className="mt-1 w-full rounded border border-[var(--border)] bg-[var(--bg-input)] px-3 py-2 text-sm" />
      </div>

      <button type="submit" disabled={isPending}
        className="w-full rounded bg-[var(--color-primary)] px-4 py-2 text-sm font-semibold text-[var(--color-primary-text)] hover:bg-[var(--color-primary-hover)] disabled:opacity-50">
        {isPending ? 'Enviando…' : 'Registrarme como voluntario/a'}
      </button>
    </form>
  )
}
```

### Pages

**`src/app/volunteers/signup/page.tsx`**

```typescript
import { VolunteerSignupForm } from './VolunteerSignupForm'

export default function VolunteerSignupPage() {
  return (
    <main className="min-h-screen bg-[var(--bg-page)] py-12 px-4">
      <div className="mx-auto max-w-xl">
        <h1 className="mb-2 text-3xl font-bold text-[var(--text-primary)]">Sé voluntario/a</h1>
        <p className="mb-8 text-[var(--text-secondary)]">
          Completá el formulario y un miembro del equipo revisará tu solicitud.
        </p>
        <VolunteerSignupForm />
      </div>
    </main>
  )
}
```

**`src/app/volunteers/signup/confirmation/page.tsx`**

```typescript
export default function ConfirmationPage() {
  return (
    <main className="min-h-screen bg-[var(--bg-page)] flex items-center justify-center px-4">
      <div className="max-w-md text-center">
        <h1 className="text-2xl font-bold text-[var(--text-primary)] mb-4">¡Gracias por registrarte!</h1>
        <p className="text-[var(--text-secondary)]">
          Recibimos tu solicitud. Un miembro del equipo la revisará pronto y te contactaremos por email.
        </p>
      </div>
    </main>
  )
}
```

### Unit tests

**`src/lib/volunteers/__tests__/validate-signup.test.ts`**

```typescript
import { describe, it, expect } from 'vitest'
import { validateSignupInput, hasErrors } from '../validate-signup'
import type { SignupInput } from '../validate-signup'

const base: SignupInput = {
  fullName: 'María García', email: 'maria@example.com', password: 'secret123',
  phone: '', availability: ['saturday_all_day'], skills: [], motivation: '',
}

describe('validateSignupInput', () => {
  it('returns no errors for valid input', () => {
    expect(hasErrors(validateSignupInput(base))).toBe(false)
  })
  it('requires fullName', () => {
    expect(validateSignupInput({ ...base, fullName: '  ' }).fullName).toBeDefined()
  })
  it('rejects invalid email', () => {
    expect(validateSignupInput({ ...base, email: 'not-an-email' }).email).toBeDefined()
  })
  it('rejects short password', () => {
    expect(validateSignupInput({ ...base, password: 'short' }).password).toBeDefined()
  })
  it('requires at least one availability slot', () => {
    expect(validateSignupInput({ ...base, availability: [] }).availability).toBeDefined()
  })
  it('accepts password of exactly 8 characters', () => {
    expect(hasErrors(validateSignupInput({ ...base, password: '12345678' }))).toBe(false)
  })
})
```

### File checklist

| File | Action |
|------|--------|
| `supabase/migrations/20260401000011_create_volunteer_profiles.sql` | Create |
| `src/lib/volunteers/constants.ts` | Create |
| `src/lib/volunteers/validate-signup.ts` | Create |
| `src/lib/volunteers/__tests__/validate-signup.test.ts` | Create |
| `src/app/actions/volunteer-signup.ts` | Create |
| `src/app/volunteers/signup/page.tsx` | Create |
| `src/app/volunteers/signup/VolunteerSignupForm.tsx` | Create |
| `src/app/volunteers/signup/confirmation/page.tsx` | Create |

## Related Issues

- EPIC-5
- S01
