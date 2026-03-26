---
story: S01
epic: EPIC-5
title: Volunteer Registration & Profiles
status: ready
created: 2026-03-25T17:13:26.731246
version: V4
---

# S01: Volunteer Registration & Profiles

## Description

Volunteer registration form, profile creation, and management with role assignment and experience tracking.

## Acceptance Criteria

**Given** I want to volunteer at the shelter
**When** I visit the volunteering page and click "Sign Up"
**Then** I see a multi-section registration form: personal info, availability, interests, and background

**Given** I fill out personal information
**When** I enter name, email, phone, date of birth
**Then** fields are validated and I cannot proceed without required fields complete

**Given** I indicate my availability
**When** I select days and hours
**Then** I can select multiple day/time combinations (e.g., Sat 9-12, Wed 14-17) and form saves preferences

**Given** I identify my interests
**When** I select volunteer roles (animal care, events, adoption support, admin)
**Then** I can select multiple roles and each shows description of responsibilities

**Given** I submit registration
**When** form is complete and submitted
**Then** volunteer profile is created, account is created, and admin receives notification to review and approve

**Given** my profile is approved by admin
**When** approval happens
**Then** I receive welcome email with onboarding info, schedule, and first task assignment

**Given** I want to update my profile
**When** I access my volunteer dashboard
**Then** I can edit: availability, interests, roles, emergency contact, and save changes (admin review optional if major change)

**Given** a volunteer has been inactive
**When** dashboard displays volunteer records
**Then** admin can see last active date and hours contributed to identify engagement level

## Tasks

- T01: Create volunteer signup form
- T02: Build profile editor
- T03: Setup role assignment
