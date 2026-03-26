---
epic_id: EPIC-11
story_id: S02
task_id: T02
title: Implement Animal Inquiry Endpoint
status: ready
type: technical_task
priority: high
task_owner: backend-team
estimated_points: 5
created_at: 2026-03-25
updated_at: 2026-03-25
---

# Task T02: Implement Animal Inquiry Endpoint

## Overview

This task involves developing a dedicated HTTP POST endpoint that enables visitors to express adoption interest in specific animals featured on the public portal. Unlike the general contact form endpoint documented in T01, this endpoint is specifically designed to capture structured inquiry data about particular animals, routing inquiries directly to adoption staff for immediate follow-up. The endpoint serves as a critical conversion point in the adoption journey, transforming casual browsing into qualified adoption inquiries.

The animal inquiry endpoint creates a direct communication channel between prospective adopters and the adoption team. When a visitor views an animal's profile on the public portal and decides to express interest, they interact with a streamlined inquiry form that pre-populates the target animal's identifier and collects essential adoption-related information. This endpoint integrates tightly with the animal management system and the adoption workflow, ensuring inquiries reach the appropriate staff members with complete context about the specific animal of interest.

The endpoint supports rate limiting at the IP address level to prevent abuse while remaining accessible to genuine prospective adopters. Rate limiting is configured at twenty adoption inquiries per IP address per day, allowing multiple interested inquiries while preventing automated form spam. The endpoint enforces validation on all input fields including adopter contact information, household details relevant to animal welfare assessment, and animal-specific questions or concerns. Email notifications through the EPIC-6 Communications system immediately alert adoption staff of new inquiries, ensuring timely response to interested parties.

## Technical Specifications

The HTTP POST endpoint is located at `/api/v1/animals/{animal_id}/inquiries` and accepts inquiry submissions for the animal identified by the provided path parameter. The animal identifier must be a valid UUID corresponding to an existing animal record in the animals table. If the animal does not exist or has been deleted, the endpoint returns HTTP 404 Not Found with an informative error message. If the animal exists but is not in an available or reserved status, the endpoint returns HTTP 400 Bad Request indicating that the animal is not currently available for adoption inquiries.

The request body contains a JSON object with the following fields structured according to Pydantic v2 validation schemas. The adopter name field accepts between three and one hundred twenty characters of alphabetic, numeric, and basic punctuation characters. The email field must conform to RFC 5322 email format standards and must not be associated with a disposable or temporary email service. The phone number field accepts an international format including country code prefix, with a minimum of ten digits and a maximum of twenty digits when formatted without spaces or hyphens.

The household composition field captures the structure of the adopter's living situation and is essential for welfare assessment. Valid values are single person, married couple, family with children, shared apartment, multigenerational household, and other with description. When the household composition is family with children, the endpoint requires an additional age range specification for the children present in the household. Age ranges available are under five, five to ten, ten to fifteen, and fifteen to eighteen. This information helps adoption staff assess compatibility between animal temperament and household safety requirements.

The animal experience field documents the adopter's history with animals and informs staff recommendations. Valid values are no prior animal ownership, one to three years of ownership, three to five years, five to ten years, and more than ten years. Additionally, adopters specify which types of animals they have previously owned or cared for, selected from a predefined list including dogs, cats, birds, reptiles, fish, small mammals, and other with description.

The inquiry message field allows adopters to ask specific questions about the animal, express concerns, or provide additional context about their adoption interest. This field accepts between twenty and two thousand characters of text, with a requirement for meaningful content excluding purely whitespace submissions. The field supports multiple languages with primary Spanish language expectation and automatic language detection for responses. The question or concern focuses on topics relevant to animal welfare and compatibility, such as compatibility with other pets, exercise requirements, medical needs, behavioral characteristics, and adoption fees.

Rate limiting for the animal inquiry endpoint is implemented at the IP address level with a threshold of twenty inquiries per calendar day. This rate limit is more generous than the contact form limit because adoption inquiries represent high-intent user interactions. The rate limit is tracked using in-memory storage with hourly compaction and daily reset cycles. When an IP address exceeds the rate limit, the endpoint returns HTTP 429 Too Many Requests with a response body explaining that the daily limit has been reached and suggesting contact through alternative channels if the limit appears to be in error.

The endpoint response for successful submissions is HTTP 200 OK with a JSON body containing the submission identifier as a UUID, the timestamp of submission creation, confirmation that the inquiry was received successfully, and a message indicating that adoption staff will contact the provided contact information within one to three business days. The response body structure is consistent across all animal inquiry submissions regardless of the animal type or adoption campaign context.

