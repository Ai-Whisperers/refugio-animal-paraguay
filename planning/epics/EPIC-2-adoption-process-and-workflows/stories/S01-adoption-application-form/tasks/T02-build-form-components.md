---
task: T02
story: S01
epic: EPIC-2
title: Build adoption form components
status: ready
priority: high
agent_type: frontend
created: 2026-03-25T10:00:00Z
---

# T02: Build adoption form components

## Description

Build the multi-step adoption application form as a Client Component tree using React Hook Form and native HTML controls. No Zustand, no Headless UI. Step state is managed with `useState`. The form submits via a Server Action defined in T03.

## Context

- Client Components (`'use client'`) — form controls require browser interaction
- React Hook Form manages field state and validation; no separate state store needed
- No Zustand — multi-step navigation uses `useState<number>` in the parent form
- No Headless UI — use native `<select>` elements styled with Tailwind CSS vars
- Server Action for submission imported from `@/app/actions/adoption`
- CSS: Tailwind CSS 3.4.19 PINNED — use CSS vars, NOT hardcoded colors

## File structure

```
src/components/adoption/
├── AdoptionForm.tsx          # Outer wrapper: step state, submit dispatch
├── FormProgress.tsx          # Step indicator (current / total)
├── sections/
│   ├── AdopterSection.tsx    # Name, email, phone, identity
│   ├── AddressSection.tsx    # Street, city, department
│   ├── HouseholdSection.tsx  # Residents, living type, other pets
│   ├── PreferencesSection.tsx# Species, size, age, special needs
│   ├── ExperienceSection.tsx # Ownership history, vet plans, time
│   └── AgreementsSection.tsx # Checkboxes for all consent fields
└── inputs/
    ├── TextInput.tsx         # label + input + error
    ├── SelectInput.tsx       # label + native select + error
    ├── CheckboxInput.tsx     # label + checkbox + error
    └── FileUpload.tsx        # Drag-and-drop, Supabase Storage upload
```

## Files to create

### `src/components/adoption/AdoptionForm.tsx`

```typescript
'use client'

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { adoptionApplicationSchema, type AdoptionApplication } from '@/lib/validation/adoption-schema'
import { submitAdoptionApplication } from '@/app/actions/adoption'
import { FormProgress } from './FormProgress'
import { AdopterSection } from './sections/AdopterSection'
import { AddressSection } from './sections/AddressSection'
import { HouseholdSection } from './sections/HouseholdSection'
import { PreferencesSection } from './sections/PreferencesSection'
import { ExperienceSection } from './sections/ExperienceSection'
import { AgreementsSection } from './sections/AgreementsSection'

const STEPS = [
  'Solicitante',
  'Dirección',
  'Hogar',
  'Preferencias',
  'Experiencia',
  'Acuerdos',
] as const

const STEP_FIELDS: Record<number, (keyof AdoptionApplication)[]> = {
  0: ['adopter'],
  1: ['address'],
  2: ['household'],
  3: ['animalPreferences'],
  4: ['experience'],
  5: ['agreements'],
}

export function AdoptionForm() {
  const [currentStep, setCurrentStep] = useState(0)
  const [submitError, setSubmitError] = useState<string | null>(null)

  const form = useForm<AdoptionApplication>({
    resolver: zodResolver(adoptionApplicationSchema),
    mode: 'onTouched',
    defaultValues: {
      address: { country: 'PY' },
      animalPreferences: { specialNeeds: false },
      agreements: {
        termsAccepted: false,
        privacyAccepted: false,
        homeVisitConsent: false,
        followUpContact: false,
      },
    },
  })

  const isLastStep = currentStep === STEPS.length - 1

  async function handleNext() {
    const fields = STEP_FIELDS[currentStep]
    const valid = await form.trigger(fields)
    if (valid) setCurrentStep((s) => s + 1)
  }

  async function onSubmit(data: AdoptionApplication) {
    setSubmitError(null)
    const result = await submitAdoptionApplication(data)
    if (result.error) {
      setSubmitError(result.error)
    }
    // On success, the Server Action redirects to /adoptar/confirmacion
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <FormProgress currentStep={currentStep} totalSteps={STEPS.length} labels={STEPS} />

      <form onSubmit={form.handleSubmit(onSubmit)} noValidate>
        <div className="bg-[var(--bg-card)] rounded-xl p-6 mt-6 space-y-6">
          {currentStep === 0 && <AdopterSection form={form} />}
          {currentStep === 1 && <AddressSection form={form} />}
          {currentStep === 2 && <HouseholdSection form={form} />}
          {currentStep === 3 && <PreferencesSection form={form} />}
          {currentStep === 4 && <ExperienceSection form={form} />}
          {currentStep === 5 && <AgreementsSection form={form} />}
        </div>

        {submitError && (
          <p className="mt-4 text-sm text-[var(--color-error)]">{submitError}</p>
        )}

        <div className="flex justify-between mt-6">
          {currentStep > 0 && (
            <button
              type="button"
              onClick={() => setCurrentStep((s) => s - 1)}
              className="px-4 py-2 text-sm text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
            >
              Anterior
            </button>
          )}
          <div className="ml-auto">
            {isLastStep ? (
              <button
                type="submit"
                disabled={form.formState.isSubmitting}
                className="px-6 py-2 rounded-lg bg-[var(--color-primary)] text-white text-sm font-medium disabled:opacity-50"
              >
                {form.formState.isSubmitting ? 'Enviando...' : 'Enviar solicitud'}
              </button>
            ) : (
              <button
                type="button"
                onClick={handleNext}
                className="px-6 py-2 rounded-lg bg-[var(--color-primary)] text-white text-sm font-medium"
              >
                Siguiente
              </button>
            )}
          </div>
        </div>
      </form>
    </div>
  )
}
```

