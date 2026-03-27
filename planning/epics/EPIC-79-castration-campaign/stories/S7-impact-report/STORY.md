---
story: S7
epic: EPIC-79
ticket: RAP-531
title: "Post-campaign impact report"
status: ready
points: 5
priority: P2
track: Fullstack
sprint: 12
version: V1
created: 2026-03-27T20:00:00
---

# S7: Post-campaign impact report

## Story
As a **campaign creator**, I want **to generate impact report when campaign ends** so that **I can share success with donors and stakeholders**.

## Description
Auto-generate impact report when campaign reaches 100% or end_date passes. Report summarizes statistics and can be shared as PDF or social media post.

## Acceptance Criteria
- [ ] Report trigger: when campaign.completed_count >= campaign.target_count OR campaign.end_date reached, generate report
- [ ] Report data: total animals castrated, total cost (sum of voucher amounts), cost per animal, clinics involved (count and names), areas covered, donors (count), campaign duration
- [ ] Report page: /campaigns/castration/{id}/report shows: title "Campaign Complete!", headline stats, breakdown by clinic, photos gallery, donor testimonial section
- [ ] Report sections: "By The Numbers" (stats cards), "Partner Clinics" (list with contributions), "Photo Gallery" (all photos), "Impact Story" (narrative), "Financial Summary"
- [ ] Shareable cards: auto-generated image card showing: "We castrated X animals! Campaign name, date, stats" - optimized for social media
- [ ] PDF export: "Download Report as PDF" button generates printable PDF with all sections
- [ ] Email sharing: automatic email to all donors with link to report and summary
- [ ] Social media: generate Open Graph tags for sharing
- [ ] Report data API: GET /api/campaigns/castration/{id}/report returns JSON with all report data

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage) - test report generation, PDF creation
- [ ] Integration test: report generated when campaign completes
- [ ] Integration test: PDF export works
- [ ] Integration test: emails sent to donors
- [ ] Component test: report page displays correctly
- [ ] Manual testing: verify report accuracy
- [ ] Deployed to staging and verified

## Technical Notes
- Trigger: cron job checks daily for campaigns reaching end_date or 100%
- Report generation: compile data from VetVoucher, Donation, CastrationDrive tables
- PDF generation: use reportlab or similar library
- Image generation: use PIL/Pillow to create social media cards
- Email: send to all donors of campaign
- Open Graph: set og:image, og:title, og:description
- Report data: cache after generation (report rarely changes)

## Story Points: 5
