---
task: T01
story: S02
epic: EPIC-8
title: Create component tests
status: ready
priority: medium
created: 2026-03-25T17:13:26.735303
---

# T01: Create component tests

## Description

Define the component testing strategy for the frontend layer and write the initial set of component tests once the frontend technology stack has been selected. The frontend stack is not yet decided (see CLAUDE.md: Frontend TBD). This task captures the behavioral requirements for component tests so that implementation can proceed as soon as the stack decision is made.

## Approach

Component tests verify individual UI components in isolation, independently of the backend. They render a component with a given set of props and simulate user interactions, then assert that the component produces the expected output and calls the expected callbacks.

The component test suite lives under `tests/frontend/unit/` and mirrors the component directory structure of the frontend application. Each component file has a corresponding test file with the same base name and a test suffix.

Once the frontend framework is selected, the testing library is chosen from that framework's ecosystem. For a React-based frontend, this would be React Testing Library, which encourages querying the DOM by accessible role and label rather than by CSS class or component internals. The same principle applies regardless of the chosen framework: test what the user sees, not implementation details of the component hierarchy.

## What Component Tests Must Cover

Component tests are not about verifying API calls or database state. They verify that the component renders correctly given its inputs and that it responds correctly to user interactions by calling the right handlers with the right arguments.

Every component that can exist in multiple visual states needs a test for each state. The states to cover are defined below.

## Animal Listing Component States

The animal listing component renders a grid of animal cards. Its states are: the empty state where no animals match the current filters (must display a meaningful empty-state message, not a blank area), the loading state where animals are being fetched (must display a loading indicator accessible to screen readers), the populated state where animals are present (must display the correct count and render each card with name, species, age, and status), and the error state where the fetch failed (must display an error message with a retry action).

Tests for the populated state use a fixed array of synthetic animal data passed as props. The test verifies that the number of rendered cards matches the length of the input array, that each card displays the animal's name, and that cards with the status "reserved" display a visual indicator distinguishing them from available animals.

## Adoption Form Component States

The adoption form is a multi-field input component. States to cover: the initial state with all fields empty and no validation errors shown, the validation error state triggered after the user attempts to submit with missing required fields, the submitting state while the form POST is in flight (submit button must be disabled), and the success state after submission (must render a confirmation message, not the form).

Tests for the validation error state simulate the user clicking the submit button without filling required fields and assert that each required field displays its associated error message. Error messages must be associated with their fields via accessible attributes so that screen reader users hear the error when they focus the field.

## Donation Form Component States

The donation form handles currency selection (EUR or PYG) and amount entry. States: initial with EUR pre-selected, after the user switches to PYG (amount field label and placeholder must update to reflect the guaraní currency), after the user enters an amount below the minimum (validation error visible), and after successful submission.

A specific test verifies that switching from EUR to PYG clears the previously entered amount, preventing confusion from an amount that was valid in one currency appearing as a value in the other.

## Authentication Component States

The login form has two states: the idle state with empty credential fields and an active submit button, and the error state after a failed login attempt (must display a message indicating the credentials were invalid without specifying whether the email or password was wrong, per security convention).

The authenticated user menu component has two states: showing the user's display name and role when a valid session exists, and rendering nothing or a login link when no session exists.

## Test Conventions

All component tests must query the DOM by accessible role, label text, or placeholder text. Querying by CSS class name, test ID attributes, or component display name is permitted only as a last resort for elements that have no accessible label and where adding one would require a non-trivial accessibility change. Accessible querying ensures that tests break when accessibility regressions are introduced, not only when visual structure changes.

Each component test file begins with a brief comment identifying which component is under test, the test file's location, and the behavioral contract being verified. This helps reviewers understand the intent without reading the test logic in detail.
