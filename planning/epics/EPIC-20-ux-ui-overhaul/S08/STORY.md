# [S08] WhatsApp Integration & Accessibility Fixes — RAP-178

## Story

As a **Paraguayan visitor**, I want a WhatsApp button visible on every page so that I can contact the shelter through my preferred communication channel.

As a **visitor using assistive technology**, I want the site to meet WCAG AA accessibility standards so that I can navigate and use all features.

## Context

WhatsApp is the primary communication channel for Paraguayan users. The UX principles mandate a floating WhatsApp button on every page. Currently there is zero WhatsApp integration. Additionally, several accessibility issues were identified in the audit: missing `aria-describedby` on form errors, no `inputMode` attributes, `lang="es"` instead of `es-PY`, and all images using `unoptimized` bypassing Next.js optimization.

## Acceptance Criteria

### WhatsApp Floating Button
- [ ] Global `WhatsAppFab` component added to `layout.tsx`
- [ ] Fixed position: bottom-right corner, above mobile safe area
- [ ] WhatsApp green icon (SVG, not emoji)
- [ ] On click: opens `https://wa.me/{PHONE_NUMBER}?text={PREFILLED_MESSAGE}` in new tab
- [ ] Phone number configurable via `NEXT_PUBLIC_WHATSAPP_NUMBER` env var
- [ ] Default pre-filled message: "Hola! Me gustaria obtener informacion sobre el Refugio Animal Paraguay."
- [ ] Button has proper aria-label: "Contactar por WhatsApp"
- [ ] Button has subtle pulse animation on first load to draw attention
- [ ] Z-index above all content but below modals
- [ ] Responsive: slightly smaller on mobile, properly positioned

### Contact Page WhatsApp
- [ ] Contact page prominently displays WhatsApp as the primary contact method
- [ ] WhatsApp number displayed with click-to-chat link
- [ ] Email form is secondary: "Tambien podes escribirnos por email"

### Accessibility Fixes
- [ ] All form inputs with validation errors have `aria-describedby` linking to error message `id`
- [ ] All form inputs have `aria-invalid={true}` when in error state
- [ ] Phone inputs have `inputMode="tel"`
- [ ] Email inputs have `inputMode="email"`
- [ ] Error messages have `role="alert"` for screen reader announcement
- [ ] `lang="es-PY"` on HTML root (not `es`)
- [ ] All `<Image>` components: remove `unoptimized` prop where possible, add `sizes` attribute for responsive loading
- [ ] For images that must remain unoptimized (external URLs): add explicit `width`/`height` to prevent CLS
- [ ] Custom 404 page (`src/app/not-found.tsx`): branded, Spanish, with navigation back to home and animals
- [ ] Focus styles visible on all interactive elements (`:focus-visible` ring)
- [ ] Color contrast: verify all text meets 4.5:1 ratio against new color palette

### Image Optimization
- [ ] Remove `unoptimized` from `<Image>` components where the image source allows optimization
- [ ] Add `sizes` prop: `sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 25vw"` for grid images
- [ ] Hero images: `priority` prop for above-the-fold loading
- [ ] Thumbnail images: explicit small dimensions to avoid large downloads

## Technical Notes

- WhatsApp deep link format: `https://wa.me/595XXXXXXXXX?text=URL_ENCODED_MESSAGE`
- The WhatsApp number is TBD — use env var with a sensible fallback (or hide button if not configured)
- `WhatsAppFab` component: `src/components/WhatsAppFab.tsx`
- Custom 404: Next.js App Router uses `src/app/not-found.tsx`
- Image optimization: external URLs (from API) need `remotePatterns` config in `next.config.mjs`

## Definition of Done

- [ ] WhatsApp button visible on every page
- [ ] WhatsApp button functional with configurable phone number
- [ ] Contact page shows WhatsApp as primary channel
- [ ] All form accessibility issues fixed (aria-describedby, inputMode, role="alert")
- [ ] `lang="es-PY"` on HTML root
- [ ] Custom 404 page in Spanish
- [ ] Image optimization applied where possible
- [ ] Lighthouse Accessibility score 90+
- [ ] Deployed to staging

## Story Points: 5
