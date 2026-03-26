---
task: T02
story: S02
epic: EPIC-2
title: Implement approval and rejection Server Actions
status: ready
priority: high
agent_type: fullstack
created: 2026-03-25T17:13:26.727969
---

# T02: Implement approval and rejection Server Actions

## Description

Implement the staff-facing review Server Actions in `src/app/actions/adoption-review.ts`. The actions `markUnderReview`, `approveApplication`, and `rejectApplication` update the `adoption_applications` row status, set `reviewer_id`, `reviewed_at`, and optional `reviewer_notes`. Then wire action buttons into the detail page built in T01 via a `ReviewActions` Client Component.

## Context

- Next.js 14 App Router — Server Actions with `'use server'` directive, NOT API routes
- Supabase-only backend — raw queries, no ORM
- Auth: `(await supabase.auth.getUser()).data.user?.id` — NOT deprecated `supabase.auth.user()?.id`
- Role guard: only `staff` and `admin` may call these actions — verify via `profiles.role`
- CSS: Tailwind CSS 3.4.19 PINNED — use CSS vars, NOT hardcoded colors (semantic green/red for approve/reject buttons is acceptable)
- `rejectApplication` requires a `notes` string — notes are optional for approval

## Files to create / modify

```
src/app/actions/adoption-review.ts          # New — Server Actions
src/app/admin/adopciones/[id]/ReviewActions.tsx  # New — Client Component with forms
src/app/admin/adopciones/[id]/page.tsx      # Modify — replace T01 placeholder comment
```

## Database columns expected

These columns must exist on `adoption_applications` (from S01/T01 migration):

```
reviewer_id    uuid REFERENCES profiles(id)
reviewed_at    timestamptz
reviewer_notes text
```

---

## Files to create

### `src/app/actions/adoption-review.ts`

```typescript
'use server'

import { redirect } from 'next/navigation'
import { createServerClient } from '@/lib/supabase/server'

type ReviewResult = { error: string }

async function getReviewerOrThrow() {
  const supabase = await createServerClient()

  const { data: { user }, error: authError } = await supabase.auth.getUser()
  if (authError || !user) {
    return { supabase: null, reviewerId: null, error: 'Debe iniciar sesión.' }
  }

  const { data: profile } = await supabase
    .from('profiles')
    .select('role')
    .eq('id', user.id)
    .single()

  if (!profile || !['staff', 'admin'].includes(profile.role)) {
    return { supabase: null, reviewerId: null, error: 'Sin autorización.' }
  }

  return { supabase, reviewerId: user.id, error: null }
}

export async function markUnderReview(
  applicationId: string,
): Promise<ReviewResult | never> {
  const { supabase, reviewerId, error } = await getReviewerOrThrow()
  if (error || !supabase) return { error: error! }

  const { error: updateError } = await supabase
    .from('adoption_applications')
    .update({
      status: 'under_review',
      reviewer_id: reviewerId,
      reviewed_at: new Date().toISOString(),
    })
    .eq('id', applicationId)

  if (updateError) {
    return { error: 'Error al actualizar el estado. Intente de nuevo.' }
  }

  redirect(`/admin/adopciones/${applicationId}`)
}

export async function approveApplication(
  applicationId: string,
  notes?: string,
): Promise<ReviewResult | never> {
  const { supabase, reviewerId, error } = await getReviewerOrThrow()
  if (error || !supabase) return { error: error! }

  const { error: updateError } = await supabase
    .from('adoption_applications')
    .update({
      status: 'approved',
      reviewer_id: reviewerId,
      reviewed_at: new Date().toISOString(),
      reviewer_notes: notes ?? null,
    })
    .eq('id', applicationId)

  if (updateError) {
    return { error: 'Error al aprobar la solicitud. Intente de nuevo.' }
  }

  redirect(`/admin/adopciones/${applicationId}`)
}

export async function rejectApplication(
  applicationId: string,
  notes: string,
): Promise<ReviewResult | never> {
  if (!notes || notes.trim().length < 5) {
    return { error: 'Debe ingresar un motivo de rechazo (mínimo 5 caracteres).' }
  }

  const { supabase, reviewerId, error } = await getReviewerOrThrow()
  if (error || !supabase) return { error: error! }

  const { error: updateError } = await supabase
    .from('adoption_applications')
    .update({
      status: 'rejected',
      reviewer_id: reviewerId,
      reviewed_at: new Date().toISOString(),
      reviewer_notes: notes.trim(),
    })
    .eq('id', applicationId)

  if (updateError) {
    return { error: 'Error al rechazar la solicitud. Intente de nuevo.' }
  }

  redirect(`/admin/adopciones/${applicationId}`)
}
```

