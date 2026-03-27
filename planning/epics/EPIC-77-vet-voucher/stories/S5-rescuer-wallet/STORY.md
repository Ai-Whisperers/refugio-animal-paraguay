---
story: S5
epic: EPIC-77
ticket: RAP-511
title: "Rescuer voucher wallet and claim flow"
status: ready
points: 5
priority: P1
track: Fullstack
sprint: 11
version: V1
created: 2026-03-27T20:00:00
---

# S5: Rescuer voucher wallet and claim flow

## Story
As a **rescuer**, I want **to see available vouchers for my area and claim them** so that **I can access free or subsidized veterinary services for animals in my care**.

## Description
Create rescuer interface to discover available vouchers from donors and claim them for animals they're caring for. Claimed vouchers show up in their wallet with details for clinic redemption.

## Acceptance Criteria
- [ ] /portal/vouchers page for rescuers: shows "Available Vouchers" section with: clinic name, location, service type, value/amount, "Claim" button
- [ ] Voucher filtering: GET /api/vouchers/available endpoint returns unclaimed vouchers, filtered by rescuer's location (within 100km radius based on rescuer profile location), sorted by expiry date (soonest first), paginated (limit 10)
- [ ] Voucher discovery: show service type, clinic name, clinic address, amount, expiry date, description of what service covers
- [ ] "Claim" button: POST /api/vouchers/{code}/claim endpoint, rescuer selects which animal they want to use voucher for (dropdown from their animals), optional note ("This is for surgical wound treatment")
- [ ] Claim flow: validate voucher exists and status=purchased, validate rescuer has animal in their care, set rescuer_id, animal_id, status=claimed, claimed_at=now(), return confirmation
- [ ] After claim: notification to clinic "Rescuer [name] has claimed a voucher for [service] at your clinic"
- [ ] Claimed vouchers section: shows rescuer's claimed vouchers (status=claimed), displays: code (or claim ID), clinic name, service type, animal name, "Share with Clinic" button (shows QR code), status badge
- [ ] QR code display: scanner-friendly, contains voucher code, clickable to copy to clipboard
- [ ] Share functionality: WhatsApp button pre-fills message "I have a voucher from Refugio for [service] at [clinic]. Voucher code: [code]"
- [ ] Redeemed vouchers section: shows past redeemed vouchers (status=redeemed), displays: clinic name, animal name, date redeemed, service type, proof photo if available
- [ ] Empty state: "No available vouchers in your area" with instructions to check back later
- [ ] Responsive design: mobile-optimized for rescuers using phones in field
- [ ] Notification to rescuer when new voucher becomes available in their area (if opted in for notifications)

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage) - test voucher availability filtering, claim validation
- [ ] Integration test: rescuer sees available vouchers
- [ ] Integration test: rescuer claims voucher for their animal
- [ ] Integration test: claimed voucher appears in wallet
- [ ] Integration test: location-based filtering works correctly
- [ ] Component test: responsive UI for mobile devices
- [ ] Component test: QR code generation and display
- [ ] Integration test: notification sent to clinic on claim
- [ ] Deployed to staging and verified

## Technical Notes
- Frontend: React page at pages/portal/vouchers.tsx with Available/Claimed/Redeemed sections
- Backend: GET /api/vouchers/available endpoint with location-based filtering using PostGIS or haversine distance calculation
- Location filtering: calculate distance between rescuer coordinates and clinic coordinates, return clinics within 100km (configurable)
- Claim endpoint: POST /api/vouchers/{code}/claim with body {animal_id, note}
- QR code generation: use qrcode Python library, return as image URL or SVG
- Animal selection: GET /api/rescuer/animals returns list of rescuer's animals in care
- Sorting: order by expires_at ASC (soonest first)
- Pagination: offset/limit parameters, default limit 10
- Notifications: send email/WhatsApp to clinic immediately on claim
- WhatsApp pre-fill: construct message with special formatting for readability

## Story Points: 5
