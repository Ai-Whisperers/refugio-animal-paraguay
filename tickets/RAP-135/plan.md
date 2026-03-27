# RAP-135 Plan

## Objective
Build a medical timeline UI component that shows chronological vet visits, vaccinations, and surgeries for an animal.

## Description
Staff need to view all medical history for an animal in a single scrollable timeline. The component integrates with the existing animal detail page, loading vet visits and vaccinations from the backend API.

## Acceptance Criteria
- [ ] Chronological timeline of vet visits appears on animal medical tab
- [ ] Each visit shows date, vet name, visit type, and status
- [ ] Vaccinations appear on timeline with name and date
- [ ] Surgeries appear on timeline with procedure and date
- [ ] Empty state shown when no medical records exist
- [ ] Loading and error states handled correctly
- [ ] Component integrated into admin animal detail page

## Complexity Assessment
**Track**: Complex Implementation

**Assessment result**: Complex — touches frontend, adds new TypeScript types, creates new component, integrates into existing page.

## Approach
1. Add medical/vaccination TypeScript types to api.ts
2. Create MedicalTimeline component that loads and displays vet visits and vaccinations
3. Create a medical tab section on the animal detail page
4. Wire up to the `/animals/{id}/vet-visits` and `/animals/{id}/vaccinations` endpoints

## Dependencies
- RAP-126 (Vet visit CRUD API) — DONE
- RAP-130 (Vaccination schema) — DONE

## Risks
- Timeline ordering: sort by date descending — handle null visit_date gracefully
