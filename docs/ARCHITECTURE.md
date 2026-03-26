# Architecture — Refugio Animal Paraguay

## Overview

Next.js 14 (App Router) + Supabase backend. Strict 4-layer separation: Structure, Styling, Functionality, Content. Modeled after production patterns from the Vete veterinary platform.

---

## Core Principle: 4-Layer Separation

Every concern lives in exactly one layer. No exceptions.

```
Layer 1: Structure    →  src/app/ + src/components/layout/
Layer 2: Styling      →  src/styles/ + src/components/ui/
Layer 3: Functionality →  src/services/ + src/hooks/ + src/store/
Layer 4: Content      →  src/content/i18n/ + src/content/seo/
```

**Rules:**
- Pages (`src/app/`) contain zero business logic, zero inline styles, zero hardcoded strings
- Components receive data via props; they do not fetch data themselves
- All Supabase queries go through service classes (`src/services/supabase/`)
- All strings are keys resolved via `next-intl`; no string literals in JSX

---

## Directory Structure

```
src/
├── app/                          # LAYER 1: Structure (Next.js App Router)
│   ├── layout.tsx                # Root layout — font, providers, metadata
│   ├── page.tsx                  # Homepage shell — delegates to components
│   ├── globals.css               # Tailwind base import only
│   ├── [locale]/                 # i18n routing (es-PY, gn)
│   │   ├── layout.tsx            # Locale provider wrapper
│   │   ├── animales/             # Animal catalog pages
│   │   │   ├── page.tsx          # Animal list page
│   │   │   └── [id]/page.tsx     # Animal detail page
│   │   ├── adoptar/              # Adoption flow
│   │   ├── donar/                # Donation pages
│   │   ├── voluntarios/          # Volunteer pages
│   │   └── admin/                # Protected admin area
│   └── api/                      # Route handlers (webhooks, etc.)
│       ├── webhooks/
│       │   ├── stripe/route.ts
│       │   └── resend/route.ts
│       └── storage/route.ts      # Signed URL generation
│
├── components/                   # LAYER 1 + 2: Structure & Styling
│   ├── layout/                   # Structural wrappers — no logic
│   │   ├── Header.tsx
│   │   ├── Footer.tsx
│   │   ├── Sidebar.tsx
│   │   └── PageShell.tsx
│   ├── ui/                       # LAYER 2: shadcn/ui base components
│   │   ├── button.tsx            # shadcn Button — no custom logic
│   │   ├── card.tsx
│   │   ├── input.tsx
│   │   ├── badge.tsx
│   │   └── dialog.tsx
│   ├── animals/                  # Animal domain components
│   │   ├── AnimalCard.tsx        # Display only — receives Animal prop
│   │   ├── AnimalCard.styles.ts  # cva variants
│   │   ├── AnimalGrid.tsx
│   │   ├── AnimalDetail.tsx
│   │   └── AnimalStatusBadge.tsx
│   ├── adoptions/                # Adoption domain components
│   │   ├── AdoptionForm.tsx
│   │   ├── AdoptionStatus.tsx
│   │   └── AdoptionTimeline.tsx
│   ├── donations/                # Donation domain components
│   │   ├── DonationForm.tsx
│   │   ├── PaymentMethodSelector.tsx
│   │   └── DonorReceipt.tsx
│   └── shared/                   # Cross-domain components
│       ├── PhotoUpload.tsx
│       ├── LoadingSkeleton.tsx
│       └── ErrorBoundary.tsx
│
├── styles/                       # LAYER 2: Styling tokens
│   ├── tokens.css                # Design tokens (colors, spacing, radius)
│   ├── typography.css            # Font stacks, scale
│   └── animations.css            # Transition definitions
│
├── services/                     # LAYER 3: Functionality — ALL data access here
│   ├── supabase/                 # Supabase domain services
│   │   ├── base-service.ts       # Abstract class with handleError + result types
│   │   ├── animal-service.ts     # Animal CRUD, photo URLs, status management
│   │   ├── adoption-service.ts   # Application submit, status transitions
│   │   ├── donation-service.ts   # Donation records, recurring setup
│   │   ├── medical-service.ts    # Medical records, vet notes
│   │   ├── volunteer-service.ts  # Volunteer applications, shifts
│   │   ├── notification-service.ts # Email + WhatsApp triggers
│   │   └── storage-service.ts   # Supabase Storage uploads + signed URLs
│   ├── payment/                  # Payment processing
│   │   ├── stripe-service.ts     # Cards, iDEAL, SEPA, Bancontact
│   │   └── paypal-service.ts     # PayPal SDK
│   └── email/                    # Transactional email
│       └── resend-service.ts     # Receipts, confirmations, ANBI receipts
│
├── hooks/                        # LAYER 3: Client-side data & state
│   ├── useAnimals.ts             # Animal list with SWR/React Query
│   ├── useAnimal.ts              # Single animal detail
│   ├── useAdoptionForm.ts        # Form state + submission
│   ├── useDonationForm.ts        # Donation flow state
│   └── useUpload.ts              # File upload with progress
│
├── store/                        # LAYER 3: Global client state (Zustand)
│   ├── ui-store.ts               # Modal state, sidebar, notifications
│   ├── filter-store.ts           # Animal filter/search state
│   └── cart-store.ts             # Donation cart (if multi-item)
│
├── lib/                          # Shared utilities (not domain-specific)
│   ├── supabase/
│   │   ├── server.ts             # createServerClient (SSR with cookies)
│   │   ├── client.ts             # createBrowserClient (singleton)
│   │   └── service.ts            # Service role client (admin only)
│   ├── env.ts                    # Validated env vars (fail-fast)
│   ├── logger.ts                 # Structured logging
│   ├── schemas/                  # Zod validation schemas
│   │   ├── animal.schema.ts
│   │   ├── adoption.schema.ts
│   │   ├── donation.schema.ts
│   │   └── volunteer.schema.ts
│   └── types/                    # TypeScript type definitions
│       ├── entities/             # Database entity types (generated + extended)
│       │   ├── animal.ts
│       │   ├── adoption.ts
│       │   ├── donation.ts
│       │   └── user.ts
│       └── service-result.ts     # ServiceResult<T> union type
│
├── actions/                      # LAYER 3: Server Actions (form submissions)
│   ├── animals/
│   │   ├── create-animal.ts
│   │   └── update-animal-status.ts
│   ├── adoptions/
│   │   ├── submit-adoption-request.ts
│   │   └── update-adoption-status.ts
│   ├── donations/
│   │   ├── create-donation.ts
│   │   └── create-recurring-donation.ts
│   └── volunteers/
│       └── submit-volunteer-application.ts
│
└── content/                      # LAYER 4: Content — all text lives here
    ├── i18n/
    │   ├── es-PY/               # Paraguayan Spanish (primary)
    │   │   ├── common.json
    │   │   ├── animals.json
    │   │   ├── adoptions.json
    │   │   ├── donations.json
    │   │   └── errors.json
    │   └── gn/                  # Guaraní (secondary)
    │       └── common.json
    └── seo/
        ├── metadata.ts          # Static OG/meta per route
        └── structured-data.ts   # JSON-LD schemas
```

