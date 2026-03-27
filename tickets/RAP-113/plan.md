# RAP-113 Plan

## Objective
Add staff notes to adoption status change emails with bilingual (ES/EN) template.

## Description
When staff approve/reject adoption requests, their decision notes should be included in the notification email. The template should support both Spanish and English, and handle all status transitions including cancelled.

## Acceptance Criteria
- [x] Status update schema accepts optional notes field
- [x] Notes are stored on the adoption request record
- [x] Notes are passed through event payload to notification handler
- [x] Email template renders bilingual content (ES/EN)
- [x] Staff notes appear in email when provided
- [x] Staff notes block is omitted when absent
- [x] Template handles approved, rejected, cancelled statuses
- [x] Unit tests cover event factory, template rendering, and handler

## Complexity Assessment
**Track**: Simple Fix
- [x] Single concern: notes through notification pipeline
- [x] Affects 6 files (schema, API, events, handler, template, tests)
- [x] Pattern well-understood from existing notification system

## Approach
Thread notes through the existing notification pipeline: schema -> API -> event -> handler -> template.