Database persistence occurs through creation of a record in the animal_inquiries table, which includes columns for inquiry identifier, animal identifier, adopter email address, adopter name, phone number, household composition, animal experience level, experience detail, inquiry message, submission timestamp, and soft-delete flag. The soft-delete flag defaults to false and allows logical deletion without removing historical inquiry records from the database, preserving audit trails for animal adoption history and adopter follow-up documentation.

Email notifications are routed through the EPIC-6 Communications system to adoption staff with the email template name adoption_inquiry_received. The template receives context including the animal's name, breed, current age, adopter name, adopter email address, adopter phone number, household composition, animal experience summary, inquiry message, and submission timestamp. The email is sent to a configuration-driven recipient list that may include adoption coordinators, animal specialists assigned to the specific animal, and shelter managers based on deployment-specific routing rules.

Additionally, a confirmation email is sent to the adopter-provided email address using the template adopter_inquiry_confirmation. This confirmation message acknowledges receipt of the inquiry, provides the inquiry identifier for reference, confirms the animal of interest, sets expectations for response timing, and provides alternative contact methods if urgent communication is necessary. Confirmation emails support internationalization with Spanish as the primary language and automatic language selection based on adopter browser or account preferences if available.

Response time targets for the animal inquiry endpoint are identical to the contact form endpoint, with the majority of submissions processed in under five hundred milliseconds. This includes validation, database insertion, rate limit checking, and email notification queuing. Performance optimization focuses on pre-computing animal metadata to avoid lookup overhead during inquiry processing and utilizing database connection pooling to minimize connection establishment latency.

## Acceptance Criteria

The animal inquiry endpoint must accept HTTP POST requests at `/api/v1/animals/{animal_id}/inquiries` with valid path parameters identifying existing animals in the system. The endpoint validates that the specified animal exists in the animals table and is in a status that permits adoption inquiries. Valid statuses are available and reserved. If the animal does not exist or is in an ineligible status such as quarantine, medical hold, or adopted, the endpoint returns an appropriate HTTP error code with a clear message explaining the situation.

Request body validation must enforce all specified field constraints including name length requirements, RFC 5322 email format compliance, phone number format validation, household composition enumeration, age range requirements when applicable, animal experience enumeration, and inquiry message length and content validation. When validation fails on any field, the endpoint returns HTTP 400 Bad Request with a JSON response body containing detailed error information specifying which field failed validation and why.

Rate limiting must be implemented at the IP address level with a threshold of twenty inquiries per calendar day. When an IP address exceeds this limit, the endpoint returns HTTP 429 Too Many Requests and refuses additional inquiries from that IP until the calendar day resets. The rate limit count should be persistent across API server restarts within a single day but may reset on deployment. The endpoint includes response headers indicating the remaining quota and reset time for client-side rate limit awareness.

Upon successful validation and rate limit clearance, the endpoint creates a database record in the animal_inquiries table with all provided information. The record includes a generated UUID identifier, the current timestamp, the animal identifier from the request path, and the adopter-provided information from the request body. The soft-delete flag defaults to false for all newly created inquiries.

Email notifications must be sent to adoption staff through the EPIC-6 Communications system using the adoption_inquiry_received template. The email must include all relevant inquiry information formatted readably with the animal's name, adopter's name, contact information, household composition, experience level, and the inquiry message. The email must be delivered within ten seconds of the inquiry submission, with error handling that logs email delivery failures without blocking the inquiry submission response.

Confirmation emails must be sent to the adopter-provided email address using the adopter_inquiry_confirmation template. The confirmation must arrive within ten seconds of inquiry submission and must include the inquiry identifier, animal name, and expectations for staff follow-up timing. Confirmation email delivery errors must be logged but must not prevent successful inquiry submission, as the inquiry remains created in the database regardless of email delivery status.

The endpoint response for successful submissions must return HTTP 200 OK with a JSON body containing the submission identifier, submission timestamp, and a success message. The response structure must be consistent and must not expose internal database details or system information. Response formatting must be appropriate for frontend consumption with clear success indication and essential information for the adopter's follow-up purposes.

Query performance for animal lookup must be optimized to complete in under one hundred milliseconds. This is achieved through indexes on the animals table primary key and through caching of animal metadata at the application level with a five-minute time-to-live. Database indexes should include composite indexes on animal status and availability timestamp to support efficient filtering during inquiry processing.

## Implementation Considerations

When multiple adoption staff members exist in the system, the email routing mechanism must distribute inquiries appropriately based on deployment configuration. Some deployments may route all inquiries to a single central inbox, while others may distribute based on animal type, assigned specialist, or geographic location. The endpoint implementation must support configurable routing rules specified through environment variables or a configuration file, allowing operational flexibility without code changes.

