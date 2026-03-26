---
task: T01
story: S03
epic: EPIC-8
title: Build adoption workflow test
status: ready
priority: medium
created: 2026-03-25T17:13:26.735566
---

# T01: Build adoption workflow test

## Description

Build the end-to-end test that exercises the complete adoption lifecycle from an animal appearing as available through to the adopter's confirmed adoption record and the associated notification. This test runs against the real FastAPI application with a real PostgreSQL test database and does not mock any application layer.

## What This Test Covers

The adoption workflow E2E test verifies seven sequential stages. Each stage makes real HTTP calls through the full application stack and asserts specific conditions before proceeding to the next stage.

## Stage One: Animal Availability

The test begins by calling the public animal listing endpoint with no authentication token. The response must contain at least one animal record with the status field set to available. The test extracts the ID of one available animal for use in subsequent stages.

The test also calls the animal detail endpoint for that specific ID and asserts that the response status is 200, that the species and age fields are present, and that the adoption button availability flag in the response is true.

## Stage Two: Adoption Request Submission

The test calls the adoption request creation endpoint authenticated with an adopter-role JWT token. The request body includes the animal ID from stage one and a set of valid adopter details. The expected response status is 201 Created.

The response body must contain an adoption request record with the status field set to pending and the animal status field set to reserved. The test saves the adoption request ID from the response.

The test then queries the animal detail endpoint again and asserts that the animal's status has changed from available to reserved, confirming that the status transition was committed to the database and reflected in the read model.

## Stage Three: Duplicate Request Prevention

The test attempts to submit a second adoption request for the same animal using the same adopter token. The expected response status is 409 Conflict. The response body must contain a structured error with a message explaining that an adoption request already exists for this animal and adopter combination.

The test asserts that no second adoption request record was created in the database by calling the adopter's request list endpoint and verifying that it contains exactly one entry.

## Stage Four: Staff Review

The test calls the staff-only adoption review endpoint, authenticated with a staff-role JWT token. This endpoint returns the pending adoption request by ID. The test asserts that all the adopter-provided fields from stage two are present in the response.

## Stage Five: Staff Approval

The test calls the staff-only adoption approval endpoint, authenticated with the staff token, passing the adoption request ID and the decision field set to approved. The expected response status is 200 OK.

The response body must show the adoption request with status set to approved. The test also queries the animal detail endpoint and asserts that the animal's status has transitioned from reserved to adopted.

## Stage Six: Notification Record

The test queries the notification log endpoint for the adopter, authenticated with the adopter token. The response must contain at least one notification record created after the approval timestamp. The notification record must reference the adoption request ID and indicate that the notification type is adoption approval.

This stage verifies that the approval action triggered the notification dispatch pathway, even though the actual email delivery is handled asynchronously and is not verified at this layer.

## Stage Seven: Adopter History

The test calls the adopter's adoption history endpoint, authenticated with the adopter token. The response must include the approved adoption record from this workflow with status set to approved and the adopted animal's name present in the record.

This final stage confirms that the complete workflow is visible to the adopter through the history endpoint and that no data was lost or corrupted during the status transitions.

## Database State Verification

After stage seven, the test performs a direct database query via SQLAlchemy to verify the final state of all affected records: the adoption request row must have status approved, the animal row must have status adopted, and the notification log must contain the expected record. Database-level assertions catch any discrepancy between what the API returns and what is actually persisted.

## Test Setup and Teardown

The test uses a pytest fixture that creates all prerequisite data before stage one: an adopter user with a verified email address, a staff user, and an available animal record. All three are inserted within a database transaction that is rolled back after the test completes, ensuring no test data persists to interfere with other tests.

The JWT tokens for the adopter and staff roles are generated from the conftest.py fixtures described in T01 of this story.
