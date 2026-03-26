---
task: T03
story: S01
epic: EPIC-8
title: Write utility tests
status: ready
priority: medium
created: 2026-03-25T17:13:26.735118
---

# T03: Write utility tests

## Description

Create the unit test suite for all shared utility modules in the application. Utilities are pure-function modules that contain no framework dependencies and no database access: email validators, currency formatters, date and timezone helpers, pagination calculators, and role permission checkers. These tests must run fast, require no external services, and collectively cover all edge cases for each utility.

## Approach

All tests in this file live under `tests/unit/` and are plain pytest functions or classes with no markers. They must complete in under two seconds for the full module. The tests use no mocks because the utilities under test have no dependencies to mock — they receive inputs and return outputs.

pytest's `parametrize` decorator is used extensively throughout this file. Any utility that accepts a range of inputs benefits from a parametrized test that expresses each input-expected output pair as a named test case. This makes the test file read as a specification of the utility's behavior.

## Email Validation Tests

The email validation utility exposes a function that accepts a string and returns a boolean indicating whether the string is a syntactically valid email address. The tests cover the following cases:

Standard valid addresses including a simple local part and domain, an address with dots in the local part, an address with a plus sign in the local part for sub-addressing, and an address with a subdomain.

Standard invalid addresses including an address with no at-sign, an address with two consecutive at-signs, an address with no domain part after the at-sign, an address with a domain that has no dot, an address with a space in the local part, and an empty string.

Edge cases that real-world validators often get wrong: an address with an IP address as the domain, an address whose local part is a quoted string containing spaces, and an internationalized domain name using punycode encoding.

The test suite for email validation must have at least ten test cases total, split across valid and invalid categories, with each test named to describe the specific case being verified.

## Currency Formatting Tests

The application handles two currencies: EUR for European donors and PYG (Paraguayan guaraní) for local cash donations. The currency formatting utility converts raw stored values to display strings.

EUR amounts are stored as integers representing euro cents. The formatter takes a cent integer and returns a string like "€12.50" for 1250 cents. The tests cover zero cents producing "€0.00", a round euro amount producing no fractional part but still showing two decimal places, a large amount producing correct thousands formatting, and a negative value raising a ValueError since negative stored amounts indicate a data error.

PYG amounts are stored as integers representing whole guaraní, since the guaraní has no sub-unit in everyday use. The formatter returns a string like "₲150.000" with a period as the thousands separator following Paraguayan convention. The tests cover zero, a three-digit amount with no thousands separator, a six-digit amount requiring one separator, and a nine-digit amount requiring two separators.

A parametrized test table covers both currency codes and verifies that calling the formatter with an unrecognized currency code raises a ValueError rather than silently returning a malformed string.

## Date and Timezone Helper Tests

Paraguay uses the America/Asuncion timezone, which observes daylight saving time on a Southern Hemisphere schedule. The timezone helper utility converts between UTC datetimes (used for all database storage) and local Paraguay time (used for display and reporting).

The tests verify that a UTC datetime falling in Paraguay standard time (April through September) is correctly offset by minus four hours. A UTC datetime falling in Paraguay summer time (October through March) is correctly offset by minus three hours. The converter must handle the exact moment of the DST transition without raising an exception, so tests include datetimes at the boundary of the transition.

A separate set of tests verifies the inverse direction: a naive datetime assumed to be in Asuncion local time is correctly converted to UTC, with the DST offset applied correctly for both the standard and summer time periods.

A test verifies that the utility raises a clear error if it receives a naive UTC datetime without timezone information, since storing or displaying a timezone-unaware datetime is a data quality problem.

## Pagination Calculator Tests

The pagination utility takes a total item count, a page number (one-indexed), and a page size, and returns a data structure containing the offset and limit values to pass to a database query, the total page count, and boolean flags for whether a previous and next page exist.

The parametrized tests cover: the first page of a result set that fits on one page, the first page of a multi-page result set, a middle page, the last page, a page number beyond the last page (which should return an empty page without raising an error), a page size larger than the total item count (which should return the first page with no next page), and a total count of zero (which should return a single empty page).

The tests also verify the edge case where the total count is exactly divisible by the page size, ensuring no off-by-one error produces a phantom empty final page.

## Role Permission Checker Tests

The role permission checker utility determines whether a given role string is authorized to perform a given action string. It is the pure-logic complement to the FastAPI dependency that enforces authorization at the route level.

The tests use a parametrized table covering every defined role-action combination. Each row specifies a role, an action, and the expected boolean result. The table must cover at minimum: an admin performing any action (always permitted), a staff member performing actions that are staff-permitted and actions that are admin-only (not permitted), an adopter performing actions that are adopter-permitted and actions reserved for staff or admin (not permitted), and an unrecognized role string performing any action (not permitted, no exception raised).

The tests also verify that the checker is case-sensitive for both role and action strings, so that "Admin" and "admin" are treated as distinct values, preventing accidental authorization through case mismatch.
