# RAP-152 Plan

## Objective
Add SEPA-specific webhook event handlers: payment_intent.processing, setup_intent.succeeded/failed, mandate.updated.

## Acceptance Criteria
- [ ] payment_intent.processing handler keeps donation pending (SEPA async)
- [ ] setup_intent.succeeded handler logs mandate saved
- [ ] setup_intent.setup_failed handler logs mandate failure
- [ ] mandate.updated handler logs status changes (warns on inactive)
- [ ] All new events in HANDLED_EVENT_TYPES constant
- [ ] 6 integration tests covering all new event types
