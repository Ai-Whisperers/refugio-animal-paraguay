---
task: T02
story: S04
epic: EPIC-2
title: Implement digital contract acceptance and signature recording
status: ready
priority: medium
agent_type: fullstack
created: 2026-03-25T17:13:26.728528
---

# T02: Implement digital contract acceptance and signature recording

## Description

Implement a digital acceptance workflow for the adoption contract. When the adopter views their approved application, they see the generated contract (PDF from T01) and a signature capture form. On submission, a Server Action records the acceptance timestamp, full name confirmation, IP address, and user agent as the digital signature — then stores this in a `contract_signatures` table. No third-party e-signature SaaS — this uses a Supabase-native approach that is legally sufficient in Paraguay for non-notarized civil agreements.

## Context

- **No DocuSign, no HelloSign** — Supabase Storage + PostgreSQL acceptance record is the approach
- Next.js 14 App Router — Server Action for recording acceptance, Server Component for rendering the contract page
- Auth: adopter must be authenticated — their `user.id` is the legal link between identity and signature
- `contract_signatures` table stores: `application_id`, `adopter_id`, `accepted_at`, `full_name_confirmation`, `ip_address`, `user_agent`
- IP address collected server-side from Next.js request headers — NOT from the client
- The adopter types their full name to confirm identity (electronic equivalent of wet signature)
- CSS: Tailwind CSS 3.4.19 PINNED — use CSS vars, NOT hardcoded colors

## Files to create / modify

```
supabase/migrations/YYYYMMDD_create_contract_signatures.sql  # New table
src/app/actions/contract.ts                                   # Server Action
src/app/adopciones/[id]/contrato/page.tsx                    # Adopter-facing contract page
src/app/adopciones/[id]/contrato/SignatureForm.tsx           # Client Component
```

---

## Files to create

### `supabase/migrations/YYYYMMDD_create_contract_signatures.sql`

```sql
CREATE TABLE IF NOT EXISTS contract_signatures (
  id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  application_id uuid NOT NULL REFERENCES adoption_applications(id) ON DELETE CASCADE,
  adopter_id   uuid NOT NULL REFERENCES profiles(id),
  accepted_at  timestamptz NOT NULL DEFAULT now(),
  full_name_confirmation text NOT NULL,
  ip_address   inet,
  user_agent   text,
  UNIQUE (application_id)  -- One signature per contract
);

-- Only the adopter who owns the application can select their own signature
ALTER TABLE contract_signatures ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Adopter reads own signature"
  ON contract_signatures FOR SELECT
  USING (adopter_id = auth.uid());

-- Inserts handled server-side via service role — no direct client insert
CREATE POLICY "No direct client insert"
  ON contract_signatures FOR INSERT
  WITH CHECK (false);
```

---

### `src/app/actions/contract.ts`

```typescript
'use server'

import { headers } from 'next/headers'
import { redirect } from 'next/navigation'
import { createServerClient } from '@/lib/supabase/server'

type SignResult = { error: string }

export async function signAdoptionContract(
  applicationId: string,
  fullNameConfirmation: string,
): Promise<SignResult | never> {
  if (!fullNameConfirmation || fullNameConfirmation.trim().length < 3) {
    return { error: 'Debe ingresar su nombre completo para firmar.' }
  }

  const supabase = await createServerClient()

  const { data: { user }, error: authError } = await supabase.auth.getUser()
  if (authError || !user) {
    return { error: 'Debe iniciar sesión para firmar el contrato.' }
  }

  // Verify the application belongs to the authenticated user and is approved
  const { data: application } = await supabase
    .from('adoption_applications')
    .select('id, status, adopter_id, contract_pdf_url')
    .eq('id', applicationId)
    .single()

  if (!application) {
    return { error: 'Solicitud no encontrada.' }
  }

  if (application.adopter_id !== user.id) {
    return { error: 'No tiene permiso para firmar esta solicitud.' }
  }

  if (application.status !== 'approved') {
    return { error: 'Solo se puede firmar una solicitud aprobada.' }
  }

  if (!application.contract_pdf_url) {
    return { error: 'El contrato aún no ha sido generado. Intente en unos minutos.' }
  }

  // Check for duplicate signature
  const { data: existing } = await supabase
    .from('contract_signatures')
    .select('id')
    .eq('application_id', applicationId)
    .single()

  if (existing) {
    return { error: 'Este contrato ya fue firmado.' }
  }

  // Collect metadata server-side — never trust client-provided IP
  const headersList = headers()
  const ip = headersList.get('x-forwarded-for')?.split(',')[0]?.trim()
    ?? headersList.get('x-real-ip')
    ?? null
  const userAgent = headersList.get('user-agent') ?? null

  // Use service role for the insert (RLS blocks direct client insert)
  const { createClient } = await import('@supabase/supabase-js')
  const adminSupabase = createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!,
  )

  const { error: insertError } = await adminSupabase
    .from('contract_signatures')
    .insert({
      application_id: applicationId,
      adopter_id: user.id,
      full_name_confirmation: fullNameConfirmation.trim(),
      ip_address: ip,
      user_agent: userAgent,
    })

  if (insertError) {
    return { error: 'Error al registrar la firma. Intente de nuevo.' }
  }

  redirect(`/adopciones/${applicationId}/contrato/confirmacion`)
}
```

