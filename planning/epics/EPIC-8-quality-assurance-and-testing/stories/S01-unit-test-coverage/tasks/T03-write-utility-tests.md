---
task_id: T03
task_title: Write Utility and Validation Function Tests
task_status: pending
story_id: S01
epic_id: EPIC-8
created_date: 2026-03-25
estimated_effort: 6 hours
dependencies:
  - T01-write-api-tests.md (EPIC-8-S01-T01)
  - T02-write-hook-tests.md (EPIC-8-S01-T02)
---

# T03: Write Utility and Validation Function Tests

## Overview

Utility and validation functions form the foundation of data integrity throughout the Refugio Animal Paraguay system. These helper functions validate input formats, transform data between different representations, and implement business rules that affect multiple layers of the application. Testing utility functions comprehensively ensures that the system's data processing pipelines are reliable and that invalid data is caught at system boundaries before it propagates into the database or external integrations.

The system includes utilities for email validation following RFC 5322 standards, currency conversion and formatting for both EUR and PYG amounts, date parsing and temporal comparisons, animal status transitions with validation, and adoption request status progression. These utilities must handle edge cases properly including malformed input, boundary conditions for numeric values, timezone considerations, and invalid state transitions.

Testing utility functions differs from endpoint testing because utilities are called synchronously and return results directly without side effects. Tests can be extremely focused, rapid, and can thoroughly exercise all code paths including error conditions. Utility tests typically form the largest portion of the test pyramid by count because individual utilities can be tested in isolation without complex fixtures or mock external services.

## Why This Task Matters

Utility functions are called by multiple higher-level components including API endpoint handlers, service classes, and scheduled tasks. A bug in a utility function can cascade through the entire system. Email validation bugs could result in communications failures with donors or adopters. Currency conversion bugs could produce incorrect donation amounts or financial reporting errors. Status transition validation bugs could allow invalid adoption states or payment intent progression.

Utility testing also provides immediate feedback during development. Developers can run utility tests in milliseconds without needing a database connection or test database cleanup. Early feedback on utility correctness lets developers catch logic errors before they affect integration testing. Poor utility test coverage often indicates untested business logic, which leads to unexpected behavior in production.

Utility functions are excellent documentation of business rules. Tests written for utilities explain what values are accepted as valid, what transformations are expected, and how edge cases are handled. This documentation is invaluable for new team members understanding system behavior.

## Technical Requirements

Email validation utilities must accept strings and return a boolean indicating validity according to RFC 5322 standards. The validation must accept standard email formats including local-part at domain-name format, reject emails with missing at-signs or domain components, reject emails with spaces or invalid characters, and accept internationalized domain names if the system supports them. Tests must verify acceptance of common formats like adopter@example.com, donor+tag@example.co.uk, and charity_partner@example.com. Tests must verify rejection of formats like missing-at-sign.com, multiple@at@signs.com, space in address@example.com, and @example.com without local part.

Currency conversion utilities must accept numeric amounts in cents (integer values) along with source currency (EUR or PYG) and return converted amounts in target currency. The conversion must use current exchange rates retrieved from an external service or configuration. The utility must handle edge cases including zero amounts, negative amounts (which may be valid for adjustments or refunds), fractional cent values (which should round appropriately), and very large amounts (considering maximum integer values). Tests must verify that one euro converts correctly to equivalent Paraguayan guaraní amounts within acceptable precision, that conversions are bidirectional (EUR to PYG and back), that edge amounts like 100 cents (one EUR) and 10000 cents (100 EUR) convert accurately, and that rounding follows consistent rules.

Animal status transition utilities must validate that status changes are legal according to adoption workflow rules. Valid transitions might include available to adopted, adopted to returned, returned to available. Invalid transitions might include available to completed, or transitions that skip required intermediate states. Tests must verify that valid transitions are accepted, invalid transitions are rejected with appropriate error messages, null or empty status values are rejected, and unknown status values are rejected.

Adoption request status progression utilities must validate that adoption request statuses can only advance through legal sequences. Valid sequences might include submitted, under-review, approved, completed. Statuses cannot move backwards or skip stages. Tests must verify forward progression, rejection of backward movement, rejection of skipped stages, and proper error messages indicating why a transition is invalid.

Date parsing utilities must accept date strings in expected formats and return datetime objects suitable for database storage or comparison. The utilities must handle timezone information correctly, either assuming UTC or parsing specified timezones. Tests must verify parsing of standard ISO 8601 formats including dates with time components, handling of timezone-aware and timezone-naive datetimes, rejection of malformed date strings, and proper temporal comparison (earlier dates compared as less than later dates).

The test suite must cover boundary conditions including minimum and maximum valid values for numeric inputs, empty strings and null values for string inputs, and edge cases like leap years for date handling. The suite must verify error handling including appropriate exception types raised for invalid input, helpful error messages that explain what was wrong, and graceful degradation where applicable.

## Implementation Approach

Tests are organized under tests/unit/utilities/ with separate test files by functional area. Email validation tests reside in tests/unit/utilities/test_email_validation.py. Currency conversion tests are in tests/unit/utilities/test_currency_conversion.py. Status transition tests are split between tests/unit/utilities/test_animal_status_transitions.py and tests/unit/utilities/test_adoption_request_status.py. Date parsing tests are in tests/unit/utilities/test_date_parsing.py.

Each test file imports the corresponding utility module and uses pytest parameterization to test multiple inputs efficiently. Email validation tests use parametrized fixtures providing email strings and expected validity results. The test method iterates through test cases verifying that the validation function returns expected boolean values. Currency conversion tests parametrize over currency pair combinations (EUR to PYG, PYG to EUR), amounts (100, 1000, 10000 cents), and round-trip conversions. Status transition tests parametrize over from-status, to-status, and whether the transition should be valid.

Fixtures provide any required setup including configuration for exchange rates if conversion utilities read from a config file. Mocking is minimal because utilities should not depend on external services unless absolutely necessary. If utilities do call external services, those calls are mocked to provide deterministic responses. Each test follows the Arrange-Act-Assert pattern with clear separation between setup, execution, and verification.

Tests for error conditions verify that appropriate exceptions are raised with helpful messages. Tests for edge cases like zero amounts, negative amounts, and very large amounts are included. Tests verify that utility functions are pure functions with no side effects, returning the same output for the same input regardless of execution order or environment state.

## Success Criteria

All utility functions must have 95% or greater code coverage with tests covering normal cases, edge cases, boundary conditions, and error conditions. Email validation tests must cover at least 20 distinct test cases including valid standard formats, valid with special characters, missing components, malformed domains, and boundary cases. Currency conversion tests must verify round-trip conversions with acceptable precision loss (less than one percent), must handle conversion between both EUR and PYG pairs, and must document any precision limitations. Status transition tests must cover all valid transitions defined in the adoption workflow and rejection of all invalid transitions with clear error messages.

Date parsing tests must verify parsing of at least five distinct date formats, handling of timezone information, rejection of malformed inputs, and temporal comparison accuracy. All tests must execute in parallel without race conditions or interference between test cases. The complete utility test suite must run in under one minute in parallel execution. All tests must follow consistent naming conventions with test functions named test_underscore_snake_case describing what is being tested and what the expected outcome is.

Coverage reports must be generated showing which utility functions have complete coverage and which have gaps. Any utility function with less than 95% coverage must be reviewed to determine whether additional test cases are needed or whether the function should be simplified. All tests must pass without failures or skips. Test output must be clear and readable with descriptive assertion messages explaining what was expected versus what was received when tests fail.
