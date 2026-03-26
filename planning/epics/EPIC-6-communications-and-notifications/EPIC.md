---
epic: EPIC-6
title: Communications & Notifications
status: ready
created: 2026-03-25T17:13:26.732358
updated: 2026-03-25T17:13:26.732361
---

# EPIC-6: Communications & Notifications

## Overview

**Goal**: Build a reliable, multi-channel notification system that keeps adopters, donors, volunteers, and staff informed of important events in real time — using the communication channels that each audience already trusts.

**Why it matters**: Paraguay is a WhatsApp-dominant culture. Volunteers and local adopters expect to receive updates through WhatsApp, not email. At the same time, the European donor network expects professional email confirmations and receipts that meet the formality standards they associate with organizational credibility. A notification system that serves only one channel fails one of these audiences entirely. This epic builds the infrastructure that allows other epics to emit notification events without caring how those events are delivered — the notification service handles routing, formatting, and delivery across all channels. Centralizing this logic also makes it easier to enforce GDPR requirements about what personal data is included in notifications.

**Target users**: Adopters who receive application status updates and adoption confirmations; donors who receive payment receipts and recurring donation summaries; volunteers who receive shift confirmations, reminders, and cancellations; shelter staff who receive alerts about overdue tasks and unfilled shifts; administrators who can review notification delivery history and failure logs.

---

## Scope

### In Scope

- Transactional email delivery using a third-party email service provider (Mailgun, Resend, or equivalent SMTP-based service); covering adoption application updates, donation receipts, and account-related messages such as password resets and email verification
- WhatsApp message delivery via the WhatsApp Business API (Meta Cloud API); covering shift confirmation and reminder messages for volunteers, and adoption status updates for local adopters who prefer WhatsApp over email
- In-app notification records stored in the database and surfaced through a dedicated API endpoint; covering any event type, queryable by recipient and read/unread status
- Notification event queue: other epics emit structured notification payloads to a queue or directly to the notification service; this epic consumes and routes those payloads to the appropriate delivery channels
- Notification preference management: recipients can configure which channels they want to receive each type of notification on; preferences are stored per-user and honored at delivery time
- Notification delivery log: every attempted delivery is recorded with its channel, timestamp, status (sent, failed, bounced), and the message identifier returned by the delivery provider; this log supports admin reporting and debugging
- Retry logic for transient delivery failures: failed email sends are retried with exponential backoff up to a configurable maximum attempt count; permanently failed messages are moved to a dead-letter record for manual review
- Template management: notification message content is defined in versioned templates rather than hardcoded strings; templates support variable substitution for recipient name, animal name, amount, dates, and other dynamic values

### Out of Scope

