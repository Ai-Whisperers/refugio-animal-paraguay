---
task: T01
story: S04
epic: EPIC-2
title: Generate adoption contract PDF via Supabase Edge Function
status: ready
priority: medium
agent_type: fullstack
created: 2026-03-25T17:13:26.728467
---

# T01: Generate adoption contract PDF via Supabase Edge Function

## Description

Implement a Supabase Edge Function `generate-adoption-contract` that generates a PDF adoption contract when an application is approved. The function uses **`@react-pdf/renderer`** compiled to Deno-compatible output via an npm specifier, renders the contract template, and uploads the result to Supabase Storage. The uploaded PDF URL is then stored back on the `adoption_applications` row in a `contract_pdf_url` column.

## Context

- Supabase Edge Function (Deno) — triggered via HTTP call from `approveApplication` Server Action (S02/T02) after status update succeeds
- PDF generation: **`@react-pdf/renderer`** — renders React component tree to PDF bytes
- Storage: Supabase Storage bucket `adoption-contracts` — private, signed URLs for download
- No external PDF service — generation happens inside the Edge Function
- CSS: N/A — PDF styling uses `@react-pdf/renderer` StyleSheet API
- The contract must be in Spanish and include all adopter + animal data from the JSONB `data` column
- `contract_pdf_url` column added to `adoption_applications` in this task's migration

## Files to create

```
supabase/functions/generate-adoption-contract/index.ts    # Edge Function
supabase/functions/generate-adoption-contract/contract-template.tsx  # PDF React component
supabase/migrations/YYYYMMDD_add_contract_pdf_url.sql    # Migration
```

---

## Files to create

### `supabase/migrations/YYYYMMDD_add_contract_pdf_url.sql`

```sql
ALTER TABLE adoption_applications
  ADD COLUMN IF NOT EXISTS contract_pdf_url text,
  ADD COLUMN IF NOT EXISTS contract_generated_at timestamptz;
```

---

### `supabase/functions/generate-adoption-contract/contract-template.tsx`

