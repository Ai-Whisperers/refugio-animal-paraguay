---
task: T02
story: S03
epic: EPIC-1
title: Display animal information
status: ready
priority: medium
agent_type: frontend
created: 2026-03-25T17:13:26.726458
---

# T02: Display animal information

## Description

Build the `AnimalDetailView` Server Component that renders all information about a single animal. Includes the primary photo, animal metadata (species, age, sex, weight, location), the adoption story description, and the "Quiero adoptarlo" CTA button that leads to the adoption request flow.

## Context

- Server Component (no `'use client'`) — data already fetched by the page
- CSS: Tailwind CSS 3.4.19 PINNED — use CSS vars, NOT hardcoded colors
- Status badge: show current status with color-coded label (available = green, reserved = yellow, adopted = gray)
- CTA button visible only when `status === 'available'`
- Photo gallery rendered by `AnimalPhotoGallery` component (T03) — slot it into the layout here

## Files to create

### `src/components/animals/AnimalDetailView.tsx`

```typescript
import Image from 'next/image'
import Link from 'next/link'
import { AnimalPhotoGallery } from './AnimalPhotoGallery'

interface AnimalDetailViewProps {
  animal: {
    id: string
    name: string
    species: string
    breed: string | null
    age_years: number
    age_months: number
    sex: string
    weight_kg: number | null
    status: string
    description: string | null
    intake_date: string | null
    intake_reason: string | null
    location: string | null
    microchip_number: string | null
    is_featured: boolean
    photo_primary_url: string | null
    photo_gallery_urls: string[] | null
  }
}

const SPECIES_LABELS: Record<string, string> = { dog: 'Perro', cat: 'Gato' }
const SEX_LABELS: Record<string, string> = { male: 'Macho', female: 'Hembra' }
const INTAKE_REASON_LABELS: Record<string, string> = {
  abandoned: 'Abandonado',
  rescue: 'Rescatado',
  surrendered: 'Entregado por dueño',
  stray: 'Callejero',
}
const STATUS_CONFIG: Record<string, { label: string; className: string }> = {
  available: { label: 'Disponible', className: 'bg-green-100 text-green-800' },
  reserved: { label: 'Reservado', className: 'bg-yellow-100 text-yellow-800' },
  adopted: { label: 'Adoptado', className: 'bg-gray-100 text-gray-600' },
  medical_hold: { label: 'En tratamiento médico', className: 'bg-blue-100 text-blue-800' },
}
const PLACEHOLDER_IMAGE = '/images/animal-placeholder.webp'

function formatAge(years: number, months: number): string {
  if (years === 0) return months <= 1 ? '1 mes' : `${months} meses`
  if (years === 1) return '1 año'
  return `${years} años`
}

export function AnimalDetailView({ animal }: AnimalDetailViewProps) {
  const statusConfig = STATUS_CONFIG[animal.status] ?? { label: animal.status, className: 'bg-gray-100 text-gray-600' }

  return (
    <div className="space-y-8">
      {/* Breadcrumb */}
      <nav className="text-sm text-[var(--text-secondary)]">
        <a href="/animales" className="hover:text-[var(--color-primary)] transition-colors">
          Animales en adopción
        </a>
        <span className="mx-2">›</span>
        <span className="text-[var(--text-primary)]">{animal.name}</span>
      </nav>

      {/* Main content grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Photo */}
        <div>
          <div className="relative aspect-[4/3] rounded-xl overflow-hidden bg-[var(--bg-skeleton)]">
            <Image
              src={animal.photo_primary_url ?? PLACEHOLDER_IMAGE}
              alt={`Foto de ${animal.name}`}
              fill
              sizes="(max-width: 768px) 100vw, 50vw"
              className="object-cover"
              priority
            />
            <span className={`absolute top-3 left-3 text-xs font-medium px-2 py-1 rounded-full ${statusConfig.className}`}>
              {statusConfig.label}
            </span>
          </div>

          {/* Photo gallery (T03) */}
          {animal.photo_gallery_urls && animal.photo_gallery_urls.length > 0 && (
            <div className="mt-3">
              <AnimalPhotoGallery
                animalName={animal.name}
                photos={animal.photo_gallery_urls}
                primaryPhoto={animal.photo_primary_url}
              />
            </div>
          )}
        </div>

        {/* Info */}
        <div className="space-y-6">
          <div>
            <h1 className="text-3xl font-bold text-[var(--text-primary)]">{animal.name}</h1>
            <p className="text-lg text-[var(--text-secondary)] mt-1">
              {SPECIES_LABELS[animal.species] ?? animal.species}
              {animal.breed ? ` · ${animal.breed}` : ''}
            </p>
          </div>

          {/* Key stats */}
          <dl className="grid grid-cols-2 gap-4">
            {[
              { label: 'Sexo', value: SEX_LABELS[animal.sex] ?? animal.sex },
              { label: 'Edad', value: formatAge(animal.age_years, animal.age_months) },
              ...(animal.weight_kg ? [{ label: 'Peso', value: `${animal.weight_kg} kg` }] : []),
              ...(animal.location ? [{ label: 'Ubicación', value: animal.location }] : []),
              ...(animal.intake_reason ? [{ label: 'Ingresó por', value: INTAKE_REASON_LABELS[animal.intake_reason] ?? animal.intake_reason }] : []),
              ...(animal.microchip_number ? [{ label: 'Microchip', value: animal.microchip_number }] : []),
            ].map(({ label, value }) => (
              <div key={label} className="bg-[var(--bg-card)] rounded-lg p-3 border border-[var(--border-subtle)]">
                <dt className="text-xs text-[var(--text-tertiary)] uppercase tracking-wide">{label}</dt>
                <dd className="mt-1 text-sm font-medium text-[var(--text-primary)]">{value}</dd>
              </div>
            ))}
          </dl>

          {/* Description */}
          {animal.description && (
            <div>
              <h2 className="text-sm font-semibold text-[var(--text-primary)] uppercase tracking-wide mb-2">
                Historia
              </h2>
              <p className="text-[var(--text-secondary)] leading-relaxed">{animal.description}</p>
            </div>
          )}

          {/* CTA */}
          {animal.status === 'available' && (
            <Link
              href={`/adoptar/${animal.id}`}
              className="block w-full text-center py-3 px-6 bg-[var(--color-primary)] text-white font-semibold rounded-xl hover:opacity-90 transition-opacity"
            >
              Quiero adoptarlo
            </Link>
          )}

          {animal.status === 'reserved' && (
            <p className="text-sm text-center text-[var(--text-secondary)] bg-[var(--bg-card)] rounded-xl p-3 border border-[var(--border-subtle)]">
              Este animal ya tiene un proceso de adopción en curso.
            </p>
          )}
        </div>
      </div>
    </div>
  )
}
```

