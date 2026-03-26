---
epic_id: EPIC-19
epic_title: API Platform & Integrations
epic_status: planned
created_date: 2026-03-26
last_updated: 2026-03-26
epic_owner: Platform & Partnerships
target_release: FPUNA-2026 Wave 4
priority: medium
estimated_effort: 32 story points
---

# EPIC-19: API Platform & Integrations

## Overview

This epic exposes Refugio Animal Paraguay's core data and capabilities as a public API and develops integrations with external systems critical to Paraguayan animal welfare operations. The public API enables partner veterinary clinics, government animal control agencies, and other shelters to query animal records, submit intake reports, and coordinate care. Integration with government animal registration systems (if available) enables Refugio to contribute to national animal welfare tracking. Integration with payment partners (Tigo Money, local banks) enables donation receipt in PYG through payment channels accessible to Paraguayan donors.

The API platform positions Refugio as a data and operational hub for the animal welfare ecosystem in Paraguay, potentially opening partnership opportunities with government, NGOs, and other organizations while maintaining appropriate data security and privacy controls.

## Why This Epic Matters

Paraguay's animal welfare infrastructure is nascent. Refugio, as a professionally-run shelter backed by European funding, is positioned to be a center of excellence and data hub. Exposing well-designed APIs enables partner veterinary clinics to mark animals they've treated as "registered with Refugio," government agencies to track animal welfare incidents, and other shelters to participate in a shared database.

From a donor perspective, particularly for EU funders, demonstrating that the organization works within broader ecosystem (government partnerships, veterinary collaborations, national coordination) enhances credibility and impact perception.

Payment integration enables accepting donations from Paraguayan citizens using local payment methods, expanding the donor base beyond international wire transfers to include microtransactions via mobile money (Tigo Money, Viva, Personal).

## Target Users

**Partner Veterinary Clinics**: Query animal records, update treatment status, coordinate care, report intakes.

**Government Animal Control Agencies**: Access aggregated animal data for policy/statistics, report suspected abuse cases, coordinate rescues.

**Other Animal Shelters**: Search for animals in Refugio database, coordinate transfers, share resources/expertise.

**Payment Partners (Tigo, Banks)**: Receive notifications of completed donations, update Refugio of successful payments.

**API Consumers (Third-Party Developers)**: Build applications using Refugio data with appropriate permissions.

**Internal Systems**: Refugio's own web/mobile platforms consume the same API, ensuring consistency.

## Scope: In Scope

Public REST API with comprehensive authentication and authorization supporting read access to public animal data (non-sensitive fields like name, type, adoption status) and write access for partner organizations (veterinary clinics submitting treatment updates, intake reports). Role-based access control enabling different API consumers to have different capabilities.

API versioning and backward compatibility ensuring existing integrations continue working as platform evolves.

Webhook system enabling third-party systems to receive notifications when animals are adopted, medical procedures are completed, or critical health alerts occur. Webhook delivery with retry logic and audit logging.

Integration with government animal registration systems (if existing API available in Paraguay). Research phase required to identify available systems.

Integration with payment partners (Tigo Money, local banks) enabling donation receipt notifications and webhook delivery to backend for payment reconciliation.

Rate limiting and quota management preventing abuse while accommodating legitimate high-volume usage.

API documentation (OpenAPI/Swagger), code examples, and SDK for common languages (Python, JavaScript) enabling rapid partner integration.

API usage analytics and monitoring enabling Refugio to track integration health and partner usage patterns.

Security: API key authentication, JWT token support, HTTPS only, rate limiting, IP whitelisting for sensitive operations.

PII protection: API never returns sensitive data (adopter email, donor names, staff phone) to unauthorized consumers. Public-facing data is anonymized.

## Scope: Out of Scope

GraphQL API (REST only). Real-time streaming API. Advanced search/filtering beyond basic parameters. Machine learning recommendations. Cross-border federation with shelters in other countries. Advanced audit logging for compliance (basic logging only). Custom reporting builder for partners. Support for legacy XML-based systems. Integration with non-Paraguayan government systems.

## Stories