In distributed deployments with multiple API server instances, rate limiting cannot rely solely on in-memory storage because each instance would maintain separate counters. The implementation must either use a shared cache service such as Redis for rate limit counters or employ a central database query to check the current daily count. For this project's current scale, an in-memory storage approach with a five-minute synchronization mechanism between instances may be acceptable, falling back to a simple count query if rate limit accuracy becomes critical.

The animal inquiry form on the frontend must pre-populate the animal identifier from the URL path and prevent modification by the user. The form must perform client-side validation before submission to provide immediate feedback on invalid inputs, reducing unnecessary server requests. The form must clearly communicate rate limiting policies to discourage rapid repeated submissions for the same animal.

Email validation must include checking against a database or service of known disposable and temporary email providers. The validation may cache this list in memory with periodic refresh intervals to avoid excessive API calls to threat intelligence providers. International email format variations must be supported, including non-ASCII characters in the local part where permitted by mail server implementations. The validation process should reject obviously invalid addresses while accepting valid addresses from unconventional providers.

Database schema design for the animal_inquiries table must include indexes on animal_id, created_at, and email address to support efficient querying for adoption staff. A composite index on animal_id and soft_delete_flag enables rapid retrieval of active inquiries for a specific animal. The email address index supports duplicate inquiry detection if staff wishes to identify multiple inquiries from the same adopter across different animals.

The soft-delete flag convention must be consistently applied across the codebase with all queries filtering out deleted records by default. Any query retrieving animal inquiries for display or analysis must include a WHERE clause filtering for soft_delete_flag = false. A separate administrative function may be required to retrieve deleted inquiries for archival or auditing purposes, with appropriate access restrictions.

Configuration-driven email routing must be externalized from the codebase, allowing operational changes without code deployment. A configuration file or environment variable structure should define recipients based on criteria such as animal type, time of day, and optional specialty areas. For example, a configuration might specify that inquiries for medical-hold animals route to a veterinary staff member while inquiries for healthy animals route to adoption coordinators.

Error messaging must be specific and helpful to users while avoiding exposure of system internals. If an animal does not exist, the message should be "The animal you are interested in is not currently available" rather than "Animal record not found in database." If rate limiting prevents submission, the message should explain that the IP address has exceeded the daily limit and suggest returning tomorrow or contacting staff directly.

The endpoint must handle concurrent submissions from the same IP address gracefully, incrementing the rate limit counter atomically to prevent race conditions where multiple rapid requests bypass the limit. Database transaction isolation levels must be configured to support consistent rate limit enforcement even under high concurrency.

## Success Metrics

The primary success metric for this implementation is the successful creation of inquiry records in the animal_inquiries table for all non-rate-limited, valid submissions. Each inquiry should be independently verifiable through database queries, and the data should match the submitted request body without loss or corruption. Successful submissions should result in an HTTP 200 OK response with a valid submission identifier that can be used for future reference.

Staff email notification delivery represents a critical success metric. Every inquiry should result in an email notification to adoption staff within ten seconds of submission. Notifications should contain complete information about the inquiry with no missing fields or truncated values. Staff should be able to identify the animal of interest, the adopter's name and contact information, and the inquiry message or question without accessing the database directly.

Adopter confirmation email delivery measures the communication effectiveness with prospective adopters. Every inquiry should result in a confirmation email to the adopter-provided address within ten seconds. The confirmation should include the inquiry identifier for future reference, the animal's name to confirm the inquiry's target, and clear expectations for staff follow-up timing. Adopters should understand that they can expect contact within one to three business days and should be provided with alternative contact methods if they need immediate assistance.

Rate limiting effectiveness should be measured by monitoring the distribution of inquiries per IP address across a week or month. The majority of IP addresses should submit fewer than five inquiries, with very few IP addresses approaching the twenty-inquiry daily limit. If rate limiting proves ineffective, the system should detect sustained high-volume submissions from single IP addresses and implement additional protective measures such as temporary IP blocking or CAPTCHA challenges.

Response time measurement should track the endpoint's performance under normal and peak load conditions. The p50 response time should be under two hundred milliseconds, the p95 response time should be under five hundred milliseconds, and the p99 response time should be under one second. Response times should remain consistent across different database states, including when the animals table contains thousands of records. Performance should be tracked through application metrics collection and alerting configured to notify operations teams if response times consistently exceed targets.

Input validation effectiveness should be measured by monitoring the percentage of submissions rejected due to validation errors. A low rejection rate, under five percent, indicates that frontend validation is effective and that users understand the required input format. A high rejection rate suggests that the form design may be confusing or that users may be attempting invalid submissions deliberately, warranting investigation.

