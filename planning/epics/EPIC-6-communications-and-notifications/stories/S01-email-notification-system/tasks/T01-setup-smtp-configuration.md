---
task_id: T01
task_title: Setup SMTP Configuration and Email Templates
task_status: pending
story_id: S01
epic_id: EPIC-6
created_date: 2026-03-25
estimated_effort: 5
dependencies:
  - EPIC-3 donation system (sending donation confirmations)
  - EPIC-2 adoption system (sending adoption status updates)
  - Configuration system from EPIC-7
---

## Overview

This task establishes the email infrastructure by configuring SMTP credentials, creating reusable email templates, and implementing a service layer for sending emails asynchronously. Email notifications are critical for keeping donors updated on their contributions, notifying adopters of application status, and alerting staff to important events. The task includes setting up template rendering, handling bounced emails, and logging all email deliveries for audit purposes.

## Why This Task Matters

Email is the primary notification channel for non-authenticated users (donors who visit the public site without creating an account). Adoption applicants rely on email updates throughout their application journey (confirmation, under review, approved/rejected). Staff members receive email alerts for high-priority events (new adoption application, animal health emergency, large donation). Without reliable email infrastructure, the shelter loses visibility into critical business events and users become frustrated when they lack status updates.

## Technical Requirements

The SMTP configuration must be read from environment variables (SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, SMTP_FROM_EMAIL) during application startup. The application must support both standard SMTP (port 587 with STARTTLS) and SMTPS (port 465 with implicit TLS). A test utility must verify SMTP connectivity on startup, raising a startup exception if SMTP is unreachable.

Email templates must be stored as HTML files with Jinja2 templating support for dynamic content injection. Templates must include adoption confirmation, donation receipt, animal available for adoption, volunteer shift reminder, and admin alerts. Each template must have a plain-text fallback version for clients that do not support HTML email.

The email service must accept a recipient email address, template name, and context dictionary, render the template with the context, and return a structured email message object without sending it. A separate sending function accepts the message object and uses FastAPI BackgroundTasks to queue it for asynchronous delivery.

Failed email deliveries must log the error and store the message in a retry queue. The application must attempt to resend failed emails up to 3 times with exponential backoff (1 minute, 5 minutes, 15 minutes). After 3 failed attempts, the message must be logged as permanently failed for manual review.

## Implementation Approach

Create an SMTP configuration module that reads and validates environment variables, tests connectivity on startup, and provides a reusable SMTP client. This module must handle connection pooling to avoid opening a new SMTP connection for every email.

Create a template directory structure with subdirectories for each notification type (donations, adoptions, staff-alerts). Store templates as HTML files with .html extension and plain-text versions with .txt extension.

Implement an email rendering service that accepts a template name, context dictionary, and optional recipient name. The service loads the HTML template, renders it with Jinja2, loads the corresponding plain-text template, and returns a structured email message object (using the Python email library or similar).

Implement an email sending service that accepts an email message object, queues it for asynchronous delivery using BackgroundTasks, and returns immediately to the caller. The BackgroundTask handler opens an SMTP connection, sends the email, and logs success or failure.

Write pytest tests that mock the SMTP connection and verify template rendering produces valid HTML and plain-text output. Test that failed send operations are retried according to the backoff schedule.

## Success Criteria

The application starts successfully with SMTP credentials from environment variables and verifies connectivity on startup. An email can be rendered from a template and sent asynchronously within 100 milliseconds of the send request (actual delivery happens in background). Failed emails are retried up to 3 times according to the backoff schedule. All pytest tests pass with 100% coverage of template rendering and SMTP client logic. Plain-text fallback versions are generated alongside HTML templates.