---

## Supabase Architecture

### Client Setup

Three Supabase clients for different contexts:

```typescript
// lib/supabase/server.ts — Server Components, Server Actions, Route Handlers
// Uses @supabase/ssr with Next.js cookie handling
// keyType: 'anon' (default) | 'service_role' (admin only)
import { createClient } from '@/lib/supabase/server'
const supabase = await createClient()

// lib/supabase/client.ts — Client Components only
// Singleton pattern to avoid re-initialization
import { createClient } from '@/lib/supabase/client'
const supabase = createClient()

// lib/supabase/service.ts — Background jobs, admin operations only
// Bypasses RLS — NEVER expose to client
import { createServiceClient } from '@/lib/supabase/service'
```

### Database Schema

Core tables with Row Level Security:

```sql
-- Animals: readable by all, writable by staff/admin
animals (
  id uuid PRIMARY KEY,
  name text NOT NULL,
  species text NOT NULL CHECK (species IN ('dog', 'cat', 'rabbit', 'bird', 'other')),
  breed text,
  birth_date date,
  sex text CHECK (sex IN ('male', 'female', 'unknown')),
  status text NOT NULL DEFAULT 'available'
    CHECK (status IN ('available', 'reserved', 'adopted', 'medical_hold', 'deceased')),
  weight_kg numeric,
  color text,
  description text,
  is_neutered boolean,
  microchip_id text,
  intake_date date NOT NULL DEFAULT CURRENT_DATE,
  photo_urls text[] DEFAULT '{}',
  primary_photo_url text,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
)

-- Adoption applications
adoption_requests (
  id uuid PRIMARY KEY,
  animal_id uuid REFERENCES animals(id),
  applicant_user_id uuid REFERENCES auth.users(id),
  status text NOT NULL DEFAULT 'pending'
    CHECK (status IN ('pending', 'reviewing', 'approved', 'rejected', 'completed', 'cancelled')),
  applicant_name text NOT NULL,
  applicant_email text NOT NULL,
  applicant_phone text,
  housing_type text,
  has_garden boolean,
  has_other_pets boolean,
  other_pets_description text,
  reason text,
  reviewed_by uuid REFERENCES auth.users(id),
  reviewed_at timestamptz,
  notes text,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
)

-- Donations
donations (
  id uuid PRIMARY KEY,
  donor_user_id uuid REFERENCES auth.users(id),
  donor_name text NOT NULL,
  donor_email text NOT NULL,
  donor_country text,
  amount_cents integer NOT NULL,
  currency text NOT NULL DEFAULT 'PYG',
  payment_provider text NOT NULL,
  payment_method text,
  stripe_payment_intent_id text,
  stripe_subscription_id text,
  is_recurring boolean DEFAULT false,
  anbi_receipt_sent boolean DEFAULT false,
  gdpr_consent boolean DEFAULT false,
  status text NOT NULL DEFAULT 'pending'
    CHECK (status IN ('pending', 'completed', 'failed', 'refunded')),
  created_at timestamptz DEFAULT now()
)

-- Medical records (linked to animals)
medical_records (
  id uuid PRIMARY KEY,
  animal_id uuid REFERENCES animals(id),
  vet_user_id uuid REFERENCES auth.users(id),
  record_type text NOT NULL,
  date date NOT NULL,
  description text NOT NULL,
  treatment text,
  medications text[],
  follow_up_date date,
  document_urls text[] DEFAULT '{}',
  created_at timestamptz DEFAULT now()
)

-- Volunteers
volunteer_applications (
  id uuid PRIMARY KEY,
  user_id uuid REFERENCES auth.users(id),
  status text DEFAULT 'pending',
  name text NOT NULL,
  email text NOT NULL,
  phone text,
  availability text[],
  skills text[],
  experience text,
  created_at timestamptz DEFAULT now()
)
```

