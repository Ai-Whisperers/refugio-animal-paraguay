---
epic_id: EPIC-11
story_id: S02
task_id: T01
title: Implement Contact Form Endpoint
status: ready
type: technical_task
priority: high
task_owner: backend-team
estimated_points: 5
created_at: 2026-03-25
updated_at: 2026-03-25
---

# T01: Implement Contact Form Endpoint

## Overview

This technical task focuses on implementing the general contact form submission endpoint that allows visitors to the public portal to submit inquiries, feedback, and messages to the Refugio Animal Paraguay staff. The endpoint serves as a primary communication channel for prospective adopters, donors, volunteers, and general inquiries about the shelter's mission and operations.

The contact form endpoint is a public, unauthenticated HTTP POST endpoint that accepts user-provided information including name, email address, subject matter, and message content. The implementation requires careful validation of all input fields to ensure data quality and prevent abuse through spam or injection attacks. The endpoint must integrate seamlessly with the email notification system established in EPIC-6 Communications to route submitted contact forms to appropriate staff members based on the subject category selected by the visitor.

The endpoint will be accessible at `/api/v1/contact` and will operate independently from the animal inquiry endpoint documented in the same story. This separation of concerns allows for distinct handling of contact inquiries versus adoption-specific inquiries, with different validation rules, routing logic, and staff notification workflows.

## Technical Specifications

The contact form endpoint accepts HTTP POST requests with a JSON payload containing four required fields. The visitor name field accepts up to one hundred twenty characters and is required for all submissions. This field captures the visitor's full name for identification and follow-up communication purposes. The email address field must be a valid RFC 5322 compliant email address with additional validation to prevent disposable email domains and known malicious email providers.

The subject field provides categorical information about the nature of the inquiry. The endpoint supports five predefined subject categories: general inquiry for information requests about the shelter's mission and operations, volunteer interest for individuals seeking to participate in shelter activities, adoption question for adoption-related inquiries distinct from formal adoption applications, donation inquiry for financial contribution and fundraising information, and other for miscellaneous or uncategorized messages.

The message field accepts the visitor's actual inquiry or feedback and can be up to two thousand characters in length. This allows sufficient space for detailed questions, feedback, and inquiries without imposing unrealistic constraints on visitor communication. The message field must be present in the request but can include reasonable whitespace handling to prevent trivial submissions.

The implementation uses Pydantic v2 request schema validation to enforce these constraints at the application layer. The ContactFormSubmission schema defines required fields with appropriate type annotations and validation constraints. Field descriptions include clear guidance on what information is expected in each field, enabling better error messages when validation fails.

Rate limiting is enforced per unique IP address with a threshold of ten submissions per calendar hour. The rate limiting mechanism operates independently for the contact form endpoint and the animal inquiry endpoint, meaning a visitor can submit ten contact forms and ten animal inquiry forms within a single hour before triggering rate limit responses. Rate limit tracking uses in-memory storage with automatic cleanup of expired entries to prevent memory bloat.

When a submission arrives within rate limits, the endpoint immediately stores the form submission in the database with a unique identifier, timestamp, and submission status. The form submission record includes denormalized copies of all submitted data for audit trail and follow-up purposes. The initial submission status is set to pending, indicating the message has been received but not yet processed by staff.

Immediately after storage, the endpoint triggers email notification to staff members through the EPIC-6 Communications system. The notification routing uses the subject category to determine which staff members receive the notification. General inquiries route to a general inquiry staff group, volunteer inquiries route to volunteer coordination staff, adoption questions route to adoption specialists, donation inquiries route to fundraising coordinators, and other messages route to a default general inbox.

A confirmation email is generated and sent to the visitor's provided email address to acknowledge receipt of their inquiry and set expectations for response time. The confirmation email includes the form submission identifier for reference in follow-up communication and provides information about typical response timeframes depending on the inquiry subject.