This epic consists of four major stories. Story S01 designs and implements the public API architecture, authentication, and core animal/adoption endpoints. Story S02 builds webhook system with delivery guarantees and partner management. Story S03 implements payment partner integrations (Tigo Money, local banks) for donation processing. Story S04 develops integrations with government animal registration systems and creates API documentation and SDKs.

## Dependencies

This epic depends on stable core API (EPIC-03) and donation system (EPIC-04). Government registration system APIs must be researched and documented before implementation. Payment partner APIs (Tigo Money, banks) must be evaluated for feasibility. Legal/compliance review needed for data sharing agreements with government and partners. API design and security review should involve external security consultant.

## Success Metrics

API adoption is successful when at least 2 partner veterinary clinics integrate with API within first year, government agencies (if partnership formed) use API for data reporting, and third-party integrations are built and maintained by partners.

Webhook reliability is successful when 99.9% of webhooks are delivered, delivery latency averages <5 seconds, and partner systems report >95% successful processing of received webhooks.

Payment integration success measured by percentage of donations received via Tigo Money (target: 10% of total donations), successful payment reconciliation (zero orphaned payments), and daily donation processing automation reducing manual work by 80%.

API performance requires response time <500ms for 95th percentile queries, supporting at least 1,000 concurrent API consumers, and graceful degradation under overload (rate limiting, not errors).

Documentation quality measured by partner feedback on usability, SDK adoption rates for provided libraries, and support ticket volume (low indicates good documentation).

## Risk Factors

**Data security risk**: Exposing APIs increases attack surface. Mitigated by authentication on all endpoints, role-based authorization, rate limiting, IP whitelisting for sensitive operations, security audit before launch, and monitoring for suspicious activity.

**Privacy risk**: Accidentally exposing PII through API. Mitigated by data classification, explicit removal of sensitive fields in API responses, comprehensive testing, and clear data sharing agreements with partners.

**Integration maintenance burden**: Supporting multiple external systems and their API changes. Mitigated by well-designed API abstraction layer, partner notification procedures for breaking changes, and limiting number of active integrations.

**Government/regulatory risk**: Government policies on data sharing or animal welfare systems could change. Mitigated by flexibility in integration design, clear data sharing agreements, and ability to disable integrations if required.

**Partner reliability risk**: Partner systems going offline or breaking integration. Mitigated by comprehensive error handling, fallback procedures, and clear SLAs in partnership agreements.

**Payment integration complexity**: Each payment partner has different requirements, error handling, reconciliation. Mitigated by abstracting payment partner specifics behind unified interface, comprehensive testing with each partner, and maintaining close relationship with payment partners.

## Technical Notes

The API is built on FastAPI (existing platform) with OpenAPI documentation auto-generated. Authentication uses API keys (for servers) and JWT tokens (for user sessions). Rate limiting implemented via dependency injection, configurable per API key/client.

API endpoints follow RESTful conventions with resource-based URLs: GET /animals/{id}, POST /intakes, PATCH /animals/{id}/medical-records. Filtering, sorting, and pagination use query parameters with standardized conventions.

Webhook system uses a webhook_subscriptions table storing consumer info, event types they're interested in, and URL to receive notifications. An outgoing_webhooks queue stores payloads to be delivered with status (pending, delivered, failed). A retry job attempts delivery with exponential backoff. All webhook deliveries are logged in audit_log for compliance.

Payment integration uses an abstract PaymentProvider interface with implementations for TigoMoney, BancoParaguayo, etc. Each provider handles their specific API quirks internally. When payment is received, webhook is sent to payment/donation system, which creates a donation record.

Government integration (if implemented) uses either webhook consumption (if government system can send updates) or polling (if only query API available). A government_sync_log tracks what data has been shared and when for audit purposes.

API keys are stored hashed (SHA256) in database. Token rotation is enforced; old keys are deprecated gradually with partner notification.

Security headers (CORS, CSP, HSTS) are configured. All traffic is HTTPS only. SQL injection and other OWASP vulnerabilities are addressed through parameterized queries, input validation, and framework-level protections.

SDKs are generated via OpenAPI CodeGen for Python and JavaScript. Python SDK distributed via PyPI, JavaScript SDK via npm.