### Row Level Security Policies

```sql
-- Animals: public read, staff write
ALTER TABLE animals ENABLE ROW LEVEL SECURITY;
CREATE POLICY "animals_public_read" ON animals FOR SELECT USING (true);
CREATE POLICY "animals_staff_insert" ON animals FOR INSERT
  WITH CHECK (auth.jwt() ->> 'role' IN ('staff', 'admin'));
CREATE POLICY "animals_staff_update" ON animals FOR UPDATE
  USING (auth.jwt() ->> 'role' IN ('staff', 'admin'));

-- Adoption requests: owner read own, staff read all
ALTER TABLE adoption_requests ENABLE ROW LEVEL SECURITY;
CREATE POLICY "adoptions_own_read" ON adoption_requests FOR SELECT
  USING (applicant_user_id = auth.uid() OR auth.jwt() ->> 'role' IN ('staff', 'admin'));
CREATE POLICY "adoptions_authenticated_insert" ON adoption_requests FOR INSERT
  WITH CHECK (auth.uid() IS NOT NULL);

-- Donations: owner read own, admin read all
ALTER TABLE donations ENABLE ROW LEVEL SECURITY;
CREATE POLICY "donations_own_read" ON donations FOR SELECT
  USING (donor_user_id = auth.uid() OR auth.jwt() ->> 'role' = 'admin');
```

