---
story: S03
epic: EPIC-1
title: Animal Detail Page
status: ready
created: 2026-03-25T17:13:26.726270
version: V1
---

# S03: Animal Detail Page

## Description

Build individual animal profile page displaying full animal information, photo gallery, and adoption call-to-action.

## Acceptance Criteria

**Given** I navigate to an animal detail page (/animals/{id})
**When** the page loads
**Then** I see the animal's name, full profile (species, breed, age, weight, health status), intake date, and primary photo

**Given** an animal has multiple photos
**When** I view the photo gallery
**Then** I can click through photos using arrow controls, dots, or swipe on mobile to see all available images

**Given** an animal's health status is special needs (injured, sick, special_needs)
**When** I view the profile
**Then** a health alert badge is displayed and special care notes are visible if available

**Given** I am viewing an adoptable animal
**When** the page displays the animal
**Then** an "Adopt Now" button is prominently displayed that links to the adoption application form

**Given** an animal is already adopted
**When** I view the page
**Then** an "Adopted" badge is displayed and the "Adopt Now" button is disabled with a message

**Given** I view an animal detail page on mobile
**When** the page renders
**Then** the layout is responsive, photo gallery is touch-friendly, and text is readable without horizontal scrolling

## Tasks

- T01: Create detail page component
- T02: Display animal information
- T03: Show photo gallery