---

### `src/app/adopciones/[id]/contrato/SignatureForm.tsx`

```typescript
'use client'

import { useTransition, useState } from 'react'
import { signAdoptionContract } from '@/app/actions/contract'

interface SignatureFormProps {
  applicationId: string
  expectedName: string
}

export function SignatureForm({ applicationId, expectedName }: SignatureFormProps) {
  const [isPending, startTransition] = useTransition()
  const [nameInput, setNameInput] = useState('')
  const [error, setError] = useState<string | null>(null)

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    startTransition(async () => {
      setError(null)
      const result = await signAdoptionContract(applicationId, nameInput)
      if (result && 'error' in result) {
        setError(result.error)
      }
    })
  }

  const nameMatches = nameInput.trim().toLowerCase() === expectedName.toLowerCase()

  return (
    <form onSubmit={handleSubmit} className="mt-8 space-y-4">
      <div className="bg-[var(--bg-card)] rounded-xl p-6 border border-[var(--border-default)]">
        <h2 className="text-lg font-semibold text-[var(--text-primary)] mb-2">
          Firma electrónica
        </h2>
        <p className="text-sm text-[var(--text-secondary)] mb-4">
          Para completar el proceso, escriba su nombre completo exactamente como aparece en el contrato:
          <span className="font-medium text-[var(--text-primary)]"> {expectedName}</span>
        </p>

        <div>
          <label
            htmlFor="signature-name"
            className="block text-sm font-medium text-[var(--text-secondary)] mb-1"
          >
            Nombre completo
          </label>
          <input
            id="signature-name"
            type="text"
            value={nameInput}
            onChange={(e) => setNameInput(e.target.value)}
            placeholder="Escriba su nombre completo"
            autoComplete="name"
            className="w-full rounded-lg border border-[var(--border-default)] bg-[var(--bg-card)] px-3 py-2 text-sm text-[var(--text-primary)] placeholder:text-[var(--text-tertiary)] focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]"
          />
        </div>

        {error && (
          <p className="mt-3 text-sm text-[var(--color-error)]">{error}</p>
        )}
      </div>

      <button
        type="submit"
        disabled={isPending || !nameMatches}
        className="w-full px-4 py-3 rounded-lg text-sm font-medium bg-[var(--color-primary)] text-white hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed transition-opacity"
      >
        {isPending ? 'Registrando firma...' : 'Firmar contrato'}
      </button>

      <p className="text-xs text-[var(--text-tertiary)] text-center">
        Al firmar, acepta los términos del contrato de adopción responsable.
        Su firma electrónica incluye fecha, hora y datos de conexión.
      </p>
    </form>
  )
}
```

---

### `src/app/adopciones/[id]/contrato/page.tsx`