The endpoint returns a success response with HTTP 200 OK status when the submission completes successfully. The response includes the submission identifier allowing visitors to reference their submission in subsequent communication. The response also includes expected response time information based on the subject category to manage visitor expectations appropriately.

## Acceptance Criteria

The implementation is complete when the contact form endpoint accepts POST requests at the `/api/v1/contact` path and validates all four required fields according to specifications. The name field must accept between one and one hundred twenty characters, rejecting names that are empty or exceed the maximum length. The email field must validate against RFC 5322 standards and reject disposable email domains through integration with a disposable email provider list.

The subject field must accept only the five predefined categories, returning a validation error if any other subject value is provided. The message field must accept up to two thousand characters and must contain at least one non-whitespace character, preventing trivial submissions of only whitespace content.

When validation succeeds, the implementation stores the submission in the database with all provided information, a unique identifier, submission timestamp, and pending status. The stored record is immediately retrievable for verification purposes and serves as the source of truth for all contact form submissions.

Rate limiting enforcement prevents more than ten submissions per unique source IP address within any calendar hour window. When a submission exceeds the rate limit, the endpoint returns an HTTP 429 Too Many Requests status code with appropriate error messaging indicating the rate limit policy and when the visitor can retry their submission.

The implementation triggers email notifications to staff through the EPIC-6 Communications system with subject-based routing to appropriate staff groups. The notification includes the submission details, visitor contact information, and a link to the staff dashboard for follow-up actions. The notification uses the staff email system configured in EPIC-6 with appropriate retry logic for transient delivery failures.

A confirmation email is sent to the visitor's provided email address within seconds of successful submission. The confirmation email includes the submission identifier, acknowledgment of receipt, and expected response timeframe based on the subject category. The confirmation email is generated through the EPIC-6 Communications system and uses appropriate email templates for consistency.

The endpoint achieves response times of less than five hundred milliseconds for the majority of requests, measured from request receipt to response transmission. This includes validation, database insertion, and email notification triggering. Performance profiling demonstrates that database latency and email notification queuing are not the bottleneck in the request-response cycle.

All submitted data is properly escaped and protected against injection attacks. Input validation prevents SQL injection, NoSQL injection, and other common attack vectors. The implementation follows OWASP standards for input validation and uses parameterized database queries exclusively.

## Implementation Considerations

The contact form endpoint must handle concurrent submissions efficiently without creating bottlenecks. Database insertion should use efficient batch operations where applicable and leverage connection pooling to minimize database overhead. The email notification system should operate asynchronously to prevent request-response delays from email system latency.

Rate limiting implementation requires careful consideration of distributed deployment scenarios. If the application runs on multiple server instances, in-memory rate limiting based solely on IP address may not function correctly as different instances maintain separate tracking. Implementation should consider using a shared rate limiting backend such as Redis for consistency across instances, or document the single-instance requirement clearly.

Email validation requires integration with external services or local validation lists. The disposable email provider check should use regularly updated lists or API services to maintain accuracy. Implementation should include caching mechanisms to avoid repeated lookups for the same email domains and should fail gracefully if external validation services become unavailable.

The Pydantic schema definition should include descriptive error messages that guide users toward correct input format. For email validation failures, messages should distinguish between malformed email addresses and disposable email domain rejections to help users understand why their email was rejected.

Database schema design should include appropriate indexes on frequently queried fields such as visitor email address and submission creation timestamp. The contact_form_submissions table should include columns for all form fields plus metadata fields for submission status, creation timestamp, and soft-delete indicators.

The soft-delete implementation for contact form submissions uses a published or visible flag rather than physical deletion, preserving audit trails and enabling recovery if needed. Staff can mark submissions as reviewed or deleted from their perspective without physically removing the data, supporting long-term audit requirements.

The implementation should establish clear conventions for how subject categories map to staff groups or email addresses. Configuration should externalize this mapping to prevent code changes when staff responsibilities shift. Configuration-driven routing enables operational flexibility without code deployment.

