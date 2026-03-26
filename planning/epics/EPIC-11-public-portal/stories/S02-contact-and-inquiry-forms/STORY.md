---
epic_id: EPIC-11
story_id: S02
title: Contact and Inquiry Forms
status: ready
type: user_story
priority: high
story_owner: backend-team
estimated_points: 8
created_at: 2026-03-25
updated_at: 2026-03-25
---

# Contact and Inquiry Forms

## User Story

As a visitor to the Refugio Animal Paraguay website, I want to submit contact inquiries and animal-specific questions through structured forms, so that I can communicate with the shelter about adoption interest, general questions, or concerns without requiring account creation.

## Overview

This story covers the implementation of two primary form submission endpoints for unauthenticated public visitors: a general contact form for inquiries, messages, and feedback, and an animal-specific inquiry form for visitors interested in adopting or learning more about particular animals currently in the shelter. These forms represent critical touchpoints for public engagement and must function reliably with robust rate limiting, validation, and notification integration.

The contact form serves as a general communication channel, accepting visitor name, email address, subject matter, and detailed message content. This form accommodates various inquiry types including adoption questions, volunteering interest, donation inquiries, and general feedback about the shelter operations or website. The system must validate all inputs for format correctness, enforce rate limiting to prevent spam and abuse, and route submissions to appropriate staff members through the email notification system.

The animal inquiry form builds on the contact form functionality by allowing visitors to express specific interest in adoption or inquiry about a particular animal. This form includes the same core visitor identification fields as the contact form, supplemented with selection of the specific animal and additional context about the visitor's interest in that particular animal. The system must verify that the selected animal exists and remains available for adoption, record the inquiry with appropriate metadata about timing and source, and notify both the relevant staff members and the visitor through automated confirmation messages.

Both forms must implement strict rate limiting at the IP address level to prevent abuse. The system enforces a limit of ten form submissions per hour per unique IP address. Rate limiting tracking uses in-memory storage with automatic expiration of old requests to prevent memory bloat. When a visitor exceeds the rate limit, the system returns a 429 Too Many Requests status code with a clear message indicating the time when the visitor can submit another form.

Form submissions flow through the email notification system established in EPIC-6 Communications, which manages delivery to appropriate staff members and automated responses to visitors. This integration ensures that submissions do not create unnecessary burden on shelter staff by automating routine acknowledgments and routing messages to specialized teams based on inquiry type.

The system stores all form submissions in the database for audit trail, analysis, and follow-up purposes. Storage includes visitor contact information, timestamp of submission, IP address for security and rate limiting purposes, form type identifier, and all submitted content. The database design supports soft-delete semantics to preserve historical records while allowing staff to mark records as deleted for privacy or other purposes.

Performance requirements for form submission endpoints are strict: the API must accept and acknowledge form submissions within 500 milliseconds under normal conditions, and must never block the visitor while processing email notifications. All email notification processing happens asynchronously through background job processing, ensuring that the visitor receives immediate feedback without waiting for mail service responses.

Error handling must be graceful and informative. When validation fails, the system returns detailed error messages explaining which fields contain invalid data and why the validation failed. The system provides helpful suggestions for correction, such as pointing out that email addresses must contain an at-sign or that messages must be at least twenty characters in length. When the visitor has exceeded rate limits or when unexpected server errors occur, the system returns appropriate error codes and messages without exposing internal system details.

## Acceptance Criteria

The contact form endpoint accepts HTTP POST requests at `/api/v1/contact` with required fields of visitor name, email address, subject, and message body. The endpoint validates that the name contains between three and one hundred characters, that the email address conforms to international email standards and is not flagged as a disposable domain address, that the subject contains between ten and two hundred characters, and that the message body contains between twenty and five thousand characters. Upon successful submission, the endpoint returns a 201 Created status code with a submission confirmation including a unique identifier and timestamp. The system sends an automated confirmation email to the visitor and routes the submission to staff members based on subject categorization.