### Storage Buckets

```
animals-photos/          # Public read, staff write
  {animal-id}/
    {photo-id}.webp

adoption-documents/      # Private — applicant + staff only
  {adoption-id}/
    {document-name}.pdf

medical-documents/       # Private — vet + admin only
  {animal-id}/
    {record-id}/
      {document-name}.pdf
```

---

## Service Layer Pattern

Copied from Vete's production pattern. Every domain gets a service class that:
- Extends `BaseService`
- Accepts `SupabaseClient` in constructor (injected, not imported)
- Returns `ServiceResult<T>` union type
- Never throws — errors are returned as `{ success: false, error: string }`

```typescript
// lib/types/service-result.ts
export interface ServiceSuccess<T> {
  success: true;
  data: T;
}

export interface ServiceError {
  success: false;
  error: string;
  code?: string;
  details?: Record<string, unknown>;
}

export type ServiceResult<T> = ServiceSuccess<T> | ServiceError;
```

```typescript
// services/supabase/base-service.ts
import type { SupabaseClient } from '@supabase/supabase-js';
import type { ServiceResult } from '@/lib/types/service-result';
import { logger } from '@/lib/logger';

export abstract class BaseService {
  constructor(protected readonly supabase: SupabaseClient) {}

  protected async handleError<T>(
    operation: () => Promise<T>,
    errorMessage: string,
    context?: Record<string, unknown>
  ): Promise<ServiceResult<T>> {
    try {
      const data = await operation();
      return { success: true, data };
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : String(error);
      logger.error(errorMessage, { error: message, ...context });
      return { success: false, error: message };
    }
  }
}
```

```typescript
// services/supabase/animal-service.ts
import { BaseService } from './base-service';
import type { ServiceResult } from '@/lib/types/service-result';
import type { Animal } from '@/lib/types/entities/animal';

export class AnimalService extends BaseService {
  async list(filters?: AnimalFilters): Promise<ServiceResult<Animal[]>> {
    return this.handleError(async () => {
      let query = this.supabase
        .from('animals')
        .select('*')
        .eq('status', 'available');

      if (filters?.species) query = query.eq('species', filters.species);

      const { data, error } = await query.order('intake_date', { ascending: false });
      if (error) throw error;
      return data ?? [];
    }, 'Failed to fetch animals');
  }

  async getById(id: string): Promise<ServiceResult<Animal>> {
    return this.handleError(async () => {
      const { data, error } = await this.supabase
        .from('animals')
        .select('*, medical_records(*)')
        .eq('id', id)
        .single();
      if (error) throw error;
      if (!data) throw new Error('Animal not found');
      return data;
    }, 'Failed to fetch animal', { animalId: id });
  }
}
```

---

## Server Actions Pattern

Forms submit to Server Actions. No API routes for mutations.

```typescript
// actions/adoptions/submit-adoption-request.ts
'use server';

import { z } from 'zod';
import { revalidatePath } from 'next/cache';
import { createClient } from '@/lib/supabase/server';
import { AdoptionService } from '@/services/supabase/adoption-service';
import { adoptionRequestSchema } from '@/lib/schemas/adoption.schema';
import type { ActionResult } from '@/lib/types/action-result';

export async function submitAdoptionRequest(
  formData: FormData
): Promise<ActionResult> {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();

  if (!user) {
    return { success: false, error: 'Authentication required' };
  }

  const parsed = adoptionRequestSchema.safeParse(
    Object.fromEntries(formData)
  );

  if (!parsed.success) {
    return {
      success: false,
      error: 'Validation failed',
      fieldErrors: parsed.error.flatten().fieldErrors,
    };
  }

  const service = new AdoptionService(supabase);
  const result = await service.create(user.id, parsed.data);

  if (!result.success) {
    return { success: false, error: result.error };
  }

  revalidatePath('/animales');
  return { success: true, data: result.data };
}
```