Disposable email rejection effectiveness should be tracked to understand how many potential adopters use temporary email addresses for adoption inquiries. If the rejection rate is very high, adoption staff may request changes to the validation rules to allow specific email providers that are popular among target users. The system should log all rejected email addresses for analysis without storing them persistently to protect privacy.

## Testing Strategy

Unit tests for the animal inquiry endpoint should verify that request schema validation functions correctly for all field combinations. Tests should cover valid submissions with minimum, typical, and maximum field lengths. Tests should verify that invalid field values such as malformed email addresses, out-of-range phone numbers, and invalid household composition values all trigger appropriate validation errors. Tests should confirm that missing required fields result in HTTP 400 Bad Request responses with specific field error information.

Unit tests should verify rate limiting logic in isolation, including counter incrementing, daily reset behavior, and limit threshold enforcement. Tests should confirm that exceeding the limit results in HTTP 429 responses and that subsequent requests from the same IP address within the same day are rejected. Tests should verify that the rate limit counter resets at the correct time for different time zones if applicable.

Integration tests should exercise the complete endpoint workflow from request receipt through database insertion and email notification queuing. Tests should verify that successful submissions create database records with all fields populated correctly, that the generated submission identifier is a valid UUID, and that submission timestamps are current. Integration tests should confirm that email notifications are queued correctly and contain expected content.

Integration tests should verify email routing logic by confirming that notifications are sent to the correct staff members based on deployment configuration. Tests should exercise different routing rules and confirm that configuration changes are reflected in email distribution without requiring code changes.

Performance tests should submit large volumes of inquiries under realistic load conditions to verify that response times remain within target ranges. Tests should measure response time distribution and identify any queuing or contention that might occur under peak load. Tests should verify that database connection pooling is configured appropriately to handle concurrent requests without exceeding resource limits.

Security tests should attempt to bypass rate limiting through header manipulation, IP address spoofing, and other common attack vectors. Tests should verify that the rate limiting implementation is resistant to distributed attacks where multiple clients attempt to circumvent the limit. Tests should attempt SQL injection through all user-provided input fields to confirm that parameterized queries prevent injection attacks. Tests should verify that email addresses cannot be used to enumerate existing animals or adopters.

End-to-end tests should simulate complete adopter workflows from animal browsing through inquiry submission and confirmation email receipt. Tests should verify that the inquiry form on the public portal correctly populates the animal identifier and that the submission successfully creates a record in the backend system. Tests should confirm that adopters receive confirmation emails and that staff members receive inquiry notifications.

## Dependencies and Constraints

This implementation depends on the successful completion of EPIC-6 Communications, which provides the email notification system required to send inquiry confirmations to adopters and notifications to adoption staff. The EmailService component from EPIC-6 must be available and correctly configured for both staff and adopter email routing.

The implementation depends on the animal management system and animals table schema being correctly implemented with appropriate status enumeration and indexing. The animals table must support queries filtering by status and must correctly reflect the current state of animals in the shelter system.

The implementation constrains database schema by introducing the animal_inquiries table with required columns for inquiry identifier, animal identifier, adopter contact information, household and experience details, inquiry message, submission timestamp, and soft-delete flag. This table requires indexes on animal_id, created_at, and a composite index on animal_id and soft_delete_flag for efficient querying.

The implementation requires rate limiting infrastructure capable of tracking inquiries per IP address with daily reset cycles. If in-memory rate limiting is used, a synchronization mechanism must exist for distributed deployments with multiple API server instances. If a shared cache service like Redis is used, the connection pooling and failover logic must be configured appropriately.

Response time constraints require that animal metadata be accessible without additional database lookups during inquiry processing. This may necessitate caching of animal name, breed, and status at the application level, with cache invalidation mechanisms when animal records are updated.

The implementation requires configuration support for email routing rules, rate limit thresholds, and email template selection. These configurations should be externalized from the codebase to allow operational changes without code redeployment. Configuration should support environment-specific variations for development, staging, and production deployments.

The implementation constrains API design by requiring a path parameter for animal identification, consistent with RESTful API principles. The endpoint URL must be `/api/v1/animals/{animal_id}/inquiries` to maintain consistency with other animal-specific endpoints in the public portal API.

The implementation requires that all user input validation be performant enough to complete within response time targets. Complex validation rules such as disposable email detection must be implemented efficiently, potentially utilizing cached data or simplified validation rules rather than real-time threat intelligence queries.

The implementation is constrained by GDPR and data protection compliance requirements, which mandate secure handling of adopter contact information and inquiry messages. Data retention policies must be defined and enforced, with mechanisms for secure deletion of inquiry data after defined retention periods. Adopter consent for marketing communications must be explicitly requested and stored separately from inquiry submission.
