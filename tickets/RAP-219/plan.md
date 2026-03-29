# RAP-219 Plan

## Objective
Add A/B subject line testing to email campaigns.

## Acceptance Criteria
- [x] subject_a, subject_b, ab_ratio columns added to email_campaigns (migration 087)
- [x] EmailCampaign model and Pydantic schemas updated with A/B fields
- [x] is_ab_test_active() helper detects A/B mode
- [x] split_recipients_by_variant() deterministic split by ratio (ceil for variant A)
- [x] initiate_send_ab() service with state-machine validation and variant counts
- [x] POST /email-campaigns/{id}/send/ab endpoint (staff only, 409 without subject_b)
- [x] 14 unit tests (split edge cases, send validation, detection)
- [x] 8 integration tests (create, patch, send, error paths)

## Complexity Assessment
**Track**: Complex — model changes, migration, service, API, tests

## Approach
Additive to existing campaign model. A/B mode detected by presence of subject_b.
Recipients split deterministically by ab_ratio using ceil for variant A.
Variant breakdown available via existing /stats endpoint from RAP-218.