### `src/components/adoption/FormProgress.tsx`

```typescript
'use client'

interface FormProgressProps {
  currentStep: number
  totalSteps: number
  labels: readonly string[]
}

export function FormProgress({ currentStep, totalSteps, labels }: FormProgressProps) {
  return (
    <nav aria-label="Pasos del formulario">
      <ol className="flex items-center justify-between gap-2">
        {labels.map((label, index) => {
          const isCompleted = index < currentStep
          const isCurrent = index === currentStep
          return (
            <li key={label} className="flex flex-col items-center gap-1 flex-1">
              <div
                className={`
                  w-8 h-8 rounded-full flex items-center justify-center text-xs font-medium
                  ${isCompleted ? 'bg-[var(--color-primary)] text-white' : ''}
                  ${isCurrent ? 'bg-[var(--color-primary)] text-white ring-2 ring-[var(--color-primary)] ring-offset-2' : ''}
                  ${!isCompleted && !isCurrent ? 'bg-[var(--bg-hover)] text-[var(--text-tertiary)]' : ''}
                `}
                aria-current={isCurrent ? 'step' : undefined}
              >
                {isCompleted ? '✓' : index + 1}
              </div>
              <span className={`text-xs hidden sm:block ${isCurrent ? 'text-[var(--text-primary)]' : 'text-[var(--text-tertiary)]'}`}>
                {label}
              </span>
            </li>
          )
        })}
      </ol>
      <div className="mt-2 text-xs text-[var(--text-tertiary)] text-center">
        Paso {currentStep + 1} de {totalSteps}
      </div>
    </nav>
  )
}
```

### `src/components/adoption/inputs/TextInput.tsx`

```typescript
import type { UseFormRegisterReturn, FieldError } from 'react-hook-form'

interface TextInputProps {
  label: string
  registration: UseFormRegisterReturn
  error?: FieldError
  type?: 'text' | 'email' | 'tel' | 'number'
  placeholder?: string
  required?: boolean
}

export function TextInput({ label, registration, error, type = 'text', placeholder, required }: TextInputProps) {
  return (
    <div className="space-y-1">
      <label className="block text-sm font-medium text-[var(--text-primary)]">
        {label}
        {required && <span className="ml-1 text-[var(--color-error)]">*</span>}
      </label>
      <input
        {...registration}
        type={type}
        placeholder={placeholder}
        aria-invalid={!!error}
        className={`
          w-full px-3 py-2 rounded-lg border text-sm bg-[var(--bg-input)]
          text-[var(--text-primary)] placeholder:text-[var(--text-tertiary)]
          focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]
          ${error ? 'border-[var(--color-error)]' : 'border-[var(--border-default)]'}
        `}
      />
      {error && (
        <p className="text-xs text-[var(--color-error)]" role="alert">
          {error.message}
        </p>
      )}
    </div>
  )
}
```

### `src/components/adoption/inputs/SelectInput.tsx`

```typescript
import type { UseFormRegisterReturn, FieldError } from 'react-hook-form'

interface SelectOption {
  value: string
  label: string
}

interface SelectInputProps {
  label: string
  registration: UseFormRegisterReturn
  options: SelectOption[]
  error?: FieldError
  required?: boolean
  placeholder?: string
}

export function SelectInput({ label, registration, options, error, required, placeholder }: SelectInputProps) {
  return (
    <div className="space-y-1">
      <label className="block text-sm font-medium text-[var(--text-primary)]">
        {label}
        {required && <span className="ml-1 text-[var(--color-error)]">*</span>}
      </label>
      <select
        {...registration}
        aria-invalid={!!error}
        className={`
          w-full px-3 py-2 rounded-lg border text-sm bg-[var(--bg-input)]
          text-[var(--text-primary)] focus:outline-none focus:ring-2
          focus:ring-[var(--color-primary)]
          ${error ? 'border-[var(--color-error)]' : 'border-[var(--border-default)]'}
        `}
      >
        {placeholder && <option value="">{placeholder}</option>}
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
      {error && (
        <p className="text-xs text-[var(--color-error)]" role="alert">
          {error.message}
        </p>
      )}
    </div>
  )
}
```

