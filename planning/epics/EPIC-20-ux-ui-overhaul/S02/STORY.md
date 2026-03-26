# [S02] Spanish Translation & Warm Tone — RAP-172

## Story

As a **Paraguayan visitor**, I want the entire website to be in warm, conversational Spanish so that I can understand the content and feel welcomed by the shelter.

## Context

Every user-facing string (100+) across 8 files is hardcoded in English. The target audience is Paraguayan users (Spanish/Guarani speakers). The `UX-PRINCIPLES.md` provides specific tone examples and word preferences. This story translates all strings and adjusts the tone to be warm and personal rather than clinical/corporate.

## Acceptance Criteria

**Given** the UX principles tone guidelines
**When** I visit any page on the site
**Then:**
- [ ] All visible text is in Spanish
- [ ] HTML `lang` attribute is `es-PY` (not just `es`)
- [ ] Meta description in `layout.tsx` is in Spanish
- [ ] Skip link text is in Spanish ("Saltar al contenido principal")
- [ ] Navbar labels: "Inicio", "Animales", "Nosotros", "Contacto", "Donar"
- [ ] Footer section headers and links in Spanish
- [ ] Homepage hero: warm Spanish headline (not literal translation of "Every Animal Deserves a Loving Home")
- [ ] Homepage stats section in Spanish with natural phrasing
- [ ] Homepage "How You Can Help" section: "Adoptar", "Donar", "Ser Voluntario"
- [ ] Animals page: "Animales Disponibles para Adopcion", "Todas las Especies", "Perros", "Gatos", "Otros"
- [ ] Status labels in Spanish: "Disponible", "Adoptado", "En Acogida", "En Tratamiento", etc.
- [ ] Animal detail page: all labels in Spanish ("Especie", "Edad", "Llego al refugio")
- [ ] Adoption form: all labels, placeholders, validation messages, success message in Spanish
- [ ] Contact form: all labels, placeholders, success message in Spanish
- [ ] Error messages use warm tone: "Algo salio mal al enviar. Podes intentar de nuevo?" not "An unexpected error occurred"
- [ ] Success messages use warm tone: "Tu solicitud llego! Te confirmamos pronto." not "Application Submitted!"
- [ ] Loading states: "Cargando..." not "Loading..."
- [ ] Empty states: "No hay animales disponibles ahora. Volve pronto!" not "No animals available right now."
- [ ] Pagination: "Anterior" / "Siguiente" not "Previous" / "Next"
- [ ] Date formatting uses `es-PY` locale
- [ ] Strings are organized in a `src/lib/strings.ts` constants file for future i18n

## Tone Guidelines (from UX-PRINCIPLES.md)

| Instead of | Use |
|-----------|-----|
| "Solicitud enviada con exito" | "Tu solicitud llego! Te confirmamos por WhatsApp en minutos." |
| "Complete todos los campos requeridos" | "Falto completar algunos datos — los marcamos en rojo" |
| "Error 400: Bad Request" | "Algo salio mal al enviar. Podes intentar de nuevo?" |
| "Animal ID: 0042 — Canino" | "Luna, 2 anos — Perrita mestiza que adora los mimos" |
| "Proceso de adopcion iniciado" | "Estas un paso mas cerca de conocer a Max!" |

**Words to use:** mimos, amiguito, familia, hogar, amor, cuidado
**Words to avoid:** mascota (use "animal de compania" or the animal's name), procesado, usuario

## Technical Notes

- Create `src/lib/strings.ts` with all UI strings as named exports. Components import from here.
- This makes future i18n (next-intl) a single-file migration.
- Keep the constants object structure flat and grouped by page/component.
- Use template literal functions for strings with interpolation: `adoptionSuccess(name: string) => ...`

## Definition of Done

- [ ] Zero English strings visible on any page
- [ ] All strings sourced from `src/lib/strings.ts`
- [ ] Tone matches UX-PRINCIPLES.md examples
- [ ] Date/number formatting uses `es-PY` locale
- [ ] Deployed to staging and verified

## Story Points: 5