---

### `src/app/admin/adopciones/[id]/ReviewActions.tsx`

```typescript
'use client'

import { useTransition, useState } from 'react'
import {
  markUnderReview,
  approveApplication,
  rejectApplication,
} from '@/app/actions/adoption-review'
import type { AdoptionApplicationStatus } from '@/types/adoption'

interface ReviewActionsProps {
  applicationId: string
  currentStatus: AdoptionApplicationStatus
}

const TERMINAL_STATUSES: AdoptionApplicationStatus[] = ['approved', 'rejected', 'withdrawn']

export function ReviewActions({ applicationId, currentStatus }: ReviewActionsProps) {
  const [isPending, startTransition] = useTransition()
  const [error, setError] = useState<string | null>(null)
  const [notes, setNotes] = useState('')
  const [showRejectForm, setShowRejectForm] = useState(false)

  function handleAction(action: () => Promise<{ error: string } | never>) {
    startTransition(async () => {
      setError(null)
      const result = await action()
      if (result && 'error' in result) {
        setError(result.error)
      }
    })
  }

  if (TERMINAL_STATUSES.includes(currentStatus)) {
    return (
      <p className="text-sm text-[var(--text-tertiary)] mt-4">
        Esta solicitud ya fue procesada y no puede modificarse.
      </p>
    )
  }

  return (
    <div className="mt-8 space-y-4">
      {error && (
        <p className="text-sm text-[var(--color-error)] bg-red-50 px-4 py-3 rounded-lg">
          {error}
        </p>
      )}

      <div className="flex flex-wrap gap-3">
        {currentStatus === 'submitted' && (
          <button
            disabled={isPending}
            onClick={() => handleAction(() => markUnderReview(applicationId))}
            className="px-4 py-2 rounded-lg text-sm font-medium bg-[var(--color-primary)] text-white hover:opacity-90 disabled:opacity-50 transition-opacity"
          >
            {isPending ? 'Procesando...' : 'Iniciar revisión'}
          </button>
        )}

        {(currentStatus === 'submitted' || currentStatus === 'under_review') && (
          <>
            <button
              disabled={isPending}
              onClick={() =>
                handleAction(() => approveApplication(applicationId, notes || undefined))
              }
              className="px-4 py-2 rounded-lg text-sm font-medium bg-green-600 text-white hover:bg-green-700 disabled:opacity-50 transition-colors"
            >
              {isPending ? 'Procesando...' : 'Aprobar'}
            </button>

            <button
              disabled={isPending}
              onClick={() => setShowRejectForm((v) => !v)}
              className="px-4 py-2 rounded-lg text-sm font-medium bg-red-600 text-white hover:bg-red-700 disabled:opacity-50 transition-colors"
            >
              Rechazar
            </button>
          </>
        )}
      </div>

      {(currentStatus === 'submitted' || currentStatus === 'under_review') && (
        <div>
          <label
            htmlFor="reviewer-notes"
            className="block text-sm font-medium text-[var(--text-secondary)] mb-1"
          >
            Notas del revisor
            {showRejectForm && (
              <span className="text-[var(--color-error)] ml-1">*</span>
            )}
          </label>
          <textarea
            id="reviewer-notes"
            rows={3}
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder={
              showRejectForm
                ? 'Motivo de rechazo (requerido)'
                : 'Observaciones opcionales...'
            }
            className="w-full rounded-lg border border-[var(--border-default)] bg-[var(--bg-card)] px-3 py-2 text-sm text-[var(--text-primary)] placeholder:text-[var(--text-tertiary)] focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]"
          />
        </div>
      )}

      {showRejectForm && (
        <button
          disabled={isPending || notes.trim().length < 5}
          onClick={() => handleAction(() => rejectApplication(applicationId, notes))}
          className="px-4 py-2 rounded-lg text-sm font-medium bg-red-600 text-white hover:bg-red-700 disabled:opacity-50 transition-colors"
        >
          {isPending ? 'Procesando...' : 'Confirmar rechazo'}
        </button>
      )}
    </div>
  )
}
```

