# RAP-053 Plan

## Objective
Wire adoption event publishing into API endpoints and add email notification handlers for adoption lifecycle events.

## Description
Adoption request creation and status changes should publish domain events via the event bus. Email notifications should be sent to adopters (confirmation) and staff (alerts) when new applications are submitted, and to adopters when their request status changes.

## Acceptance Criteria
- [x] AdoptionRequestCreated domain event class and factory function exist
- [x] POST /adoption-requests publishes AdoptionRequestCreated event
- [x] POST /public/adoption-applications publishes AdoptionRequestCreated event
- [x] PATCH /adoption-requests/{id}/status publishes AdoptionStatusChanged event
- [x] Email handler sends adopter confirmation on new request
- [x] Email handler sends staff alert on new request
- [x] Event publishing is conditional on bus.is_running (graceful when bus down)
- [x] Unit tests cover event creation and handler registration
- [x] Integration tests cover API endpoints with event bus

## Complexity Assessment
**Track**: Complex Implementation
- Multiple files affected (3 API endpoints, domain events, handlers, templates)
- Cross-cutting concern (event bus integration across API layer)

## Approach
1. Add AdoptionRequestCreated domain event class + factory
2. Wire event_bus dependency into adoption endpoints
3. Add notification handler + email templates
4. Add integration conftest event bus fixture
5. Write unit and integration tests