### `src/components/adoption/inputs/CheckboxInput.tsx`

```typescript
import type { UseFormRegisterReturn, FieldError } from 'react-hook-form'

interface CheckboxInputProps {
  label: string
  registration: UseFormRegisterReturn
  error?: FieldError
  description?: string
}

export function CheckboxInput({ label, registration, error, description }: CheckboxInputProps) {
  return (
    <div className="space-y-1">
      <label className="flex items-start gap-3 cursor-pointer">
        <input
          {...registration}
          type="checkbox"
          aria-invalid={!!error}
          className="mt-0.5 w-4 h-4 rounded border-[var(--border-default)] text-[var(--color-primary)] focus:ring-[var(--color-primary)]"
        />
        <span className="text-sm text-[var(--text-primary)]">
          {label}
          {description && (
            <span className="block text-xs text-[var(--text-tertiary)] mt-0.5">{description}</span>
          )}
        </span>
      </label>
      {error && (
        <p className="text-xs text-[var(--color-error)] ml-7" role="alert">
          {error.message}
        </p>
      )}
    </div>
  )
}
```

### `src/components/adoption/sections/AdopterSection.tsx`

```typescript
import type { UseFormReturn } from 'react-hook-form'
import type { AdoptionApplication } from '@/lib/validation/adoption-schema'
import { TextInput } from '../inputs/TextInput'
import { SelectInput } from '../inputs/SelectInput'

const IDENTITY_OPTIONS = [
  { value: 'cedula', label: 'Cédula de Identidad' },
  { value: 'pasaporte', label: 'Pasaporte' },
  { value: 'otro', label: 'Otro documento' },
]

interface AdopterSectionProps {
  form: UseFormReturn<AdoptionApplication>
}

export function AdopterSection({ form }: AdopterSectionProps) {
  const { register, formState: { errors } } = form
  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold text-[var(--text-primary)]">Información del solicitante</h2>
      <TextInput label="Nombre completo" registration={register('adopter.fullName')} error={errors.adopter?.fullName} required />
      <TextInput label="Correo electrónico" registration={register('adopter.email')} type="email" error={errors.adopter?.email} required />
      <TextInput label="Teléfono" registration={register('adopter.phone')} type="tel" placeholder="+595 9X XXX XXXX" error={errors.adopter?.phone} required />
      <SelectInput label="Tipo de documento" registration={register('adopter.identityType')} options={IDENTITY_OPTIONS} error={errors.adopter?.identityType} required placeholder="Seleccionar..." />
      <TextInput label="Número de documento" registration={register('adopter.identityNumber')} error={errors.adopter?.identityNumber} required />
    </div>
  )
}
```

## Acceptance Criteria

- [ ] `AdoptionForm` uses `useState<number>` for step tracking — no Zustand store
- [ ] `AdoptionForm` uses `useForm` with `zodResolver` from `@hookform/resolvers/zod`
- [ ] `handleNext()` calls `form.trigger(fields)` before advancing — validates current step only
- [ ] `FormProgress` renders all step labels, marks completed steps with ✓
- [ ] `TextInput`, `SelectInput`, `CheckboxInput` all use `UseFormRegisterReturn` props
- [ ] `SelectInput` uses native `<select>` — no Headless UI dependency
- [ ] All error messages displayed via `role="alert"` paragraph
- [ ] Active/error border uses CSS var (`var(--color-error)`, `var(--border-default)`) — no hardcoded colors
- [ ] Form submission dispatches to Server Action `submitAdoptionApplication` (defined in T03)
- [ ] `isSubmitting` state disables the submit button and shows "Enviando..."
- [ ] TypeScript: no type errors in any component

## Implementation Notes

- React Hook Form's `trigger(fields)` accepts an array of top-level keys — step 0 passes `['adopter']`, step 1 passes `['address']`, etc.
- `mode: 'onTouched'` shows errors only after the user has blurred a field — avoids premature red highlighting
- `noValidate` on the `<form>` element disables native browser validation (React Hook Form handles it)
- File upload component (`FileUpload.tsx`) is deferred — it uploads to Supabase Storage and stores the path in a hidden field; implement after the base form works
- Each section component receives the full `UseFormReturn<AdoptionApplication>` — allows calling `form.trigger()` from within sections if needed

## Related

- Depends on: S01/T01 (database migration, types), S01/T03 (Server Action `submitAdoptionApplication`)
- Part of: S01 — Adoption Application Form
