# RAP-234 Plan

## Objective
Publish a public sub-processor registry listing all third-party services that may process personal data on behalf of the shelter.

## Acceptance Criteria
- [ ] GET /legal/sub-processors returns registry
- [ ] Lists: Stripe, Twilio, SMTP provider, Sentry, Hostinger, AWS/S3
- [ ] Each entry: name, role, data processed, purpose, data location, DPA availability
- [ ] GDPR Article 28(3)(d) basis documented
- [ ] 11 unit tests passing

## Complexity Assessment
**Track**: Simple Fix — stateless GET endpoint, no DB.

## Approach
1. Create src/api/sub_processor_registry.py
2. Register router in app.py
3. Write 11 unit tests