## Acceptance Criteria

- [ ] `AnimalDetailView` is a Server Component (no `'use client'`)
- [ ] Status badge shown with correct label and style for each status value
- [ ] "Quiero adoptarlo" CTA only appears when `status === 'available'`
- [ ] `status === 'reserved'` shows a "proceso en curso" message instead of CTA
- [ ] Age formatted in Spanish: "2 meses", "1 año", "3 años"
- [ ] Breadcrumb navigation links back to `/animales`
- [ ] `null` optional fields (weight, location, breed, microchip) are gracefully omitted from the stats grid
- [ ] `AnimalPhotoGallery` only rendered when `photo_gallery_urls` has entries
- [ ] Primary photo uses `priority` prop (above the fold — avoids LCP penalty)
- [ ] All CSS uses CSS variable classes — no hardcoded Tailwind color utilities

## Implementation Notes

- Status badge uses hardcoded Tailwind color classes for the semantic colors (green/yellow/gray/blue) — this is intentional since status colors are fixed and not theme-dependent
- CTA links to `/adoptar/[id]` — the adoption request flow (separate epic)
- The stats grid uses a dynamic array to skip null fields — avoids empty `<dd>` cells
- `AnimalPhotoGallery` is created in T03 and imported here

## Related

- Depends on: T01 (detail page fetches and passes animal data)
- Blocks: T03 (photo gallery is a sub-component used here)
- Part of: S03 — Animal Detail Page
