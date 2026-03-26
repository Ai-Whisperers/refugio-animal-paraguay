---
task: T03
story: S01
epic: EPIC-2
title: Implement Zod validation schema and Server Action
status: ready
priority: high
agent_type: fullstack
created: 2026-03-25T10:00:00Z
---

# T03: Implement Zod validation schema and Server Action

## Description

Define the `adoptionApplicationSchema` Zod schema in `src/lib/validation/adoption-schema.ts`, then implement the `submitAdoptionApplication` Server Action in `src/app/actions/adoption.ts`. The Server Action validates incoming data, authenticates the user via Supabase, inserts into `adoption_applications`, and redirects on success or returns a structured error.

## Context

- Next.js 14 App Router — Server Actions use `'use server'` directive, NOT API routes
- Supabase-only backend — NO Prisma, NO ORM
- Auth: `(await supabase.auth.getUser()).data.user?.id` — NOT deprecated `supabase.auth.user()?.id`
- Redirect on success via `redirect('/adoptar/confirmacion')` from `next/navigation`
- On error: return `{ error: string }` so `AdoptionForm.tsx` can display it inline
- CSS: Tailwind CSS 3.4.19 PINNED — no UI in this task

## Files to create

### `src/lib/validation/adoption-schema.ts`

```typescript
import { z } from 'zod'

export const adoptionApplicationSchema = z.object({
  adopter: z.object({
    fullName: z.string()
      .min(3, { message: 'Nombre debe tener al menos 3 caracteres' })
      .max(100, { message: 'Nombre es demasiado largo' }),
    email: z.string()
      .email({ message: 'Email inválido' }),
    phone: z.string()
      .regex(/^(\+595|0)?[9]\d{8,9}$/, {
        message: 'Número de teléfono Paraguay inválido',
      }),
    identityType: z.enum(['cedula', 'pasaporte', 'otro']),
    identityNumber: z.string()
      .min(4, { message: 'Número de documento inválido' })
      .max(20),
  }),
  address: z.object({
    street: z.string()
      .min(3, { message: 'Calle requerida' })
      .max(200),
    city: z.string()
      .min(2, { message: 'Ciudad requerida' }),
    department: z.string()
      .min(2, { message: 'Departamento requerido' }),
    postalCode: z.string().optional(),
    country: z.literal('PY'),
  }),
  household: z.object({
    residentsCount: z.number()
      .int()
      .min(1, { message: 'Debe haber al menos 1 residente' })
      .max(20),
    childrenAges: z.array(z.number().int().min(0).max(100)).optional(),
    otherPets: z.array(z.object({
      type: z.string(),
      name: z.string(),
      age: z.number().int().min(0),
    })).optional(),
    livingType: z.enum(['casa', 'apartamento', 'chacra']),
  }),
  animalPreferences: z.object({
    species: z.enum(['perro', 'gato', 'otro']),
    sizePreference: z.enum(['pequeño', 'mediano', 'grande']).optional(),
    agePreference: z.enum(['cachorro', 'adulto', 'senior']).optional(),
    specialNeeds: z.boolean().default(false),
  }),
  experience: z.object({
    hasOwnedPets: z.boolean(),
    experienceYears: z.number().int().min(0).max(80),
    veterinaryPlans: z.string()
      .min(10, { message: 'Describa sus planes veterinarios' }),
    timeCommitment: z.number().min(0).max(24),
    trainingExperience: z.string()
      .min(10, { message: 'Describa su experiencia con adiestramiento' }),
  }),
  agreements: z.object({
    termsAccepted: z.boolean()
      .refine((v) => v === true, { message: 'Debe aceptar los términos' }),
    privacyAccepted: z.boolean()
      .refine((v) => v === true, { message: 'Debe aceptar la política de privacidad' }),
    homeVisitConsent: z.boolean()
      .refine((v) => v === true, { message: 'Debe consentir la visita al hogar' }),
    followUpContact: z.boolean(),
  }),
})

export type AdoptionApplication = z.infer<typeof adoptionApplicationSchema>
```

### `src/app/actions/adoption.ts`

```typescript
'use server'

import { redirect } from 'next/navigation'
import { createServerClient } from '@/lib/supabase/server'
import { adoptionApplicationSchema, type AdoptionApplication } from '@/lib/validation/adoption-schema'

type SubmitResult = { error: string }

export async function submitAdoptionApplication(
  data: AdoptionApplication,
): Promise<SubmitResult | never> {
  // Parse and validate — catches typos/tampered payloads from the client
  const parsed = adoptionApplicationSchema.safeParse(data)
  if (!parsed.success) {
    return { error: 'Datos del formulario inválidos. Por favor revise los campos.' }
  }

  const supabase = await createServerClient()

  // Use the non-deprecated getUser() API
  const { data: { user }, error: authError } = await supabase.auth.getUser()
  if (authError || !user) {
    return { error: 'Debe iniciar sesión para enviar una solicitud de adopción.' }
  }

  const { error: insertError } = await supabase
    .from('adoption_applications')
    .insert({
      adopter_id: user.id,
      status: 'submitted',
      data: parsed.data,
      submitted_at: new Date().toISOString(),
    })

  if (insertError) {
    return { error: 'Error al enviar la solicitud. Por favor intente de nuevo.' }
  }

  // redirect() throws internally — must not be inside try/catch
  redirect('/adoptar/confirmacion')
}
```

## Acceptance Criteria

- [ ] `adoptionApplicationSchema` exported from `src/lib/validation/adoption-schema.ts`
- [ ] `AdoptionApplication` type is `z.infer<typeof adoptionApplicationSchema>` — used by T02 form components
- [ ] Field `experience.veterinaryPlans` spelled correctly (no typo `veterinayPlans`)
- [ ] Server Action file starts with `'use server'` directive
- [ ] Auth uses `(await supabase.auth.getUser()).data.user?.id` — no deprecated `supabase.auth.user()`
- [ ] Unauthenticated calls return `{ error: string }` — no thrown exceptions reaching client
- [ ] `redirect('/adoptar/confirmacion')` called on successful insert (outside try/catch)
- [ ] DB errors return `{ error: string }` for inline display in `AdoptionForm`
- [ ] `adoptionApplicationSchema.safeParse()` called server-side — guards against tampered client data
- [ ] TypeScript: no type errors in either file

## Implementation Notes

- `redirect()` from `next/navigation` throws a special Next.js error internally — calling it inside a `try/catch` block will swallow it silently. Keep `redirect()` after any error checks, outside of try/catch.
- `safeParse()` is preferred over `parse()` in the Server Action because it allows returning a structured error object rather than throwing, which would surface as an unhandled error to the user.
- The Zod schema lives in `src/lib/validation/adoption-schema.ts` (not in `src/app/actions/`) so it can be imported by both the Server Action (for server-side re-validation) and by `AdoptionForm.tsx` (via `zodResolver`) without creating a circular dependency.
- `createServerClient()` is the SSR-compatible Supabase client from `@/lib/supabase/server` — it reads the session from cookies. Do not use the browser client here.

## Related

- Depends on: S01/T01 (database table `adoption_applications`), S01/T02 (imports `submitAdoptionApplication` and `AdoptionApplication` type)
- Part of: S01 — Adoption Application Form
