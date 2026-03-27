# RAP-155 Plan

## Objective
Create a dedicated Subscription model and service layer for managing recurring Stripe donations with proper lifecycle tracking.

## Description
The existing codebase has basic subscribe/cancel endpoints in the SEPA router, but subscriptions are tracked only via fields on the Donation model. This story creates a proper Subscription table to track subscription lifecycle (active, paused, canceled, past_due), a dedicated service layer, and a subscriptions router with full CRUD + list endpoints.

## Acceptance Criteria
- [ ] Subscription SQLAlchemy model with proper status enum and lifecycle fields
- [ ] Alembic migration for subscriptions table
- [ ] Subscription service layer handling Stripe API interactions
- [ ] Dedicated subscriptions router with create, list, get, cancel endpoints
- [ ] Enhanced webhook handlers for subscription lifecycle events
- [ ] Unit and integration tests with 80%+ coverage
- [ ] All quality gates pass (ruff, black, pytest)

## Complexity Assessment
**Track**: Complex Implementation

- Multiple files affected (model, schema, service, router, webhooks, migration)
- Stripe API integration with subscription lifecycle
- Webhook handler enhancements
- New test coverage needed

**Assessment result**: Complex — new model + service + router + webhook enhancement

## Approach
1. Create Subscription model and migration
2. Create Pydantic schemas
3. Create subscription service
4. Create subscriptions router
5. Enhance webhook handler for subscription events
6. Register router in app.py
7. Write unit and integration tests

## Dependencies
- Depends on: EPIC-31 (SEPA integration) - DONE
- Depends on: Existing donation/donor models - available

## Risks
- Risk: Stripe subscription API complexity -> Mitigation: Follow existing SEPA patterns, mock in tests