```typescript
/** @jsxImportSource https://esm.sh/react@18 */
import React from 'https://esm.sh/react@18'
import {
  Document,
  Page,
  Text,
  View,
  StyleSheet,
} from 'https://esm.sh/@react-pdf/renderer@3'

const styles = StyleSheet.create({
  page: {
    padding: 48,
    fontSize: 11,
    fontFamily: 'Helvetica',
    color: '#1a1a1a',
  },
  title: {
    fontSize: 18,
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 11,
    textAlign: 'center',
    color: '#555',
    marginBottom: 32,
  },
  section: {
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 12,
    fontWeight: 'bold',
    marginBottom: 6,
    borderBottomWidth: 1,
    borderBottomColor: '#ddd',
    paddingBottom: 4,
  },
  row: {
    flexDirection: 'row',
    marginBottom: 4,
  },
  label: {
    width: '40%',
    color: '#555',
  },
  value: {
    width: '60%',
  },
  clause: {
    marginBottom: 8,
    lineHeight: 1.5,
  },
  signatureSection: {
    marginTop: 48,
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  signatureBlock: {
    width: '45%',
    borderTopWidth: 1,
    borderTopColor: '#1a1a1a',
    paddingTop: 8,
  },
  footer: {
    position: 'absolute',
    bottom: 32,
    left: 48,
    right: 48,
    fontSize: 9,
    color: '#999',
    textAlign: 'center',
  },
})

export interface ContractData {
  applicationId: string
  generatedAt: string
  adopter: {
    fullName: string
    email: string
    phone: string
    identityType: string
    identityNumber: string
  }
  address: {
    street: string
    city: string
    department: string
    country: string
  }
}

interface ContractDocumentProps {
  data: ContractData
}

export function ContractDocument({ data }: ContractDocumentProps) {
  return (
    <Document>
      <Page size="A4" style={styles.page}>
        <Text style={styles.title}>CONTRATO DE ADOPCIÓN RESPONSABLE</Text>
        <Text style={styles.subtitle}>Refugio Animal Paraguay</Text>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Datos del Adoptante</Text>
          <View style={styles.row}>
            <Text style={styles.label}>Nombre completo:</Text>
            <Text style={styles.value}>{data.adopter.fullName}</Text>
          </View>
          <View style={styles.row}>
            <Text style={styles.label}>Documento:</Text>
            <Text style={styles.value}>
              {data.adopter.identityType.toUpperCase()} {data.adopter.identityNumber}
            </Text>
          </View>
          <View style={styles.row}>
            <Text style={styles.label}>Email:</Text>
            <Text style={styles.value}>{data.adopter.email}</Text>
          </View>
          <View style={styles.row}>
            <Text style={styles.label}>Teléfono:</Text>
            <Text style={styles.value}>{data.adopter.phone}</Text>
          </View>
          <View style={styles.row}>
            <Text style={styles.label}>Dirección:</Text>
            <Text style={styles.value}>
              {data.address.street}, {data.address.city}, {data.address.department}
            </Text>
          </View>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Compromisos del Adoptante</Text>
          <Text style={styles.clause}>
            1. El adoptante se compromete a brindar al animal adoptado atención veterinaria
            adecuada, incluyendo vacunaciones anuales, desparasitación y atención en caso de
            enfermedad o lesión.
          </Text>
          <Text style={styles.clause}>
            2. El adoptante se compromete a no ceder, vender ni abandonar al animal bajo
            ninguna circunstancia. En caso de no poder continuar con el cuidado del animal,
            deberá contactar al Refugio Animal Paraguay para coordinar su retorno.
          </Text>
          <Text style={styles.clause}>
            3. El adoptante autoriza al Refugio Animal Paraguay a realizar visitas de
            seguimiento domiciliario durante los primeros 12 meses post-adopción.
          </Text>
          <Text style={styles.clause}>
            4. El adoptante se compromete a mantener al animal en condiciones de bienestar,
            con alimentación adecuada, espacio suficiente y trato digno.
          </Text>
        </View>

        <View style={styles.signatureSection}>
          <View style={styles.signatureBlock}>
            <Text>Firma del Adoptante</Text>
            <Text style={{ marginTop: 4, color: '#555' }}>{data.adopter.fullName}</Text>
            <Text style={{ marginTop: 2, color: '#555', fontSize: 10 }}>
              {data.adopter.identityType.toUpperCase()} {data.adopter.identityNumber}
            </Text>
          </View>
          <View style={styles.signatureBlock}>
            <Text>Por el Refugio Animal Paraguay</Text>
            <Text style={{ marginTop: 4, color: '#555' }}>Representante Legal</Text>
          </View>
        </View>

        <Text style={styles.footer}>
          Contrato N°: {data.applicationId} | Generado: {data.generatedAt} |
          Este documento tiene valor legal conforme a la legislación paraguaya vigente.
        </Text>
      </Page>
    </Document>
  )
}
```

---

### `supabase/functions/generate-adoption-contract/index.ts`

```typescript
import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'
import { renderToBuffer } from 'https://esm.sh/@react-pdf/renderer@3'
import React from 'https://esm.sh/react@18'
import { ContractDocument, type ContractData } from './contract-template.tsx'

const SUPABASE_URL = Deno.env.get('SUPABASE_URL')!
const SUPABASE_SERVICE_ROLE_KEY = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
const STORAGE_BUCKET = 'adoption-contracts'

interface RequestBody {
  applicationId: string
}

serve(async (req) => {
  try {
    const { applicationId }: RequestBody = await req.json()

    if (!applicationId) {
      return new Response(JSON.stringify({ error: 'applicationId required' }), {
        status: 400,
        headers: { 'Content-Type': 'application/json' },
      })
    }

    const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

    // Fetch the approved application
    const { data: application, error: fetchError } = await supabase
      .from('adoption_applications')
      .select('id, status, data')
      .eq('id', applicationId)
      .single()

    if (fetchError || !application) {
      return new Response(JSON.stringify({ error: 'Application not found' }), {
        status: 404,
        headers: { 'Content-Type': 'application/json' },
      })
    }

    if (application.status !== 'approved') {
      return new Response(
        JSON.stringify({ error: 'Contract can only be generated for approved applications' }),
        { status: 422, headers: { 'Content-Type': 'application/json' } },
      )
    }

    const adopter = application.data.adopter
    const address = application.data.address

    const contractData: ContractData = {
      applicationId: application.id,
      generatedAt: new Date().toLocaleDateString('es-PY'),
      adopter: {
        fullName: adopter?.fullName ?? 'Sin nombre',
        email: adopter?.email ?? '',
        phone: adopter?.phone ?? '',
        identityType: adopter?.identityType ?? 'cedula',
        identityNumber: adopter?.identityNumber ?? '',
      },
      address: {
        street: address?.street ?? '',
        city: address?.city ?? '',
        department: address?.department ?? '',
        country: 'PY',
      },
    }

    // Render PDF to buffer
    const pdfBuffer = await renderToBuffer(
      React.createElement(ContractDocument, { data: contractData }),
    )

    // Upload to Supabase Storage
    const fileName = `${applicationId}/contract.pdf`
    const { error: uploadError } = await supabase.storage
      .from(STORAGE_BUCKET)
      .upload(fileName, pdfBuffer, {
        contentType: 'application/pdf',
        upsert: true,
      })

    if (uploadError) {
      console.error('Storage upload failed', uploadError)
      return new Response(JSON.stringify({ error: 'PDF upload failed' }), {
        status: 500,
        headers: { 'Content-Type': 'application/json' },
      })
    }

    // Get a signed URL (valid 1 year)
    const { data: signedUrl } = await supabase.storage
      .from(STORAGE_BUCKET)
      .createSignedUrl(fileName, 60 * 60 * 24 * 365)

    // Store URL back on the application row
    await supabase
      .from('adoption_applications')
      .update({
        contract_pdf_url: signedUrl?.signedUrl ?? null,
        contract_generated_at: new Date().toISOString(),
      })
      .eq('id', applicationId)

    return new Response(
      JSON.stringify({ url: signedUrl?.signedUrl }),
      { status: 200, headers: { 'Content-Type': 'application/json' } },
    )
  } catch (err) {
    console.error('generate-adoption-contract failed', err)
    return new Response(JSON.stringify({ error: 'Internal server error' }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' },
    })
  }
})
```