Error handling throughout the implementation provides specific feedback on validation failures. Generic error messages frustrate users and prevent them from correcting their input. Implementation should communicate which field failed validation and what constraint was violated, enabling users to adjust their submission appropriately.

## Success Metrics

The contact form endpoint successfully accepts valid contact submissions and stores them in the database. Verification involves submitting test forms with valid data and confirming the submissions appear in the database with correct field values and metadata.

Email notifications reach staff members with appropriate subject-based routing. Verification involves checking that staff members in different groups receive notifications corresponding to their group assignments and that routing logic correctly identifies appropriate recipients.

Confirmation emails reach visitor-provided addresses with correct submission information and expected response timeframes. Verification involves submitting test forms and confirming receipt of confirmation emails with correct content and submission identifiers.

Rate limiting enforcement prevents excessive submissions from the same IP address. Verification involves submitting more than ten forms from a test IP address within a single hour and confirming that submissions after the tenth trigger rate limit errors.

Response time measurements confirm that the endpoint operates within the five hundred millisecond target for the vast majority of requests. Performance profiling under load conditions demonstrates that the endpoint can handle reasonable traffic volumes without degradation.

Input validation rejects invalid email addresses, oversized messages, and invalid subject categories. Verification involves submitting test forms with intentionally invalid data and confirming appropriate validation errors are returned.

Disposable email domain validation rejects submissions from disposable email providers. Verification involves submitting forms from known disposable email addresses and confirming rejection with appropriate error messaging.

## Testing Strategy

Unit tests validate the Pydantic schema for ContactFormSubmission against valid and invalid input combinations. Tests verify that the schema accepts all valid field combinations and rejects missing fields, oversized fields, and invalid email addresses. Tests include edge cases such as maximum-length names, exactly one non-whitespace character in messages, and all five subject categories.

Integration tests verify the complete request-response cycle through the endpoint. Tests submit valid contact forms and verify that database records are created with correct field values. Tests submit invalid forms and verify that appropriate validation errors are returned. Tests verify that rate limiting is enforced correctly by submitting multiple forms and confirming the rate limit error appears after the tenth submission.

Email notification tests verify that email notifications are queued for delivery through the EPIC-6 Communications system. Tests check that notifications are routed to the correct staff groups based on subject category. Tests verify that confirmation emails are queued for delivery to visitor-provided addresses.

Performance tests measure response times under realistic load conditions. Tests submit contact forms through load generation tools and measure response time percentiles, confirming that the majority of requests complete within the five hundred millisecond target.

Security tests verify input validation and injection prevention. Tests submit deliberately malformed input designed to trigger injection vulnerabilities and confirm that the implementation rejects such input safely. Tests verify that stored data is properly escaped and cannot be exploited through subsequent retrieval.

End-to-end tests verify the complete user journey from form submission through staff notification and visitor confirmation. Tests submit contact forms through the public endpoint and verify that staff members receive notifications and visitors receive confirmation emails.

## Dependencies and Constraints

This task depends on EPIC-6 Communications being implemented to provide the email notification infrastructure. The contact form endpoint requires access to configured email addresses or staff group identifiers to route notifications appropriately.

This task depends on the database schema including the contact_form_submissions table with appropriate columns for form fields, metadata, and soft-delete indicators.

This task depends on rate limiting infrastructure being available, either through Redis integration or in-memory tracking acceptable for the deployment target.

This task depends on the Pydantic v2 schema validation framework being available in the FastAPI application.

The implementation is constrained to operate within the FastAPI application's request-response cycle and must complete within the five hundred millisecond response time target including database insertion and email notification queuing.

The implementation must use parameterized database queries exclusively to prevent SQL injection vulnerabilities, regardless of how the database access layer is implemented.

The implementation must not store plain-text passwords or security credentials in the contact_form_submissions table, and must protect all sensitive visitor information according to data protection regulations.

The implementation is constrained to provide internationalization support through the email templates provided by EPIC-6, allowing notification content to be localized appropriately for Spanish and Dutch recipients.
