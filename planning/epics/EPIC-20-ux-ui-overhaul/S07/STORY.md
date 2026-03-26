# [S07] Animal Detail & Adoption Flow Overhaul — RAP-177

## Story

As an **adopter viewing an animal's profile**, I want the adoption CTA to always be visible and the form to save my progress so that I don't lose data on a slow connection and can easily start the process.

## Context

The detail page buries the "Apply to Adopt" button below all content (below the fold on mobile). The adoption form is a single page with no localStorage persistence — a 3G connection drop means starting over. The UX principles require a sticky bottom CTA, photo gallery with swipe/lightbox, multi-step form, and localStorage persistence.

## Acceptance Criteria

### Animal Detail Page
- [ ] Sticky bottom CTA bar on mobile: "Quiero Adoptar a [name]" — fixed to bottom of viewport, `bg-white border-t shadow-lg`
- [ ] Sticky bar only shows when animal is available
- [ ] Photo gallery: clicking main photo opens a modal/lightbox with all photos
- [ ] Gallery supports swipe on mobile (basic CSS scroll-snap or lightweight lib)
- [ ] Thumbnail strip is clickable — changes main photo
- [ ] Detail labels in Spanish: "Especie", "Edad", "Tamano", "Sexo", "Llego al refugio"
- [ ] Date formatted with `es-PY` locale
- [ ] Breadcrumb in Spanish: "Animales / [name]"
- [ ] WhatsApp button: "Preguntar por [name]" — deep link to WhatsApp with pre-filled message

### Adoption Form Overhaul
- [ ] Multi-step form with progress bar: "Paso 1 de 3"
- [ ] Step 1: Personal info (name, email, phone)
- [ ] Step 2: About your home (message/motivation, living situation — can be simple textarea for now)
- [ ] Step 3: Consent & submit (GDPR consent, review summary, submit)
- [ ] Progress bar shows current step visually
- [ ] "Anterior" button always available (saves current step data)
- [ ] "Siguiente" validates current step before advancing
- [ ] **localStorage persistence**: all form fields auto-save to localStorage keyed by animal ID
- [ ] On page load: restore saved form data from localStorage
- [ ] On successful submit: clear localStorage for this form
- [ ] Submit button: "Enviar Solicitud" with loading state "Enviando..."
- [ ] Success message: warm tone, mentions the animal by name, mentions WhatsApp confirmation

### Optimistic UI
- [ ] On submit click: button immediately shows loading state
- [ ] Form fields become disabled during submission
- [ ] On success: smooth transition to success state (no page jump)

## Technical Notes

- Sticky bottom bar: `fixed bottom-0 inset-x-0 p-4 bg-white/95 backdrop-blur-sm border-t z-20`
- Hide sticky bar when user scrolls to the actual CTA button area (IntersectionObserver)
- localStorage key format: `refugio_adoption_${animalId}`
- Photo gallery: CSS scroll-snap is sufficient, no need for heavyweight libraries
- Multi-step form: use a `step` state variable, render different fieldsets per step

## Definition of Done

- [ ] Sticky CTA visible on mobile detail page
- [ ] Photo gallery with lightbox interaction
- [ ] Multi-step adoption form with progress bar
- [ ] localStorage persistence verified (fill form, refresh, data restored)
- [ ] All strings in Spanish
- [ ] Mobile responsive
- [ ] Deployed to staging

## Story Points: 5