---

## Component Pattern

Components are pure — they receive typed props and return JSX. No data fetching inside components.

```typescript
// components/animals/AnimalCard.tsx
import type { Animal } from '@/lib/types/entities/animal';
import { useTranslations } from 'next-intl';
import { animalCardVariants } from './AnimalCard.styles';

interface AnimalCardProps {
  animal: Animal;
  variant?: 'default' | 'compact' | 'featured';
  onAdoptClick?: (id: string) => void;
}

export function AnimalCard({ animal, variant = 'default', onAdoptClick }: AnimalCardProps) {
  const t = useTranslations('animals');

  return (
    <div className={animalCardVariants({ variant })}>
      {/* JSX only — no fetch, no business logic */}
    </div>
  );
}
```

```typescript
// components/animals/AnimalCard.styles.ts — LAYER 2: Styling isolated
import { cva } from 'class-variance-authority';

export const animalCardVariants = cva(
  'rounded-xl border bg-[var(--bg-card)] transition-shadow',  // CSS variables, not bg-white
  {
    variants: {
      variant: {
        default: 'p-4 shadow-sm hover:shadow-md',
        compact: 'p-2 shadow-none',
        featured: 'p-6 shadow-lg border-primary',
      },
    },
    defaultVariants: { variant: 'default' },
  }
);
```

---

## CSS Variable Theming

**Rule**: Never use hardcoded Tailwind color utilities (`bg-white`, `text-gray-900`, `border-gray-200`). All colors reference CSS variables defined in `styles/tokens.css`.

```css
/* styles/tokens.css */
:root {
  --bg-base:        #ffffff;
  --bg-card:        #f9fafb;
  --bg-muted:       #f3f4f6;
  --bg-primary:     #16a34a;   /* green-600 — shelter brand */
  --bg-primary-hover: #15803d;

  --text-base:      #111827;
  --text-muted:     #6b7280;
  --text-inverted:  #ffffff;

  --border-base:    #e5e7eb;
  --border-strong:  #d1d5db;

  --radius-card:    0.75rem;
  --shadow-card:    0 1px 3px 0 rgb(0 0 0 / 0.1);
}
```

```typescript
// ✅ CORRECT — uses CSS variables
'rounded-xl border border-[var(--border-base)] bg-[var(--bg-card)] text-[var(--text-base)]'

// ❌ FORBIDDEN — hardcoded Tailwind colors
'rounded-xl border border-gray-200 bg-white text-gray-900'
```

Tailwind CSS is **pinned at 3.4.19**. Do NOT upgrade to v4 — v4's build system does not scan JSON files, breaking `next-intl` dictionary loading and any JSON-based config imports. Pin in `package.json`:

```json
{ "dependencies": { "tailwindcss": "3.4.19" } }
```

---

## i18n Pattern

All user-visible strings come from translation files. Zero hardcoded strings in components.

```
content/i18n/es-PY/animals.json:
{
  "status": {
    "available": "Disponible para adopción",
    "reserved": "Reservado",
    "adopted": "Adoptado",
    "medical_hold": "En tratamiento médico"
  },
  "filters": {
    "species": "Especie",
    "all": "Todos"
  }
}
```

```typescript
// In a component:
const t = useTranslations('animals');
<span>{t('status.available')}</span>
```

---

## Authentication

Supabase Auth with custom roles in JWT:

```typescript
// Roles: 'adopter' | 'donor' | 'volunteer' | 'staff' | 'admin' | 'vet'
// Set via Supabase Auth hooks or DB function on user creation

// Middleware (src/middleware.ts):
// - Public routes: /, /animales/*, /donar, /voluntarios
// - Authenticated: /adoptar/formulario, /perfil/*
// - Staff-only: /admin/*
```

---

## Client Hooks Pattern

### useAsyncData\<T\>

Generic data-fetching hook. Use this instead of raw `useState + useEffect` combos.

