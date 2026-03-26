# [S05] Homepage Redesign with Trust Signals — RAP-175

## Story

As a **first-time visitor**, I want to see real evidence of the shelter's work (photos, impact numbers, team, location) so that I trust the organization before taking any action.

## Context

The current homepage is a text-only gradient with hardcoded English stats and emoji icons. The UX principles mandate a specific information hierarchy for trust-building: (1) Real photos, (2) Social proof/stats, (3) Team, (4) Physical presence, (5) CTA. The homepage is the primary entry point and sets the emotional tone for the entire site.

## Acceptance Criteria

**Given** I visit the homepage
**When** the page loads
**Then:**

### Hero Section
- [ ] Full-width hero with a placeholder for real shelter/animal photography (use a warm gradient + branded SVG illustration until real photos are available)
- [ ] Headline in warm Spanish (not "Every Animal Deserves a Loving Home")
- [ ] Subheadline mentioning Paraguay specifically, establishing geographic identity
- [ ] Two CTAs: "Conoce Nuestros Animales" (primary orange) and "Quiero Donar" (secondary green)
- [ ] CTAs at thumb-reach level on mobile

### Impact Stats Section
- [ ] Dynamic stats from API where possible (animal count, adoption count)
- [ ] Fallback to reasonable hardcoded values if API unavailable
- [ ] Warm labels: "Animales Rescatados", "Adopciones Exitosas", "Voluntarios Activos"
- [ ] Counter animation or visual emphasis

### How to Help Section
- [ ] Replace emoji icons (🏠💝🤝) with Lucide React SVG icons (Home, Heart, Users)
- [ ] Three cards: Adoptar, Donar, Ser Voluntario
- [ ] Warm descriptions in Spanish
- [ ] Each card links to the relevant page

### Trust Signals Section (NEW)
- [ ] "Nuestro Equipo" — structure for team member cards (photo placeholder, name, role)
- [ ] "Donde Encontrarnos" — physical address, hours, location indicator
- [ ] Contact info visible: WhatsApp number, email

### Social Proof Section (NEW)
- [ ] "Historias de Adopcion" — placeholder structure for adoption testimonials
- [ ] Card layout: adopter quote, animal name, photo placeholder

### Footer CTA
- [ ] Warm closing CTA: "Cada animal merece una oportunidad. Vos podes ser parte de su historia."
- [ ] WhatsApp and donate buttons

## Technical Notes

- The homepage should be a server component where possible. Stats could be fetched server-side from the API.
- Use `lucide-react` icons instead of emoji. Package is already in the skill spec.
- Install `lucide-react` if not present: `npm install lucide-react`
- Glassmorphism hint for hero text overlay: `bg-white/80 backdrop-blur-sm rounded-2xl`

## Definition of Done

- [ ] Homepage renders with all sections
- [ ] All text in Spanish with warm tone
- [ ] No emoji icons — proper SVG icons
- [ ] Structure ready for real photos (placeholder graphics acceptable)
- [ ] Mobile-first responsive
- [ ] Deployed to staging

## Story Points: 5
