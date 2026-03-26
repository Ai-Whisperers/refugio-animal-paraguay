---
epic_id: EPIC-11
title: Public Portal
status: ready
created_at: 2026-03-25
updated_at: 2026-03-25
type: feature
priority: high
epic_owner: backend-team
---

# EPIC-11: Public Portal

## Overview

The Public Portal is the primary public-facing interface of the Refugio Animal Paraguay platform, designed to showcase adoptable animals, facilitate visitor inquiries, provide educational content about the shelter and animal care, and drive donations through campaign landing pages. This epic encompasses the complete backend infrastructure needed to support a dynamic, user-friendly portal that serves both prospective adopters and the general public interested in supporting the shelter's mission.

The Public Portal operates as an unauthenticated experience for visitors while providing staff and administrators with backend capabilities to manage content, campaigns, and submissions. It represents a critical touchpoint between the shelter and its community, combining functional discovery (finding animals to adopt) with informational content (learning about rescue operations) and conversion funnels (donating and submitting inquiries).

## Scope

The Public Portal epic includes four main user stories spanning animal discovery, form submission, educational content delivery, and donation campaign management. Each story encompasses both the API endpoints required to deliver information to the frontend and, where applicable, the administrative backend tools needed to manage that information.

The animal browsing and search functionality allows visitors to browse all available animals (excluding those in quarantine, under medical hold, reserved, or already adopted) with comprehensive filtering and search capabilities. The contact and inquiry forms enable visitors to submit general inquiries about the shelter or express interest in specific animals for adoption. The about and educational pages deliver dynamic content about the shelter's mission, team, programs, and animal care education. The donation landing pages showcase active campaigns, display donation totals, and integrate with Stripe for payment processing.

All endpoints in the Public Portal are accessible without authentication, though rate limiting is applied to form submission endpoints to prevent abuse. The backend infrastructure supports multilingual content (Spanish primary, Dutch with fallback), in-memory caching with five-minute time-to-live for frequently accessed content, and soft deletes for campaigns and content to maintain historical data integrity.

## Stories

1. **S01: Animal Browsing and Search** — Implement publicly accessible endpoints that allow visitors to browse all available animals with comprehensive filtering (species, breed, age, size, gender, medical status) and search capabilities. Includes both animal listing with pagination and detailed animal profile endpoints.

2. **S02: Contact and Inquiry Forms** — Implement form submission endpoints for general contact inquiries and animal-specific adoption inquiries, including rate limiting, email notification integration, and form submission tracking in the database.

3. **S03: About and Educational Pages** — Implement content delivery endpoints for shelter information, team profiles, educational articles about animal care and rescue operations, and program descriptions. Includes administrative backend for staff to manage portal content with versioning and publication control.

4. **S04: Donation Landing Pages** — Implement campaign listing endpoints, real-time donation total computation, Stripe payment link integration, and administrative backend for creating and managing donation campaigns with metrics tracking.

## Dependencies

The Public Portal depends on several other epics:

- **EPIC-1: Core Animal Management** — The animals table and animal status management are foundational; the Public Portal queries available animals from this system.

- **EPIC-6: Communications** — Email notification system used to send confirmation messages to form submitters and notification emails to staff when inquiries are received.

- **EPIC-9: Donations and Financial** — The donations table and Stripe integration; the Public Portal displays aggregated donation totals and integrates with Stripe payment links for campaign donations.

The Public Portal is a horizontal dependency for the frontend application, which will consume all public endpoints. It establishes the baseline content and interaction model for the platform.

## Success Metrics

Success for the Public Portal is measured across several dimensions:

- **API Availability and Performance**: All public endpoints maintain 99.5% uptime with response times under 500 milliseconds for list endpoints and under 200 milliseconds for cached content. Rate limiting effectively prevents form submission abuse without impacting legitimate users.

- **Content Completeness**: All animal records available for adoption are accurately displayed with complete information including photos, medical history summaries, and behavioral notes. Educational content is current and reflects the shelter's actual programs.

- **Donation Funnel**: Donation campaign pages load quickly, donation totals display accurately and update in real time, and the Stripe integration successfully processes donations with clear confirmation feedback.

- **Form Submission Quality**: Contact and inquiry forms capture complete, valid information; submissions are reliably stored in the database and trigger appropriate notification emails to staff.

