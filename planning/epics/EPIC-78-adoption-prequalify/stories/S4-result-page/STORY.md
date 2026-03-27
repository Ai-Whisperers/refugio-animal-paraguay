---
story: S4
epic: EPIC-78
ticket: RAP-520
title: "Qualification result page with alternatives"
status: ready
points: 5
priority: P1
track: Frontend
sprint: 11
version: V1
created: 2026-03-27T20:00:00
---

# S4: Qualification result page with alternatives

## Story
As a **prospective adopter**, I want **to see qualification result and animal alternatives** so that **I can understand if I'm ready and explore other options**.

## Description
Display pre-qualification results. If qualified, show green confirmation with next steps. If not qualified, show clear explanation and suggest compatible animals.

## Acceptance Criteria
- [ ] Result page shown after form submission: displays result based on qualification status
- [ ] If qualified (qualified=true): show large green checkmark icon, "Congratulations! You're qualified to adopt [animal name]!", estimated wait time, "Continue to Full Application" button, "Browse Similar Animals" button
- [ ] If not qualified (qualified=false): show clear explanation of why (list each failed_requirement with human-readable message), "Animals That Match Your Profile" section with carousel/grid of 5-10 suggested alternatives
- [ ] Failed requirements display: red X icon, requirement type, specific failure message, e.g. "This animal needs a home with a yard. Your answer indicated apartment living."
- [ ] Alternative animals display: show animal photo, name, species, age, special traits ("Good with kids"), match score as % ("87% match"), "Learn More" button links to animal detail page
- [ ] Alternative animals filtered: only show animals with match_score >= 70% (from smart matching)
- [ ] Call-to-action: if not qualified but good alternatives exist, show "Browse X other animals that fit your home"
- [ ] Responsive design: single column on mobile, grid layout on desktop
- [ ] Share functionality: "Share my results" button to WhatsApp/email (if qualified, can share and encourage friends)
- [ ] Results summary printable: "Print or Save" button generates PDF with results, failed requirements, and alternatives
- [ ] No backtracking: once submitted, user sees results (form is now read-only)

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage) - test result rendering for qualified/unqualified
- [ ] Component test: qualified result displays correctly
- [ ] Component test: unqualified result with alternatives displays correctly
- [ ] Component test: alternatives carousel/grid renders animals
- [ ] Component test: PDF generation works
- [ ] Component test: responsive on mobile/tablet/desktop
- [ ] Integration test: clicking "Continue to Full Application" navigates to application form
- [ ] Integration test: clicking animal alternative navigates to animal profile
- [ ] Manual testing: verify UX for various scenarios
- [ ] Deployed to staging and verified

## Technical Notes
- Frontend: React component to display result, route to this after form submission
- Conditional rendering: if qualified, show green UI, else show unqualified UI with alternatives
- Result data: passed from pre-qualify API response (qualified, failed_requirements, suggested_animals)
- Alternatives: sorted by match_score DESC, limit 10
- PDF generation: use react-pdf or similar library
- Share functionality: construct WhatsApp message "I got X% match for adopting [animal]! Check if you match too: [link]"
- Printable: add print CSS media query for clean printing
- Animation: fade in result, slide in alternatives carousel

## Story Points: 5