The animal inquiry form endpoint accepts HTTP POST requests at `/api/v1/animals/{animal_id}/inquiries` with required fields of visitor name, email address, and reason for interest. The endpoint validates visitor name and email using the same constraints as the contact form. The endpoint verifies that the specified animal exists in the database and has not been deleted. The endpoint accepts optional fields including visitor zip code, household information, and existing pet information for adoption eligibility assessment. Upon successful submission, the endpoint returns a 201 Created status code with an inquiry confirmation. The system sends a confirmation email to the visitor and routes the inquiry to the adoption coordinator team.

Rate limiting is enforced at the IP address level for both forms, limiting each unique IP to ten submissions per hour across both endpoints combined. When the rate limit is exceeded, the endpoint returns a 429 Too Many Requests status code with a message indicating when the visitor can submit another request. The rate limiting counter resets after sixty minutes from the oldest submission in the rate limit window.

Both endpoints reject requests from known VPN, proxy, or abuse source IP addresses through integration with a threat intelligence provider. When a request originates from a flagged IP, the endpoint returns a 403 Forbidden status code indicating that the service is not available from that IP address.

All form submissions are stored in the database with soft-delete capability, preserving records for audit and follow-up purposes while allowing staff to mark submissions as deleted. The system records the visitor IP address, submission timestamp, form type, and all submitted content for security audit and analysis.

## Success Metrics

The success of this story is measured through multiple dimensions of functionality and performance. The contact form endpoint must successfully accept and process ninety-nine percent of valid submissions within five hundred milliseconds, measured consistently across all hours of operation. The animal inquiry endpoint must achieve the same performance targets while correctly identifying and validating the referenced animal in ninety-nine percent of submissions.

Rate limiting must function correctly, rejecting all submissions that exceed the ten-per-hour limit while accepting all submissions that fall within the rate limit. Verification that rate limiting blocks exactly at the boundary is critical—the eleventh submission within an hour must be rejected while the first submission of the next hour must be accepted.

Email notification integration must deliver confirmation messages to visitors within five minutes of successful form submission in ninety-eight percent of cases. Staff notification delivery must achieve the same performance target. Visitors must report satisfaction with automated confirmation messages, indicating that the messages provide clear acknowledgment of receipt and expected follow-up timeline.

Form validation must reject invalid submissions while accepting all valid submissions. Specific validation success metrics include correct identification of invalid email addresses with zero false positives or false negatives, correct validation of name and subject length constraints, and correct validation of message body length constraints. The system must reject disposable domain email addresses while accepting all legitimate domain addresses.

The security metric of blocking submissions from known abuse sources must function correctly, rejecting all submissions from flagged IP addresses while accepting submissions from legitimate IP addresses with zero false positives.

## Technical Considerations

The contact form endpoint implementation requires careful consideration of email validation. Rather than using simplistic regular expressions, the system uses a dedicated email validation library that understands international email standards including non-ASCII characters valid under modern email specifications. The system maintains a live list of disposable email domain addresses, updating this list daily to prevent misuse through temporary email services. The email validation failure should not cause the entire request to fail but instead should be reported as a validation error allowing the visitor to correct the address.

The animal inquiry endpoint requires database query to verify that the specified animal exists and is not deleted. This query must use appropriate database indexing to complete within the response time budget. If the animal does not exist or has been deleted, the endpoint returns a 404 Not Found error indicating that the animal cannot be found, without revealing whether the animal was deleted or never existed.

Rate limiting implementation must use efficient in-memory tracking that does not require external services like Redis. The implementation tracks all submissions per IP address within the rolling one-hour window, removing old entries automatically to prevent memory exhaustion. The system uses a sliding window algorithm that counts submissions within the last sixty minutes, allowing for smooth operation as submissions age out of the rate limit window.

IP address extraction must correctly identify the visitor's actual IP address even when requests pass through proxy servers or load balancers. The system reads the X-Forwarded-For header when present, using the leftmost IP address as the visitor's actual address. The system must validate this header to prevent IP spoofing attacks where a malicious visitor falsifies the header. The implementation uses configuration to specify trusted proxy servers, accepting the X-Forwarded-For header only from requests originating from these trusted intermediaries.

