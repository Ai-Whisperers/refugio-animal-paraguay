---
task: T03
story: S03
epic: EPIC-1
title: Show photo gallery
status: ready
priority: medium
agent_type: frontend
created: 2026-03-25T17:13:26.726543
---

# T03: Show photo gallery

## Description

Build the `AnimalPhotoGallery` Client Component that displays a row of thumbnail images below the primary photo on the animal detail page. Clicking a thumbnail swaps the main displayed image. This is the only interactive element on the detail page — everything else is Server-rendered.

## Context

- Client Component (`'use client'`) — needs `useState` for selected photo state
- Thumbnails: max 6 photos from `photo_gallery_urls` array stored in Supabase Storage
- Photos served from Supabase Storage public bucket `animals-photos`
- CSS: Tailwind CSS 3.4.19 PINNED — use CSS vars, NOT hardcoded colors
- `next/image` required for all images — never `<img>` tags

## Files to create

### `src/components/animals/AnimalPhotoGallery.tsx`

```typescript
'use client'

import { useState } from 'react'
import Image from 'next/image'

interface AnimalPhotoGalleryProps {
  animalName: string
  photos: string[]
  primaryPhoto: string | null
}

const PLACEHOLDER_IMAGE = '/images/animal-placeholder.webp'
const MAX_GALLERY_PHOTOS = 6

export function AnimalPhotoGallery({ animalName, photos, primaryPhoto }: AnimalPhotoGalleryProps) {
  const allPhotos = [
    ...(primaryPhoto ? [primaryPhoto] : []),
    ...photos.filter((url) => url !== primaryPhoto),
  ].slice(0, MAX_GALLERY_PHOTOS)

  const [selectedIndex, setSelectedIndex] = useState(0)
  const selectedPhoto = allPhotos[selectedIndex] ?? PLACEHOLDER_IMAGE

  if (allPhotos.length <= 1) return null

  return (
    <div>
      {/* Main selected photo */}
      <div className="relative aspect-[4/3] rounded-xl overflow-hidden mb-3 bg-[var(--bg-skeleton)]">
        <Image
          src={selectedPhoto}
          alt={`Foto ${selectedIndex + 1} de ${animalName}`}
          fill
          sizes="(max-width: 768px) 100vw, 50vw"
          className="object-cover"
        />
      </div>

      {/* Thumbnail strip */}
      <div className="flex gap-2 overflow-x-auto pb-1">
        {allPhotos.map((url, idx) => (
          <button
            key={url}
            onClick={() => setSelectedIndex(idx)}
            aria-label={`Ver foto ${idx + 1} de ${animalName}`}
            aria-pressed={idx === selectedIndex}
            className={`
              relative flex-shrink-0 w-16 h-16 rounded-lg overflow-hidden border-2 transition-all
              ${idx === selectedIndex
                ? 'border-[var(--color-primary)] opacity-100'
                : 'border-[var(--border-subtle)] opacity-70 hover:opacity-100 hover:border-[var(--color-primary)]'
              }
            `}
          >
            <Image
              src={url}
              alt={`Miniatura ${idx + 1}`}
              fill
              sizes="64px"
              className="object-cover"
            />
          </button>
        ))}
      </div>
    </div>
  )
}
```

## Acceptance Criteria

- [ ] `AnimalPhotoGallery` is a `'use client'` component using `useState`
- [ ] Returns `null` when there is only one or zero photos (no gallery needed)
- [ ] Primary photo (`photo_primary_url`) always appears first in the thumbnail strip
- [ ] Clicking a thumbnail updates the main displayed image
- [ ] Max 6 photos shown in gallery (additional photos silently truncated)
- [ ] Active thumbnail has a visible border highlight using `--color-primary`
- [ ] Each thumbnail button has `aria-pressed` for accessibility
- [ ] All images use `next/image` with `fill` and appropriate `sizes`
- [ ] All CSS uses CSS variable classes — no hardcoded Tailwind color utilities
- [ ] TypeScript: no type errors

## Implementation Notes

- `allPhotos` deduplicates primary photo from gallery array to avoid showing it twice — filter uses `!== primaryPhoto` URL comparison
- `MAX_GALLERY_PHOTOS = 6` is a named constant — change here to affect the whole component
- The main selected photo lives in the same component as thumbnails (`AnimalDetailView` slots this in below the static primary photo — so at small screen sizes users see both)
- `overflow-x-auto` on the thumbnail strip handles mobile when there are many photos
- Supabase Storage URLs are public and served directly — no signed URL needed for `animals-photos` bucket

## Related

- Depends on: T01 (page), T02 (AnimalDetailView imports and renders this)
- Photos stored in: `animals-photos` Supabase Storage bucket (EPIC-1/S04/T01)
- Part of: S03 — Animal Detail Page