```typescript
// hooks/useAsyncData.ts
import { useState, useEffect, useRef, useCallback } from 'react';

interface AsyncDataState<T> {
  data: T | null;
  isLoading: boolean;
  error: string | null;
  refetch: () => void;
}

export function useAsyncData<T>(
  fetcher: () => Promise<T>,
  deps: unknown[] = [],
  options?: { refetchInterval?: number }
): AsyncDataState<T> {
  const [data, setData] = useState<T | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const isMountedRef = useRef(true);  // prevents setState after unmount
  const [refreshKey, setRefreshKey] = useState(0);

  const refetch = useCallback(() => setRefreshKey(k => k + 1), []);

  useEffect(() => {
    isMountedRef.current = true;
    setIsLoading(true);
    setError(null);

    fetcher()
      .then(result => {
        if (isMountedRef.current) {
          setData(result);
          setIsLoading(false);
        }
      })
      .catch((err: unknown) => {
        if (isMountedRef.current) {
          setError(err instanceof Error ? err.message : 'Error desconocido');
          setIsLoading(false);
        }
      });

    return () => { isMountedRef.current = false; };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [refreshKey, ...deps]);

  useEffect(() => {
    if (!options?.refetchInterval) return;
    const id = setInterval(refetch, options.refetchInterval);
    return () => clearInterval(id);
  }, [refetch, options?.refetchInterval]);

  return { data, isLoading, error, refetch };
}
```

Usage:
```typescript
const { data: animals, isLoading, error, refetch } = useAsyncData(
  () => animalService.list(),
  [filters]
);
```

### Modal Hook Hierarchy

Three-level hierarchy. Use the simplest level that satisfies the requirement.

```typescript
// hooks/useModal.ts — Level 1: open/close state only
export function useModal(initialOpen = false) {
  const [isOpen, setIsOpen] = useState(initialOpen);
  return {
    isOpen,
    open: () => setIsOpen(true),
    close: () => setIsOpen(false),
    toggle: () => setIsOpen(v => !v),
  };
}

// hooks/useModalWithData.ts — Level 2: carries typed data
export function useModalWithData<T>() {
  const [isOpen, setIsOpen] = useState(false);
  const [data, setData] = useState<T | null>(null);

  return {
    isOpen,
    data,
    open: (item: T) => { setData(item); setIsOpen(true); },
    // 200ms delay on close — allows CSS exit transition before clearing data
    close: () => {
      setIsOpen(false);
      setTimeout(() => setData(null), 200);
    },
  };
}

// hooks/useModalForm.ts — Level 3: carries data + async submit
export function useModalForm<TData, TResult>(
  onSubmit: (data: TData) => Promise<ServiceResult<TResult>>
) {
  const modal = useModalWithData<TData>();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const submit = async (data: TData) => {
    setIsSubmitting(true);
    setSubmitError(null);
    const result = await onSubmit(data);
    setIsSubmitting(false);
    if (result.success) {
      modal.close();
    } else {
      setSubmitError(result.error);
    }
    return result;
  };

  return { ...modal, isSubmitting, submitError, submit };
}
```

### useConfirmation

Promise-based confirmation dialog — avoids prop-drilling callbacks.

```typescript
// hooks/useConfirmation.ts
import { useState, useRef, useCallback } from 'react';

interface ConfirmOptions {
  title: string;
  description: string;
  confirmLabel?: string;
  variant?: 'danger' | 'default';
}

export function useConfirmation() {
  const [isOpen, setIsOpen] = useState(false);
  const [options, setOptions] = useState<ConfirmOptions | null>(null);
  const resolveRef = useRef<((value: boolean) => void) | null>(null);

  const confirm = useCallback((opts: ConfirmOptions): Promise<boolean> => {
    setOptions(opts);
    setIsOpen(true);
    return new Promise(resolve => { resolveRef.current = resolve; });
  }, []);

  const handleConfirm = useCallback(() => {
    setIsOpen(false);
    resolveRef.current?.(true);
  }, []);

  const handleCancel = useCallback(() => {
    setIsOpen(false);
    resolveRef.current?.(false);
  }, []);

  return { isOpen, options, confirm, handleConfirm, handleCancel };
}

// Usage — caller awaits the promise
const { confirm, ...dialogProps } = useConfirmation();

const handleDelete = async (id: string) => {
  const ok = await confirm({
    title: 'Eliminar animal',
    description: '¿Seguro? Esta acción no se puede deshacer.',
    variant: 'danger',
  });
  if (!ok) return;
  await animalService.delete(id);
};
```

