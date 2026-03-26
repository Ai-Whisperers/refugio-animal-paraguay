---
task_id: T01
task_title: Setup SMS Gateway for Critical Alerts
task_status: pending
story_id: S02
epic_id: EPIC-6
created_date: 2026-03-25
estimated_effort: 5
dependencies:
  - EPIC-5 volunteer management (shift reminders)
  - EPIC-2 adoption system (urgent application updates)
  - Configuration system from EPIC-7
---

## Overview

This task establishes SMS notification infrastructure using a provider like Twilio or Vonage that supports South American phone numbers (Paraguay and neighboring countries). SMS is reserved for critical time-sensitive alerts where email delays are unacceptable: volunteer shift reminders sent one hour before start time, urgent adoption application decisions, and critical animal health alerts. The integration includes phone number validation, rate limiting to prevent SMS spam, and cost tracking since SMS carries per-message charges.

## Why This Task Matters

Some notifications cannot tolerate 30-minute email delivery delays. A volunteer who forgets their shift assignment needs a one-hour advance reminder via SMS to actually show up. An adoption applicant waiting for a critical yes/no decision on their application experiences anxiety if the decision sits in email unread for hours. Staff must be immediately alerted if a shelter animal has a life-threatening medical emergency. SMS provides guaranteed immediate delivery for these critical scenarios.

## Technical Requirements

The SMS provider credentials (API key, Account SID, phone number) must be read from environment variables. The application must support international phone numbers across South America (Paraguay country code +595, Argentina +54, Brazil +55, etc.). Phone numbers must be validated using a library that supports parsing and formatting across multiple countries.

The SMS gateway must enforce rate limits to prevent abuse: maximum 3 SMS messages per phone number per hour, maximum 50 SMS messages per shelter per day. Exceeded rate limits must log the attempt and skip sending rather than queuing a message that will fail later.

Each SMS message must be logged to the database with timestamp, recipient phone number, message content, status (sent, failed, queued), and cost if available from the provider. This logging enables cost tracking and troubleshooting.

SMS messages must be template-based and much shorter than email templates due to character limits. Messages must be under 160 characters to fit in a single SMS (longer messages incur multiple charges). The application must track message length and reject templates that exceed limits.

Failed SMS sends must be retried up to 2 times (SMS is less critical than email, so fewer retries). After 2 failures, the message is logged as failed without triggering an escalation.

## Implementation Approach

Create an SMS configuration module that reads provider credentials from environment variables and initializes the SMS client library. Create a phone number validation module that parses and validates international numbers using a library like phonenumbers.

Implement an SMS sending service that accepts a recipient phone number, template name, and context dictionary. The service validates the phone number, checks rate limits, renders the SMS template (much shorter than email), and submits to the provider.

Create a database table to log all SMS messages with recipient phone number (stored hashed for privacy), timestamp, status, and cost. Implement queries to calculate daily/monthly SMS costs and provide audit trail.

Implement rate limiting by tracking SMS sends per phone number and per shelter in the database. Query the SMS log table to determine if rate limits are exceeded before allowing a new send.

Write pytest tests that mock the SMS provider and verify rate limiting prevents excessive sends, phone number validation works across multiple countries, and failed sends are retried twice.

## Success Criteria

The application starts with SMS provider credentials from environment variables and confirms connectivity. A volunteer receives a one-hour advance SMS reminder for their shift assignment. SMS sends are rate-limited to 3 per phone number per hour and 50 per shelter per day. All SMS messages are logged to the database with timestamp, recipient, and status. Failed SMS sends are retried up to 2 times. All pytest tests pass covering international phone number validation and rate limiting scenarios.

