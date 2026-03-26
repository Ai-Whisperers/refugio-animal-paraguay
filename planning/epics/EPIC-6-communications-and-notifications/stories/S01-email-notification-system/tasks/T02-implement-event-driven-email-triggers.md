---
task_id: T02
task_title: Implement Event-Driven Email Triggers
task_status: pending
story_id: S01
epic_id: EPIC-6
created_date: 2026-03-25
estimated_effort: 8
dependencies:
  - T01-setup-smtp-configuration
  - EPIC-3 donation system webhooks
  - EPIC-2 adoption application endpoints
  - EPIC-5 volunteer management
---

## Overview

This task wires email notifications into business events throughout the application. Whenever a significant event occurs (donation received, adoption application submitted, volunteer shift assigned, animal's medical status changes), the system automatically triggers the appropriate email notification to relevant stakeholders. The triggers are implemented as callback functions invoked at strategic points in the code, decoupled from core business logic.

## Why This Task Matters

Users expect immediate feedback when they take actions (confirming a donation, submitting an adoption application). Staff members rely on email alerts to know when action is required (new application to review, volunteer no-show to follow up on). Without event-driven triggers, notifications must be manually sent or require polling, creating delays and missed opportunities for engagement.

## Technical Requirements

Email triggers must be implemented as callback functions that are invoked after the primary business operation completes successfully. For example, after a donation payment is confirmed in the webhook, the system calls a donate_success callback function that renders and sends the donation receipt email.

Trigger functions must accept event data (donation record, adoption application record, etc.) and extract relevant information for template rendering. The trigger function must determine the recipient email address, select the appropriate template, render it with context data, and queue it for sending.

Triggers must handle errors gracefully. If email rendering fails (template syntax error, missing context field), the trigger must log the error but not fail the primary business operation. A human operator must review failed notifications in a dedicated admin dashboard.

Triggers must support conditional delivery based on user preferences. If a donor has opted out of promotional emails, they still receive transactional emails (donation receipt) but not marketing emails (monthly newsletter). The application must query the user preferences before deciding whether to send an optional notification.

Bulk operations that affect many records (e.g., assigning 20 volunteers to shifts, approving bulk donations) must batch email sends so that all 20 emails are queued within a single database transaction, not individually.

## Implementation Approach

Create an events module that defines event types (DonationReceived, AdoptionApplicationSubmitted, AnimalBecomeAvailable, etc.) as simple dataclasses. Each event type includes fields from the associated business record that are needed for email rendering.

Create a triggers module that implements a callback function for each event type. Each callback accepts an event object, extracts context data, queries user preferences, renders the appropriate template, and queues the email for sending.

Wire trigger functions into the codebase at the points where business events occur. For donations, the webhook handler calls the donate_success trigger after updating the donation status. For adoption applications, the POST endpoint calls the application_submitted trigger after inserting the record.

Implement a preferences check function that queries the user table to determine opt-in/opt-out status for different notification categories. The trigger respects these preferences before sending.

Write pytest tests that simulate business events and verify the correct email templates are rendered with correct context data. Test that bulk operations queue multiple emails without duplicating sends.

## Success Criteria

When a donation is successfully confirmed, a donation receipt email is sent within 100 milliseconds to the donor. When an adoption application is submitted, confirmation emails are sent to the applicant and staff reviewers within 100 milliseconds. When a volunteer is assigned a shift, a reminder email is queued to send 24 hours before the shift. Bulk operations that assign 20 volunteers queue 20 emails without delays or duplicates. Opt-out preferences are respected and opted-out users do not receive marketing emails. All pytest tests pass covering 8 event types and preference checks.