```typescript
import { createServerClient } from '@/lib/supabase/server'
import { redirect, notFound } from 'next/navigation'
import Link from 'next/link'
import { SignatureForm } from './SignatureForm'

interface PageProps {
  params: { id: string }
}

export default async function ContractPage({ params }: PageProps) {
  const supabase = await createServerClient()

  const { data: { user } } = await supabase.auth.getUser()
  if (!user) redirect('/login')

  const { data: application } = await supabase
    .from('adoption_applications')
    .select('id, status, adopter_id, data, contract_pdf_url')
    .eq('id', params.id)
    .single()

  if (!application) notFound()

  // Only the adopter who owns this application may view it
  if (application.adopter_id !== user.id) redirect('/')

  if (application.status !== 'approved') {
    redirect(`/adopciones/${params.id}`)
  }

  // Check if already signed
  const { data: existingSignature } = await supabase
    .from('contract_signatures')
    .select('accepted_at')
    .eq('application_id', params.id)
    .single()

  const adopterName: string = application.data?.adopter?.fullName ?? ''

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <Link
        href={`/adopciones/${params.id}`}
        className="text-sm text-[var(--text-tertiary)] hover:text-[var(--text-primary)] mb-6 inline-block"
      >
        ← Volver
      </Link>

      <h1 className="text-2xl font-bold text-[var(--text-primary)] mb-2">
        Contrato de Adopción
      </h1>

      {existingSignature ? (
        <div className="mt-4 bg-green-50 border border-green-200 rounded-xl px-6 py-4">
          <p className="text-sm font-medium text-green-800">
            Contrato firmado el{' '}
            {new Date(existingSignature.accepted_at).toLocaleDateString('es-PY', {
              day: 'numeric',
              month: 'long',
              year: 'numeric',
            })}
          </p>
        </div>
      ) : (
        <>
          {application.contract_pdf_url ? (
            <div className="mt-4 mb-6">
              <a
                href={application.contract_pdf_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 text-sm text-[var(--color-primary)] hover:underline"
              >
                Ver contrato en PDF →
              </a>
            </div>
          ) : (
            <p className="mt-4 text-sm text-[var(--text-tertiary)]">
              El contrato está siendo generado. Recargue la página en unos minutos.
            </p>
          )}

          {application.contract_pdf_url && (
            <SignatureForm
              applicationId={application.id}
              expectedName={adopterName}
            />
          )}
        </>
      )}
    </div>
  )
}
```

---

## Acceptance Criteria

- [ ] Migration creates `contract_signatures` table with `UNIQUE (application_id)` constraint
- [ ] RLS policy prevents direct client insert — signature only inserted server-side via service role
- [ ] `signAdoptionContract` Server Action verifies `adopter_id === user.id` — no cross-user signing
- [ ] Returns `{ error }` if application is not `approved` or has no `contract_pdf_url` yet
- [ ] Returns `{ error }` if contract already signed (duplicate check before insert)
- [ ] IP address and user agent collected server-side via `next/headers` — not from client
- [ ] Submit button disabled until typed name matches `expectedName` (case-insensitive)
- [ ] Signed state shows formatted acceptance date — no form shown again
- [ ] `redirect('/adopciones/[id]/contrato/confirmacion')` called outside try/catch
- [ ] TypeScript: no type errors in any file

## Implementation Notes

- **Legal sufficiency (Paraguay)** — Paraguay's Ley N° 4017/10 on Electronic Documents and Signatures recognizes electronic signatures for private agreements. Recording the acceptance timestamp, full name confirmation, IP address, and user agent creates an audit trail sufficient for non-notarized adoption contracts.
- **Why service role for the insert** — The `contract_signatures` RLS policy blocks all direct client inserts. The Server Action runs server-side and uses `SUPABASE_SERVICE_ROLE_KEY` (a server-only env var, never exposed to the browser). This prevents adopters from signing contracts they don't own or forging signatures.
- **`headers()` from `next/headers`** — IP address must be collected server-side. `x-forwarded-for` is set by the reverse proxy/CDN. Taking only the first IP (`split(',')[0]`) avoids client-injected forged IPs in the forwarded chain.
- **Name matching** — The client-side match (`nameMatches`) is UX feedback only — the submit button disables until names match. The Server Action does NOT enforce exact name matching (names may have slight variations); it only requires a non-empty string ≥ 3 chars.
- **`redirect()` placement** — Called after all validation branches, outside any try/catch, as always.

## Related

- Depends on: S04/T01 (generates `contract_pdf_url`, adds `contract_pdf_url` column), S02/T02 (approves the application, which enables signing)
- Part of: S04 — Adoption Contracts and Documents
