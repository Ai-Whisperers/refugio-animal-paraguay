# RAP-209 Plan

## Objective
Implement one-click email unsubscribe so users can opt out of all email notifications from a signed link without needing to log in.

## Description
Adds a signed JWT-based unsubscribe flow to the notification preferences system. Authenticated users can request an unsubscribe link; clicking the link (which requires no authentication) disables all email notification preferences for that user.

## Acceptance Criteria
- [ ] `GET /notification-preferences/unsubscribe-link` (authenticated) returns a signed URL
- [ ] `GET /notification-preferences/unsubscribe?token=<token>` (public) processes unsubscribe
- [ ] Token is a signed JWT containing user_id and purpose="unsubscribe"
- [ ] Token has 30-day expiry
- [ ] Unsubscribe disables all email channel preferences for the user
- [ ] Invalid/expired tokens return 400
- [ ] Service function `unsubscribe_email` disables all email preferences
- [ ] Unit tests for token generation, validation, and unsubscribe
- [ ] Integration tests for both endpoints

## Complexity Assessment
**Track**: Simple Fix

**Assessment result**: Complex — new service functions, new endpoints (authenticated + public), JWT token flow

## Approach
1. Add `generate_unsubscribe_token` and `process_unsubscribe` to service
2. Add `unsubscribe_all_email` to preference service
3. Add schema for unsubscribe link response
4. Add endpoints to existing notification_preferences router
5. Write unit and integration tests

## Dependencies
- Depends on: RAP-205 (notification preference model) ✓ DONE
- Uses: python-jose (already in project dependencies)

## Risks
- Token must not be guessable — uses HMAC-signed JWT with secret_key