- SMS delivery (WhatsApp covers the same audience in Paraguay and avoids SMS costs; SMS may be added as a future channel)
- Push notifications to mobile apps (no mobile app exists in the current scope; this would require EPIC-11 or a future mobile epic)
- Bulk marketing campaigns or newsletter broadcasting (the shelter's donor newsletter is handled externally)
- Two-way WhatsApp conversations or chatbot functionality (the integration is send-only for notifications)
- Full email marketing platform with open tracking, click tracking, or A/B testing

---

## Stories

- **S01: Email Notification System** — Integrate with a transactional email service provider via its HTTP API. Implement the notification service layer that receives a notification event payload, selects the appropriate email template, renders it with the provided variables, and submits it to the email provider. Implement the delivery log write. Implement retry with exponential backoff for transient failures. Define email templates for: adoption application received, application status changed, adoption contract available for download, donation receipt, recurring donation charge confirmation, password reset, and email address verification.

- **S02: WhatsApp Integration** — Integrate with the WhatsApp Business API to send templated messages. WhatsApp requires pre-approved message templates for business-initiated messages; document the template approval process and store approved template identifiers in configuration. Implement the notification service routing logic that selects WhatsApp as the delivery channel when the recipient has a confirmed WhatsApp-capable phone number and has not opted out. Implement templates for: volunteer shift confirmation, shift reminder (sent 24 hours before the shift), shift cancellation by staff, and adoption status update for local adopters. Handle rate limiting responses from the WhatsApp API gracefully.

- **S03: In-App Notifications** — Implement the notifications table in PostgreSQL recording each notification with recipient user ID, event type, summary text, read status, and creation timestamp. Implement the FastAPI endpoint that returns a paginated list of unread notifications for the authenticated user, ordered by creation time descending. Implement the mark-as-read endpoint that accepts a list of notification IDs. Implement the badge count endpoint that returns the count of unread notifications for efficient polling from the frontend (TBD). In-app records are written for all notification types regardless of whether email or WhatsApp delivery also occurs.

- **S04: Notification Preferences** — Implement the notification preferences data model allowing each user to configure which channels (email, WhatsApp, in-app) they want to receive for each notification category (adoption updates, volunteer shifts, donation receipts, system alerts). Implement the FastAPI endpoints for reading and updating preferences. Apply preference filtering in the notification routing layer so that delivery only occurs through channels the recipient has enabled. Define sensible defaults: email on for all categories; WhatsApp off by default (must be explicitly enabled by the user to avoid sending unrequested WhatsApp messages); in-app always on.

---

## Dependencies

**Depends on**:
- EPIC-10 (Authentication & User Accounts) — recipient preferences and in-app notification records are tied to user accounts; the notification service must be able to look up a user's preferred channels by their user ID
- Third-party email service provider account and API credentials (set up during EPIC-9 infrastructure provisioning)
- WhatsApp Business API account and approved message templates (set up by shelter administrator during deployment; templates require Meta review and approval)

**Consumed by** (epics that emit notification events to this system):
- EPIC-2 (Adoption Process) — adoption application received, status changed, contract ready
- EPIC-3 (Donations) — donation receipt, recurring charge confirmation
- EPIC-4 (Medical Records) — vaccination overdue reminder, medication expiry alert
- EPIC-5 (Volunteer Management) — shift confirmation, shift reminder, shift cancellation
- EPIC-10 (Authentication) — password reset, email verification

---

## Success Metrics

- Email delivery latency: transactional emails dispatched within 30 seconds of the triggering event under normal load
- WhatsApp delivery latency: shift reminder messages delivered within five minutes of their scheduled send time
- Delivery reliability: fewer than 0.5 percent of notification attempts result in a permanent failure (bounces and invalid phone numbers excluded from this metric)
- Zero silent failures: every delivery attempt, successful or not, is recorded in the notification delivery log within five seconds of the attempt
- Preference compliance: no notification is delivered through a channel that the recipient has disabled; this is verified by integration tests against the preference system

---

## Risk Factors

- **WhatsApp template approval delays**: Meta's WhatsApp Business API requires each message template to be reviewed and approved before it can be sent. This approval process can take days. Mitigation: submit template approval requests early, before the shelter goes live; design the WhatsApp integration to fail gracefully by falling back to email if a template is not yet approved.
- **WhatsApp rate limiting for new accounts**: New WhatsApp Business accounts have low messaging rate limits that increase over time based on message volume and quality. Mitigation: plan a gradual rollout of WhatsApp notifications; monitor delivery success rates and quality scores in the WhatsApp Business API dashboard.
- **GDPR considerations for notification content**: Notification messages sent via third-party providers (Mailgun, WhatsApp) pass through systems outside the EU unless configured otherwise. Donor names, email addresses, and donation amounts in notification bodies are personal data. Mitigation: use the minimum personal data necessary in notification templates; document the legal basis for transmission in the platform's privacy policy; select email providers with EU data processing agreements.
- **Volunteer phone number quality**: WhatsApp delivery requires a valid, WhatsApp-registered phone number. Many volunteer numbers may be Paraguayan mobile numbers that are WhatsApp-registered, but this cannot be guaranteed. Mitigation: implement a WhatsApp number validation step during volunteer registration that confirms the number is reachable on WhatsApp before enabling the channel.

---

## Effort & Priority

**Priority**: Medium-high. Notification delivery is a dependency of the adoption and volunteer workflows' perceived quality — adopters and volunteers who receive no confirmation after submitting a form will lose trust. However, the core functional workflows (application submission, shift sign-up) are not blocked by notification delivery. Email notifications for the EU donor network are the highest-value deliverable and should be prioritized first.

**Estimated effort**: Two sprints. Email integration and the notification routing layer (S01, S04) form the first sprint and unblock the adoption and donation workflows. WhatsApp integration and in-app notifications (S02, S03) follow in the second sprint.
