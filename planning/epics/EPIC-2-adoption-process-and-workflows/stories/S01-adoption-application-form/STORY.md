---
story: S01
epic: EPIC-2
title: Adoption Application Form
status: ready
created: 2026-03-25T17:13:26.727395
version: V1
---

# S01: Adoption Application Form

## Description

Multi-step form for adoption applications collecting adopter information, household details, and animal preferences with real-time validation.

## Acceptance Criteria

**Given** I click "Adopt Now" on an animal detail page
**When** I am not logged in
**Then** I am prompted to log in or create an account before proceeding to the application form

**Given** I am logged in and start the adoption application
**When** I view the form
**Then** I see a multi-step form (Step 1: Adopter info, Step 2: Household, Step 3: Experience, Step 4: Review & Submit)

**Given** I enter information in Step 1 (personal details)
**When** I fill out name, email, phone, address, date of birth
**Then** each field is validated as I type (email format, phone format, DOB age ≥18) with inline error messages

**Given** I move to Step 2 (household information)
**When** I answer questions about home type (apartment, house, farm), own/rent, other pets, children
**Then** the questions are displayed in a clear flow with options appropriate to each question

**Given** I complete Step 3 (adoption experience)
**When** I answer about previous pet ownership and why I want to adopt
**Then** a text field accepts open-ended response and character counter shows remaining limit

**Given** I review my submission on Step 4
**When** I view the review page
**Then** all entered data is displayed for confirmation with ability to edit any section, and a final Submit button is visible

**Given** I submit the application
**When** the form is valid and submitted
**Then** the application is saved to the database, I receive a confirmation email with application reference number, and I am redirected to a success page

## Tasks

- T01: Design form schema
- T02: Build form components
- T03: Implement validation
