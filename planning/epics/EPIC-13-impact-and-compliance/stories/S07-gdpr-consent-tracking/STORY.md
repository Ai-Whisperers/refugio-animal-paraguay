---
story: S07
epic: EPIC-13
title: GDPR Consent Tracking
status: ready
created: 2026-03-26T00:00:00.000000
effort: 5
version: V3
---

# S07: GDPR Consent Tracking

## User Story

As a **donor, adopter, or volunteer**, I want to **manage my communication preferences and see a record of what I consented to (GDPR Article 7)** so that **the shelter can only contact me for purposes I explicitly agreed to, and I have transparency over my consent history**.

## Acceptance Criteria

**Given** I am a registered user
**When** I access my account settings → Communications/Privacy
**Then** I see a list of available communication types with toggle switches: marketing emails, newsletter, SMS updates, event invitations, donation receipts

**Given** I opt into a communication type (e.g., newsletter)
**When** I toggle the preference on
**Then** the system records: consent_type=newsletter, user_id, opt_in_date=now(), ip_address, user_agent, method=user_self_service, verification_method=implicit, consent_status=active

**Given** I opt out of a communication type
**When** I toggle the preference off
**Then** the system records: opt_out_date=now(), opt_out_reason (optional), previous_status transitions to inactive, and I immediately stop receiving that communication type

**Given** I request to view my consent history
**When** I click "View Consent Log" in account settings
**Then** I see a chronological list of all my consent changes: date, communication type, action (opt-in/opt-out), method (web form / email link / staff-assisted), IP/user agent, notes

**Given** the shelter sends me a marketing email
**When** I click "Unsubscribe" at the bottom of the email
**Then** my consent record updates (opt_out_date=now(), method=email_link) and I receive a confirmation that I've been unsubscribed

**Given** I never explicitly consented to a communication type
**When** I receive a communication attempt
**Then** the system blocks the send and logs a "consent_violation" audit event for staff review

**Given** I am a new donor completing a donation
**When** I submit the donation form
**Then** the form shows explicit checkboxes for opt-in (not pre-checked) with clear language: "Yes, I want to receive updates about my donation impact"

**Given** a staff member needs to opt in a user (e.g., during in-person signup)
**When** they check a consent checkbox in the staff dashboard
**Then** the system records the consent with method=staff_assisted, staff_id, notes, and sends a confirmation email to the user

## Tasks

- T01: Create user_consent database table (user_id, consent_type, opt_in_date, opt_out_date, ip_address, user_agent, method_enum, verification_method_enum, notes)
- T02: Implement PUT /api/user/{user_id}/consents endpoint for managing preferences
- T03: Build user-facing Consent History page showing all opt-in/opt-out events
- T04: Create consent validation middleware (before email send, check consent_status is active)
- T05: Add unsubscribe link handler for email click tracking (update consent, send confirmation)
- T06: Staff dashboard UI for reviewing user consent records and manual opt-in (with audit trail)
- T07: Email templates for consent confirmation, unsubscribe confirmation, consent reminder
- T08: Audit logging for all consent changes and validation failures
- T09: Unit tests for consent validation and state transitions (90%+ coverage)
- T10: Integration tests for email unsubscribe flow and staff opt-in workflow

## Definition of Done

- [ ] User consent table stores all required fields (type, dates, IP, method, verification)
- [ ] Consent API endpoint validates user identity and logs all changes
- [ ] Consent History page displays all changes chronologically with method/IP info
- [ ] Email send validation checks consent status before delivery
- [ ] Email unsubscribe links update consent and send confirmation immediately
- [ ] Staff consent management includes audit trail (who, when, why)
- [ ] Audit trail logs all consent changes and validation failures
- [ ] No unencrypted user data in email headers or unsubscribe URLs
- [ ] Unit test coverage ≥90% for consent validation
- [ ] Integration tests cover email unsubscribe, staff opt-in, and grace period scenarios
- [ ] Deployed to staging and verified

## Technical Notes

- Consent types (enum): marketing_email, newsletter, sms_updates, event_invitations, donation_receipts, donor_impact_reports, volunteer_communications
- Method values (enum): user_self_service, email_link, staff_assisted, import_batch
- Verification method (enum): implicit (user action), explicit (double-opt-in), staff_verified
- Email unsubscribe: generate UUID token in email URL like /api/email/unsubscribe/{token}, validate token before updating consent
- Staff opt-in: store staff_id, require reason/notes, send confirmation email to user
- Audit events: user_consent_granted, user_consent_revoked, consent_validation_failed, staff_consent_update
- Consider: double-opt-in for marketing email (require email link click), implicit opt-in for transactional (donation receipts)
- Grace period: consider 14-day re-engagement window before marking inactive donors

## Dependencies

- Depends on: S01-audit-trail-system (all consent changes must be audited)
- Depends on: EPIC-10 (User authentication and account management)
- Depends on: EPIC-6 (Communications and notifications — email service integration)
- Blocks: S03-impact-report-generator (reports should respect donor communication preferences)

## Story Points: 5