Form submission storage must include comprehensive audit trail data including submission timestamp, visitor IP address, form type, and all user-submitted content. The database schema uses soft deletes with a deleted_at timestamp column, allowing staff to mark submissions as deleted while preserving the data for forensic analysis. The system records whether each submission has been responded to, allowing staff to track follow-up status.

Email notification integration through EPIC-6 establishes asynchronous processing of all email messages. The system enqueues email jobs with complete message details and recipient information, immediately returning success to the API response. The background job processor handles retries, bounce tracking, and logging. This asynchronous pattern ensures that mail service latency or failures do not impact the API response time or user experience.

Subject-based categorization of contact form submissions routes messages to appropriate staff teams. The system analyzes the subject line and message content to categorize submissions into categories such as adoption inquiry, volunteering, feedback, complaint, other inquiry. Each category routes to different staff members based on configured routing rules. Submissions that do not clearly match any category route to a general inquiry inbox for manual sorting. The categorization logic must be robust against unusual capitalization, spelling variations, and language preferences.

Error messages returned to the user must be helpful and specific about validation failures. Rather than returning a generic error message, the system identifies exactly which field failed validation and why. The message indicates whether the problem is that the field is missing, too short, too long, in invalid format, or contains disallowed content. The error response includes suggestions for correction where helpful.

## Risk Mitigation

The primary risk for this story involves spam and abuse of the form submission endpoints. High-volume submissions could overwhelm staff or block legitimate submissions. Rate limiting at the IP level mitigates this risk by enforcing a strict limit of ten submissions per hour. Additional mitigation includes integration with threat intelligence providers to block submissions from known abuse sources, and monitoring of submission patterns to detect and respond to new abuse attempts.

Another significant risk involves incorrect email address validation causing the system to reject legitimate addresses or accept invalid addresses. This risk is mitigated through use of a tested email validation library rather than custom regex patterns, and through maintaining updated lists of disposable domain addresses. The system includes comprehensive testing of email validation across diverse international formats.

Visitor confusion about form submission is another risk. Visitors might not understand that the system is handling their submission and might not receive confirmation messages, leading to duplicate submissions or lost communications. This risk is mitigated through clear confirmation messages, automated replies sent immediately upon form submission, and prominently displayed information about expected staff response timeframes.

Data privacy and security of form submissions poses a risk, particularly if the system stores personally identifiable information without appropriate safeguards. This risk is mitigated through secure database storage with appropriate access controls, soft-delete capability to remove submissions when requested by visitors, and clear privacy policies communicated to visitors before form submission. The system logs all access to form submission data for audit trail purposes.

## Dependencies

This story depends on successful completion of EPIC-6 Communications for email notification system integration. The contact and inquiry form endpoints require the ability to send automated confirmation messages to visitors and notifications to staff members. Specific dependencies include the email template system for rendering dynamic content and the background job processor for asynchronous message delivery.

This story depends on successful completion of EPIC-10 Authentication for role-based access control systems that staff members use to view and manage form submissions. Staff members with appropriate roles must be able to view submitted forms, mark submissions as resolved, and potentially re-contact visitors.

This story depends on the public database schema established in EPIC-5 Database Architecture, particularly the form_submissions table for storing contact and inquiry form data with appropriate columns for audit trail, soft-delete tracking, and categorization.

This story depends on the API framework established in EPIC-9 API Foundation, particularly the HTTP request handling, validation framework using Pydantic v2, error response formatting, and middleware support for rate limiting and security headers.

## Related Stories

This story relates directly to S01-animal-browsing-and-search, which provides the animal detail pages from which visitors access the animal inquiry form. The two stories work in concert to enable the public to discover animals and then express interest through the inquiry form.

This story precedes S03-about-and-educational-pages and S04-donation-landing-pages, which also require contact form functionality for visitor engagement. A shared contact form endpoint serves multiple purposes across the portal.

This story coordinates with EPIC-10 Authentication on staff access to form submissions through authenticated endpoints that display submissions and enable response management.