- **Multilingual Support**: Content endpoints serve Spanish content by default with Dutch fallback available when requested via language headers. Content management backend allows staff to maintain translations independently.

## Risk Factors

Several risks require mitigation:

- **Form Abuse Through Rate Limiting Bypass**: Determined attackers might attempt distributed submissions or IP spoofing. Mitigation includes additional validation such as email verification requirements and CAPTCHA integration if abuse patterns emerge.

- **Search Performance Degradation**: As the animal database grows, unoptimized search queries could slow response times. Mitigation includes database indexing on frequently filtered fields (species, gender, age range) and query optimization reviews before production.

- **Cache Invalidation Complexity**: In-memory caching with five-minute TTL could lead to stale content if campaigns or content are updated and the cache isn't properly invalidated. Mitigation includes explicit cache invalidation on content updates and comprehensive testing of cache behavior.

- **Stripe Integration Failures**: Payment processing failures could leave inconsistent states between the Stripe dashboard and the local database. Mitigation includes webhook handling for payment confirmation, reconciliation procedures, and clear error messaging to users.

- **Scalability of Donation Total Computation**: Real-time aggregation across the donations table could become slow at scale. Mitigation includes caching the aggregated total with background job updates rather than computing on every request.

## Technical Notes

### Database Tables

The Public Portal primarily queries and writes to several tables:

- **animals** — From EPIC-1, filtered where status is 'available' (excluding quarantine, medical_hold, reserved, adopted).

- **portal_content** — Stores shelter information, team profiles, educational articles, and about pages. Includes fields for content type, language, title, body, publication status, and timestamps.

- **donation_campaigns** — Stores active and past donation campaigns with campaign name, description, target amount, current total (computed), Stripe payment link URL, start date, end date, and publication status.

- **form_submissions** — Stores contact and inquiry form submissions with submitter name, email, phone, submission type (contact or animal inquiry), related animal ID (if applicable), message body, submission timestamp, and staff response status.

### API Endpoints

**Animal Browsing**: GET endpoints for listing animals with pagination, filtering (species, breed, age, size, gender, medical status), and search by name. GET endpoint for individual animal detail with full profile.

**Contact Forms**: POST endpoint accepting contact form submissions (name, email, phone, message, captcha token). Rate limited to 10 requests per hour per IP address.

**Animal Inquiries**: POST endpoint accepting animal-specific inquiries (animal ID, name, email, phone, message, captcha token). Rate limited to 10 requests per hour per IP address.

**Content Delivery**: GET endpoints for about page content, team profiles, educational articles, and program descriptions. Cached with five-minute TTL.

**Donation Campaigns**: GET endpoint listing active campaigns with donation totals. GET endpoint for individual campaign detail including Stripe payment link.

**Administrative**: POST endpoints for creating campaigns, updating campaign status, managing portal content (restricted to authenticated staff). PATCH endpoints for updating campaign metrics and content publication status.

### Caching Strategy

In-memory caching is implemented for animal listings (paginated), content pages, and campaign listings. Cache entries expire after five minutes or are explicitly invalidated when underlying data changes. Search queries and filter combinations are not cached due to combinatorial complexity; instead, database query optimization and indexing ensure adequate performance.

### Multilingual Content

All content endpoints accept an optional Language header (default: Spanish). Content endpoints return Spanish by default; Dutch translations are included in the response when available. The content management backend allows staff to maintain Spanish and Dutch versions of content independently.

### Security Considerations

All public endpoints are unauthenticated and do not require JWT tokens. Form submission endpoints are protected by rate limiting and optional CAPTCHA validation. Email addresses captured through forms are stored securely and used only for shelter communication. No personally identifiable information from form submissions is exposed through public API endpoints.

## Acceptance Criteria

The Public Portal epic is complete when:

- All four stories and their associated tasks are fully implemented and tested.

- All public endpoints are accessible without authentication and return data in the correct format with appropriate status codes.

- Rate limiting is enforced on form submission endpoints without impacting legitimate users.

- Animal listings accurately reflect availability status from the animals table.

- Educational content is complete and current.

- Donation campaigns display accurate totals and Stripe integration functions correctly.

- Form submissions are reliably stored and trigger notification emails via EPIC-6.

- All endpoints maintain performance targets (list endpoints under 500ms, cached endpoints under 200ms).

- Multilingual content support is functional for Spanish and Dutch.

- Code review passes and all quality gates are met.
