---
story: S6
epic: EPIC-77
ticket: RAP-512
title: "Clinic redemption interface"
status: ready
points: 5
priority: P1
track: Fullstack
sprint: 11
version: V1
created: 2026-03-27T20:00:00
---

# S6: Clinic redemption interface

## Story
As a **clinic staff**, I want **to redeem vouchers when providing services** so that **I can track which services were performed and get reimbursed**.

## Description
Create clinic interface for redeeming vouchers. Staff enters or scans voucher code, verifies voucher details, uploads proof of service (photo and invoice), and marks as redeemed.

## Acceptance Criteria
- [ ] /clinic/redeem page accessible to clinic staff, shows: "Redeem Voucher" form with: voucher code input field (text with placeholder "Enter code or scan QR"), "Scan QR Code" button, or QR scanner integrated (camera input)
- [ ] QR code scanning: click "Scan QR Code" opens device camera, scans QR code containing voucher code, auto-fills code field
- [ ] Manual code entry: text field accepts code typed or pasted, validates UUID format
- [ ] Code lookup: GET /api/vouchers/{code} returns voucher details if valid, validates status=claimed
- [ ] Voucher display: shows: rescuer name, animal name, service type, amount, "Proceed" button
- [ ] Confirmation step: displays details and asks "Is this the service you performed?" with Yes/No buttons
- [ ] If No: clears form and allows re-entry
- [ ] If Yes: proceeds to proof upload
- [ ] Proof upload: file upload for proof photo (JPEG/PNG, max 5MB), description field ("We performed castration and vaccinations")
- [ ] Invoice upload: file upload for clinic invoice (PDF, DOC, max 10MB), required to claim reimbursement
- [ ] Submit button: POST /api/vouchers/{code}/redeem with body {proof_photo, proof_photo_description, invoice_file}, validates all required fields
- [ ] After successful redemption: show confirmation "Service recorded! Donor will receive notification.", status changes to redeemed, redeemed_at=now()
- [ ] Proof storage: photos and invoices stored in cloud storage (S3 equivalent), references stored in database
- [ ] Database: VetVoucher gets proof_photo_url, proof_description, invoice_url, invoice_filename fields
- [ ] Clinic dashboard: shows redeemable vouchers (status=claimed), completed vouchers (status=redeemed) with date redeemed
- [ ] Monthly reconciliation: clinic sees total redeemed amount, export as CSV for accounting
- [ ] Response format: {status: 'success', message: 'Voucher redeemed', voucher_details}

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage) - test code validation, redemption flow, proof handling
- [ ] Integration test: redeem voucher with proof photo and invoice
- [ ] Integration test: QR code scanning works correctly
- [ ] Integration test: manual code entry works
- [ ] Integration test: invalid code returns proper error
- [ ] Integration test: non-claimed voucher cannot be redeemed
- [ ] Component test: QR scanner integrates correctly
- [ ] Component test: file uploads validate size and format
- [ ] Integration test: confirmation notification sent to donor
- [ ] Deployed to staging and verified

## Technical Notes
- Frontend: React page at pages/clinic/redeem.tsx with form, QR scanner (use qr-scanner or react-qr-reader library)
- Backend: POST /api/vouchers/{code}/redeem endpoint, requires clinic auth
- QR code scanning: use HTML5 getUserMedia API for camera access, qr-scanner library to decode
- File upload: use multipart/form-data, validate MIME types (image/jpeg, image/png, application/pdf)
- Cloud storage: upload to S3 bucket, store URL in database
- File naming: use UUID-based naming to avoid collisions
- Validation: voucher code must be valid UUID, photo must be <5MB, invoice must be <10MB
- Error messages: "Voucher not found", "Voucher already redeemed", "Please upload proof photo and invoice"
- Clinic auth: verify current clinic user is from clinic_id on voucher
- Dashboard: show redeemable vouchers with "Redeem" button, redeemed vouchers with photo/invoice preview

## Story Points: 5
