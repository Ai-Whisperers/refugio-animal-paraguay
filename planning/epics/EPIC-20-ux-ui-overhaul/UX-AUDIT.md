# UX/UI Forensic Audit — Refugio Animal Paraguay Frontend

**Date:** 2026-03-26
**Auditor:** Automated deep-dive against `docs/UX-PRINCIPLES.md`
**Scope:** All files in `frontend/src/` on `develop` branch
**Verdict:** The frontend is a functional English-language boilerplate that violates nearly every principle in the project's own UX guidelines. It needs a ground-up visual and linguistic overhaul before it represents a credible Paraguayan animal shelter.

---

## Severity Scale

| Level | Meaning |
|-------|---------|
| **CRITICAL** | Breaks trust, causes 404s, or contradicts core identity |
| **MAJOR** | Significant UX principle violation, degrades experience materially |
| **MODERATE** | Noticeable quality gap vs. what the guidelines mandate |
| **MINOR** | Polish item, not user-blocking |

---

## 1. Identity Crisis: Wrong Colors, Wrong Language, Wrong Tone

### 1.1 Color Palette Inversion — CRITICAL

**What the guidelines say:** Primary = `#E8622A` (warm orange, energy/hope), Secondary = `#2A7E62` (nature green)

**What the code does:** `tailwind.config.ts` defines `primary` as a green scale (`#16a34a` / Tailwind's `green-600`) and `accent` as an orange scale (`#f97316`). The entire identity is inverted. Every `bg-primary-600`, `text-primary-700`, `hover:bg-primary-700` across every component renders green where orange should be.

**Files affected:** `tailwind.config.ts` (source), then cascades into every `.tsx` file that uses `primary-*` or `accent-*` classes (all of them).

**Impact:** The site looks like a generic green SaaS product instead of a warm, inviting shelter. The warm orange that should say "hope and energy" is buried as a secondary accent.

### 1.2 Full English Hardcoding — CRITICAL

**What the guidelines say:** "Lenguaje Humano y Calido" in Spanish. `lang="es-PY"` on HTML root. Warm conversational Spanish tone throughout.

**What the code does:** Every single user-facing string is in English. A complete inventory:

| File | English Strings |
|------|----------------|
| `page.tsx` (home) | "Every Animal Deserves a Loving Home", "Refugio Animal Paraguay rescues, rehabilitates...", "Meet Our Animals", "Donate Now", "150+", "Animals Rescued", "80+", "Successful Adoptions", "50+", "Active Volunteers", "How You Can Help", "Adopt", "Give a rescued animal a forever home...", "Donate", "Your contribution helps us provide food...", "Volunteer", "Join our team of dedicated volunteers..." |
| `Navbar.tsx` | "Home", "Animals", "About", "Contact", "Donate", "Skip to main content" |
| `Footer.tsx` | "About Us", "Our Animals", "Contact", "Donate", "Volunteer", "Foster", "Shelter", "Support Us", "Giving animals a second chance at life...", "All rights reserved" |
| `animals/page.tsx` | "Animals Available for Adoption", "Meet our furry friends...", "All Species", "Dogs", "Cats", "Other", "Loading animals...", "Try Again", "No animals available right now...", "Previous", "Next", status labels ("New Arrival", "Available", "Adopted", etc.) |
| `animals/[id]/page.tsx` | "Animals", "About [name]", "Apply to Adopt [name]", "This animal is not currently available...", "Back to Animals", "Species", "Age", "Arrived", all status labels |
| `animals/[id]/apply/page.tsx` | "Adoption Application", "Fill in your details below...", "Full Name", "Email Address", "Phone Number", "Message", "Data Processing Consent", "Submit Application", "Submitting...", "Cancel", "Application Submitted!", "Thank you for your interest..." |
| `contact/page.tsx` | "Contact Us", "Have a question?...", "Send a Message", "Name", "Email", "Subject", "Message", "Send Message", "Sending...", "Message Sent!" |
| `layout.tsx` | metadata description in English, "Skip to main content" |

That's **100+ hardcoded English strings** in a site targeting Paraguayan users.

### 1.3 Tone Completely Wrong — MAJOR

**What the guidelines say:** Warm, personal. "Tu solicitud llego! Te confirmamos por WhatsApp en minutos" not "Solicitud enviada con exito". Use words like "mimos", "amiguito", "familia", "hogar", "amor". Avoid "mascota", "procesado", "usuario".

**What the code does:** Cold, corporate English. "Application Submitted!" with a confetti emoji. "We have received your application and will review it shortly." "Failed to load animals." "An unexpected error occurred." Even the animal cards say "dog" / "cat" instead of giving them personality.

### 1.4 HTML lang attribute — MODERATE

`layout.tsx` sets `lang="es"` (good intent) but guidelines specify `lang="es-PY"` (Paraguayan Spanish). The meta description is in English, which contradicts the lang tag and hurts SEO for the target market.

---

## 2. Broken Navigation: Pages That Don't Exist

### 2.1 Dead Links — CRITICAL

The `Navbar.tsx` links to `/about` and `/donate`. The `Footer.tsx` links to `/about`, `/donate`, `/volunteer`, and `/foster`. **None of these pages exist** in `src/app/`. Clicking them produces a Next.js 404 page.

**Dead link inventory:**
- `/about` — referenced in Navbar + Footer (2 places)
- `/donate` — referenced in Navbar + Footer + Homepage CTA (3 places)
- `/volunteer` — referenced in Footer (1 place)
- `/foster` — referenced in Footer (1 place)

This means **4 out of 5 navigation links in the footer** go nowhere. The homepage's second-most-prominent CTA ("Donate Now") goes to a 404. For an NGO that depends on donations, this is a conversion killer.

---

## 3. Missing WhatsApp Integration — CRITICAL

**What the guidelines say:** "Boton flotante de WhatsApp Business visible en **todas** las paginas". WhatsApp is THE communication channel for Paraguayan users. Confirmations go by WhatsApp first, email second.

**What the code does:** Zero WhatsApp integration anywhere. No floating button. No WhatsApp links. No mention of WhatsApp in any component. The contact page only has an email form.

**Impact:** The primary communication channel for the target demographic is completely absent.

---

## 4. Homepage: No Emotional Connection

### 4.1 No Real Imagery — MAJOR

**What the guidelines say:** "Nunca stock photos — siempre fotos reales del refugio." Homepage order: (1) Real photos of shelter and animals, (2) Adoption count (social proof), (3) Real team with names and photos, (4) Physical address and hours, (5) CTA.

**What the code does:** A text-only gradient (`bg-gradient-to-br from-primary-50 to-shelter-warm`) with no photos whatsoever. No shelter photos, no animal photos, no team photos, no address, no hours. Just text and numbers.

### 4.2 Stats Are Hardcoded and Fake — MAJOR

"150+ Animals Rescued", "80+ Successful Adoptions", "50+ Active Volunteers" are hardcoded strings. These should come from the API (the database knows how many animals exist, how many adoptions completed). Hardcoded numbers erode trust when they don't match reality.

### 4.3 Emoji Icons Instead of Professional Graphics — MODERATE

The "How You Can Help" section uses `🏠`, `💝`, `🤝` emoji as section icons. This looks amateurish for an NGO seeking EU donor trust. The project uses `lucide-react` in its nextjs-patterns skill — proper SVG icons should be used.

### 4.4 No Trust Signals — MAJOR

Zero testimonials, no team section, no physical address visible, no registration number, no partner logos. The guidelines explicitly require these as trust-building elements before asking for conversion.

---

## 5. Animal Catalog: Functional but Unpolished

### 5.1 Emoji Placeholders — MODERATE

When an animal has no photo, a massive emoji (`🐕`, `🐈`, `🐾`) renders on a gray background. This looks unfinished. The guidelines specify "skeleton placeholders mientras cargan" for loading states.

### 5.2 Status Badges Misplaced — MODERATE

**What the guidelines say:** Badges should overlay the photo (top-right corner of the card image).

**What the code does:** Badges sit inline next to the animal name in the text area, competing for space with typography. On small screens, the name + badge wrap awkwardly.

### 5.3 Limited Filters — MODERATE

Only species filter (All/Dogs/Cats/Other). The API supports filtering by `species`, `status`, `breed`, `size`, `gender`, `age_range`, and full-text search. The guidelines specify segmented controls and granular filters.

### 5.4 No Skeleton Loaders — MODERATE

Loading state is a single centered spinner. No skeleton cards that hint at the layout that's coming. This violates the "Conexion Inestable como Caso Base" principle.

### 5.5 Duplicated Code — MINOR

`calculateAge()`, `statusBadgeClass()`, `STATUS_LABELS`, and `AnimalPlaceholder` are duplicated between `animals/page.tsx` and `animals/[id]/page.tsx`. Should be extracted to shared utilities.

---

## 6. Animal Detail Page: Weak Conversion

### 6.1 CTA Below the Fold — MAJOR

**What the guidelines say:** "Botones de accion principales al alcance del pulgar (zona inferior de la pantalla)."

**What the code does:** The "Apply to Adopt" button sits at the bottom of the content, after the photo, details grid, and description. On mobile, users must scroll past everything to find the primary action. No sticky bottom bar.

### 6.2 No Photo Gallery Interaction — MODERATE

Photo thumbnails render in a horizontal scroll strip but they're not clickable. No lightbox, no swipe gallery, no zoom. The guidelines specify "Tap en foto -> Ampliar galeria (swipe para pasar)."

### 6.3 Date Localization — MINOR

Dates use `en-US` locale: `toLocaleDateString("en-US", ...)`. Should be `es-PY`.

---

## 7. Adoption Form: Missing Critical UX Patterns

### 7.1 No localStorage Persistence — CRITICAL

**What the guidelines say:** "Formularios guardan progreso localmente (localStorage) — no perder datos al perder senal."

**What the code does:** All form state is in React `useState`. Refresh the page, lose everything. On a 3G connection that drops mid-form, the user starts over.

### 7.2 Single Page Form Instead of Multi-Step — MAJOR

**What the guidelines say:** Multi-step form with progress bar. "Un concepto por paso, barra de progreso visible." Max 5-6 questions per step.

**What the code does:** All fields on one page. No progress indicator. No step-by-step flow. The form is manageable now (4 fields) but the guidelines anticipate this growing into a proper adoption screening form.

### 7.3 No Optimistic UI Feedback — MAJOR

**What the guidelines say:** "Acciones criticas (enviar formulario) con feedback inmediato optimista + confirmacion real."

**What the code does:** Button text changes to "Submitting..." but there's no optimistic feedback. No visual confirmation that the system received the click. On slow connections, the user doesn't know if it's working.

### 7.4 Success Message Tone — MODERATE

The success message says "Application Submitted!" with a `🎉` emoji. The guidelines want: "Estas un paso mas cerca de conocer a [name]!" — personal, warm, mentioning the animal by name naturally, and promising WhatsApp confirmation.

---

## 8. Contact Page: Basic but Adequate

### 8.1 No WhatsApp Alternative — MAJOR

The contact page only offers an email form. For Paraguayan users, WhatsApp IS the contact method. The page should prominently display the WhatsApp number and only secondarily offer the email form.

### 8.2 Success Message Weak — MODERATE

"Message Sent! Thank you for reaching out. We'll get back to you as soon as possible." Should be warmer and mention the response channel (WhatsApp preferred).

---

## 9. Technical & Accessibility Issues

### 9.1 No `aria-describedby` on Form Errors — MODERATE

Form inputs with validation errors show error text visually but don't link it via `aria-describedby`. Screen readers won't associate the error with the input.

### 9.2 Hardcoded `unoptimized` on All Images — MODERATE

Every `<Image>` component has `unoptimized` prop, bypassing Next.js image optimization. This means no WebP conversion, no responsive sizing, no lazy loading optimization. On 3G connections, this is painful.

### 9.3 No `inputMode` Attributes — MINOR

Phone input should have `inputMode="tel"`, email should have `inputMode="email"` per the guidelines. Currently using `type` but not `inputMode`.

### 9.4 Viewport themeColor Wrong — MINOR

`layout.tsx` sets `themeColor: "#16a34a"` (the wrong green). Should be `#E8622A` (the real primary orange).

---

## 10. Missing Components & Infrastructure

| Missing Component | UX Principles Reference | Priority |
|---|---|---|
| WhatsApp floating button | "Boton flotante visible en todas las paginas" | CRITICAL |
| `/about` page | Navbar + Footer link, trust building | CRITICAL |
| `/donate` page | Homepage CTA, Footer link, revenue | CRITICAL |
| `/volunteer` page | Footer link | MAJOR |
| `/foster` page | Footer link | MAJOR |
| Skeleton card loaders | "skeleton placeholders mientras cargan" | MAJOR |
| Service Worker / PWA | "Catalogo disponible offline via Service Worker" | MODERATE |
| Error boundary pages | Graceful error handling | MODERATE |
| 404 page (custom) | Brand consistency on errors | MODERATE |

---

## Summary Scorecard

| Category | Score | Notes |
|----------|-------|-------|
| Color System Alignment | 1/10 | Inverted primary/secondary |
| Language & Localization | 0/10 | 100% English, target is Spanish |
| Tone & Voice | 1/10 | Corporate English vs warm Spanish |
| Navigation Integrity | 4/10 | 4 of 9 links are dead |
| WhatsApp Integration | 0/10 | Completely absent |
| Homepage Trust Building | 2/10 | No photos, no team, no address |
| Animal Catalog UX | 5/10 | Functional but unpolished |
| Adoption Flow UX | 3/10 | No persistence, no multi-step |
| Form Resilience (3G) | 2/10 | No localStorage, no offline |
| Accessibility (WCAG AA) | 5/10 | Basic structure ok, details missing |
| Performance Optimization | 3/10 | All images unoptimized |
| Code Quality | 6/10 | Duplicated utilities, ok structure |

**Overall: 2.7 / 10** — Functional skeleton that needs a complete visual, linguistic, and UX overhaul.