---

## Supabase Storage bucket setup (manual prerequisite)

In Supabase dashboard → Storage:

1. Create bucket `adoption-contracts`
2. Set as **private** (not public)
3. RLS policy — allow service role only:
   ```sql
   CREATE POLICY "Service role only"
     ON storage.objects FOR ALL
     USING (auth.role() = 'service_role')
     WITH CHECK (auth.role() = 'service_role');
   ```

---

## Calling the Edge Function from the approve Server Action

In `src/app/actions/adoption-review.ts`, after the status update succeeds, trigger the contract generation:

```typescript
// After successful status update to 'approved':
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const serviceKey = process.env.SUPABASE_SERVICE_ROLE_KEY!

await fetch(`${supabaseUrl}/functions/v1/generate-adoption-contract`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${serviceKey}`,
  },
  body: JSON.stringify({ applicationId }),
})
// Fire-and-forget — do not await or block the redirect on PDF generation
```

---

## Acceptance Criteria

- [ ] Migration adds `contract_pdf_url text` and `contract_generated_at timestamptz` to `adoption_applications`
- [ ] Edge Function deploys: `supabase functions deploy generate-adoption-contract`
- [ ] Returns 422 if application status is not `approved`
- [ ] PDF contains adopter name, identity document, address, and four commitment clauses
- [ ] PDF uploaded to `adoption-contracts/{applicationId}/contract.pdf` in Supabase Storage
- [ ] `contract_pdf_url` updated on the `adoption_applications` row after upload
- [ ] Signed URL is valid for 1 year
- [ ] TypeScript: no type errors in either file

## Implementation Notes

- **`renderToBuffer`** is the server-side render method in `@react-pdf/renderer` — it returns a `Uint8Array` suitable for Storage upload.
- **Fire-and-forget from Server Action** — PDF generation is asynchronous and non-blocking. The `approveApplication` Server Action triggers it and redirects immediately. If generation fails, the `contract_pdf_url` column remains null and the admin can re-trigger manually.
- **`upsert: true`** in the storage upload — allows re-generating the contract without deleting the old file first.
- **Service role key in Server Action** — `SUPABASE_SERVICE_ROLE_KEY` is a server-only env var. It must NOT be exposed to the client. The `approveApplication` Server Action runs server-side, so this is safe.
- **Signed URL expiry** — 1 year is reasonable for adoption contract downloads. If longer persistence is needed, regenerate the signed URL on demand from the detail page.

## Related

- Depends on: S02/T02 (`approveApplication` triggers this function), S01/T01 (`adoption_applications` table with JSONB `data`)
- T02 (same story) adds the digital acceptance signature workflow
- Part of: S04 — Adoption Contracts and Documents
