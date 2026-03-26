---
task: T02
story: S02
epic: EPIC-8
title: Add interaction tests
status: ready
priority: medium
created: 2026-03-25T17:13:26.735358
---

# T02: Add interaction tests

## Description

Define and implement interaction tests that verify multi-step user flows within the frontend application. Interaction tests operate at a level above component tests: rather than testing a single component in isolation, they render a connected subtree of components and simulate a realistic user journey from start to finish, asserting correct state transitions along the way.

Like component tests, the frontend stack is TBD. This task defines the behavioral requirements for interaction tests so that implementation is unblocked once the stack is selected.

## Approach

Interaction tests live under `tests/frontend/integration/`. They use the same testing library as component tests but render a larger component tree that includes routing, form state management, and mock API responses. The backend API is not called in these tests; instead, the HTTP layer is intercepted and replaced with mock handlers that return responses matching the Pydantic response schemas defined in the FastAPI application.

The mock responses must be kept in sync with the actual API schemas. A shared schema fixture file under `tests/frontend/fixtures/` contains example response payloads that are used both in interaction tests and in contract verification tooling.

## Adoption Application Submission Flow

The adoption submission flow starts from the animal detail page and ends at the adoption confirmation screen. The test simulates the following sequence:

The user views the animal detail page for an available animal. The page shows the animal's name, species, age, photo, and a button to begin the adoption process. The test asserts that the button is present and accessible.

The user activates the adoption button. The adoption request form renders. The test fills in the required fields: personal information, housing situation, and adoption motivation. Field values are entered character by character using the testing library's user-event simulation to replicate real keyboard input rather than programmatic value assignment.

The user submits the form. The mock API handler returns a 201 response matching the adoption request creation schema, with the status field set to pending and the animal status field set to reserved. The test asserts that the success confirmation screen renders, that the confirmation displays the animal's name and the pending status, and that the adopt button is no longer present on the animal detail page (because the animal is now reserved).

A separate test in this flow verifies the duplicate submission scenario. The mock API handler for this variant returns a 409 Conflict response. The test asserts that the form displays an error message explaining that an adoption request already exists for this animal, and that the submit button becomes enabled again so the user can navigate away or try a different animal.

## Donation Flow

The donation flow covers the complete path from selecting a donation amount to receiving a confirmation of payment processing.

The test renders the donation landing page, selects EUR as the currency, enters an amount, and clicks the donate button. The mock API handler for payment intent creation returns a client secret string and a pending donation record ID. The test verifies that the Stripe payment form element renders (or a mock of it, since Stripe Elements cannot be exercised in a unit test environment) and that the amount display reflects what was entered.

A second test variant covers the PYG cash donation path, which has no Stripe step. The test submits the form, the mock handler returns a 201 with the pending cash record, and the test asserts that the confirmation screen explains that cash payment instructions will be provided by shelter staff.

A third variant covers the webhook-triggered completion state. The test renders the donation status page for a pending donation ID and then simulates the polling mechanism detecting that the donation status changed to completed. The test asserts that the page updates to show the completion message without a full page reload.

## Admin User Management Flow

The admin user management flow covers searching for a user by name and changing their role.

The test renders the admin user list page with a mock response containing five user records. The test simulates typing a search term into the search field and asserts that only matching users appear in the list as the mock handler returns a filtered response.

The test then selects a user and opens the role editor. It changes the role from staff to admin using the role dropdown, clicks save, and asserts that the mock patch endpoint was called with the correct user ID and the new role value. The success response from the mock causes the user list to update, and the test asserts that the updated role label appears in the corresponding row.

## Pagination Interaction

The pagination interaction test covers the pattern common across multiple list views: animals, adoption requests, and donations.

The test renders a paginated list with a mock response indicating twenty-three total records across three pages. It verifies that the previous button is disabled on page one. It clicks the next button and asserts that a new mock API call is made with the page parameter incremented to two. It verifies that the previous button is now enabled. It clicks next again to reach page three and asserts that the next button is now disabled.

## Mock API Response Discipline

All mock API responses in interaction tests must conform exactly to the Pydantic response schemas. If a schema adds a new required field, the mock fixtures must be updated in the same pull request. A test that uses a response fixture missing a newly required field catches the divergence immediately, preventing frontend-backend schema drift from going undetected until integration testing.