---

### Updated `src/app/admin/adopciones/[id]/page.tsx`

Replace the `{/* Approve/reject actions are implemented in T02 */}` comment with the `ReviewActions` import and usage:

```typescript
import { createServerClient } from '@/lib/supabase/server'
import { redirect, notFound } from 'next/navigation'
import Link from 'next/link'
import { ReviewActions } from './ReviewActions'
import type { AdoptionApplicationRow } from '@/types/adoption'

interface PageProps {
  params: { id: string }
}

export default async function AdoptionDetailPage({ params }: PageProps) {
  const supabase = await createServerClient()

  const { data: { user } } = await supabase.auth.getUser()
  if (!user) redirect('/login')

  const { data: profile } = await supabase
    .from('profiles')
    .select('role')
    .eq('id', user.id)
    .single()

  if (!profile || !['staff', 'admin'].includes(profile.role)) {
    redirect('/')
  }

  const { data: application } = await supabase
    .from('adoption_applications')
    .select('*')
    .eq('id', params.id)
    .single<AdoptionApplicationRow>()

  if (!application) notFound()

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <Link
        href="/admin/adopciones"
        className="text-sm text-[var(--text-tertiary)] hover:text-[var(--text-primary)] mb-6 inline-block"
      >
        ← Volver a solicitudes
      </Link>
      <h1 className="text-2xl font-bold text-[var(--text-primary)] mb-2">
        Solicitud de Adopción
      </h1>
      <p className="text-xs text-[var(--text-tertiary)] mb-6">ID: {application.id}</p>

      <div className="bg-[var(--bg-card)] rounded-xl p-6 space-y-4 border border-[var(--border-default)]">
        <pre className="text-xs text-[var(--text-secondary)] overflow-auto">
          {JSON.stringify(application.data, null, 2)}
        </pre>
      </div>

      <ReviewActions
        applicationId={application.id}
        currentStatus={application.status}
      />
    </div>
  )
}
```

---

## Acceptance Criteria

- [ ] `markUnderReview` sets `status = 'under_review'`, `reviewer_id`, `reviewed_at`
- [ ] `approveApplication` sets `status = 'approved'`, `reviewer_id`, `reviewed_at`, optional `reviewer_notes`
- [ ] `rejectApplication` sets `status = 'rejected'`, `reviewer_id`, `reviewed_at`, required `reviewer_notes`
- [ ] `rejectApplication` returns `{ error: string }` if `notes` is blank or < 5 chars — does not call Supabase
- [ ] All three actions verify `profiles.role` is `staff` or `admin` — return `{ error }` if not
- [ ] Auth uses `(await supabase.auth.getUser()).data.user?.id` — no deprecated API
- [ ] `redirect()` called after all error-return branches, outside any try/catch block
- [ ] Detail page shows action buttons only for non-terminal statuses
- [ ] Terminal statuses (`approved`, `rejected`, `withdrawn`) render a read-only message
- [ ] `ReviewActions` uses `useTransition` — button shows "Procesando..." during pending state
- [ ] Error shown inline — no `alert()` or `window.confirm()`
- [ ] TypeScript: no type errors in any file

## Implementation Notes

- `getReviewerOrThrow` is an internal helper (not exported) that consolidates the auth + role check shared by all three actions. This avoids repeating 8 lines of guard logic in each action.
- `redirect()` from `next/navigation` throws internally — it must live after all error-return branches, outside any try/catch. The current structure guarantees this: early returns handle errors, `redirect()` is always the last statement.
- `useTransition` is used instead of a `useState<boolean>` loading flag — it integrates with React's concurrent features and correctly defers the re-render until the Server Action resolves.
- The `notes` textarea serves double duty: optional notes for approval, required notes for rejection. `showRejectForm` toggles the confirmation button and the required indicator on the label.
- `TERMINAL_STATUSES` is a named constant array — avoids repeating the three literal strings in the guard condition.

## Related

- Depends on: S02/T01 (detail page scaffold, `adoption_applications` table with `reviewer_id`/`reviewed_at`/`reviewer_notes` columns)
- Part of: S02 — Application Review Workflow