---

## PostgreSQL Error Mapping

Supabase returns PostgreSQL error codes. Map them to user-facing Spanish messages at the service layer.

```typescript
// lib/utils/pg-error.ts
const PG_ERROR_MESSAGES: Record<string, string> = {
  '23505': 'Ya existe un registro con estos datos.',           // unique_violation
  '23503': 'No se puede eliminar: tiene registros asociados.', // foreign_key_violation
  '23502': 'Faltan campos obligatorios.',                       // not_null_violation
  '22P02': 'Formato de datos inválido.',                        // invalid_text_representation
  'PGRST116': 'Registro no encontrado.',                        // PostgREST single() not found
};

export function pgErrorToSpanish(code: string | undefined): string {
  if (!code) return 'Ocurrió un error inesperado.';
  return PG_ERROR_MESSAGES[code] ?? 'Ocurrió un error inesperado.';
}
```

Apply in `BaseService.handleError()`:

```typescript
// In base-service.ts — extend error handling to map PG codes
import { pgErrorToSpanish } from '@/lib/utils/pg-error';

// Inside handleError catch block:
const pgCode = (error as { code?: string })?.code;
const message = pgCode
  ? pgErrorToSpanish(pgCode)
  : error instanceof Error ? error.message : 'Error desconocido';
```

---

## Anti-Patterns (Learned from Vete — Do Not Repeat)

1. **Cloudinary dependency** — Use Supabase Storage instead. Single vendor, integrated auth, RLS-based access control.

2. **Prisma in a Next.js edge environment** — Supabase client works in all Next.js runtimes (Node.js, Edge, RSC). No schema compilation step.

3. **Data fetching in components** — All data comes from Server Components (RSC) via services, or from hooks wrapping services. Never `fetch()` inside a component directly.

4. **Business logic in pages** — Pages are structural shells. All logic lives in services or Server Actions.

5. **Inline Tailwind without tokens** — Define design tokens in `styles/tokens.css` and reference via CSS variables. Avoids magic values scattered across components.

6. **God services** — One service class per domain entity. `AnimalService` does not touch donations. Split by bounded context.

7. **Hardcoded strings in JSX** — Every user-visible string goes through `useTranslations()`. Enables Guaraní support without touching components.

8. **Bare `process.env` access** — Use `lib/env.ts` which validates at startup and gives typed access. Missing env vars fail fast with clear messages.

---

## Environment Variables

```bash
# .env.local (never committed)
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_ROLE_KEY=eyJ...  # server-side only

# Payments
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
PAYPAL_CLIENT_ID=...
PAYPAL_CLIENT_SECRET=...

# Email
RESEND_API_KEY=re_...
EMAIL_FROM=hola@refugioanimal.com.py
EMAIL_FROM_NAME=Refugio Animal Paraguay

# App
NEXT_PUBLIC_APP_URL=https://refugioanimal.com.py
```

---

## Tech Stack Summary

| Layer | Technology | Reason |
|-------|-----------|--------|
| Framework | Next.js 14 App Router | RSC, Server Actions, file-based routing |
| Backend | Supabase | DB + Auth + Storage + Realtime in one |
| Styling | Tailwind CSS + shadcn/ui + cva | Utility-first with typed variants |
| State | Zustand (client) + RSC (server) | Minimal, no over-engineering |
| Forms | React Hook Form + Zod | Type-safe validation with good DX |
| i18n | next-intl | es-PY + Guaraní support |
| Email | Resend | ANBI receipts, confirmations |
| Payments | Stripe + PayPal | EU donors (iDEAL, SEPA) + international |
| Background | Supabase Edge Functions | Recurring donation checks, reminders |
| Monitoring | Sentry (errors) | Production error tracking |

---

*Last updated: 2026-03-25*
