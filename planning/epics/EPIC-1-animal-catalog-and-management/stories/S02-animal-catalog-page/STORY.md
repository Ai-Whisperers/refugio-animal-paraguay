---
story: S02
epic: EPIC-1
title: Animal Catalog Page
status: ready
created: 2026-03-25T17:13:26.725874
version: V1
---

# S02: Animal Catalog Page

## Description

Build /adoptar page displaying animal listings with pagination, basic filters, and animal preview cards.

## Acceptance Criteria

**Given** I visit the /adoptar page
**When** the page loads
**Then** I see a responsive grid of animal cards showing name, species, breed, age, photo, and status

**Given** the catalog contains more than 12 animals
**When** I scroll or navigate to the next page
**Then** pagination shows available page numbers and I can load the next batch of 12 animals

**Given** I view the animal catalog
**When** the page displays animals
**Then** each card includes a photo (or placeholder), animal name, species emoji, breed, age range (kitten/puppy/adult/senior), and adoption status badge

**Given** I want to filter the catalog
**When** I interact with the filter controls
**Then** I can filter by species (dog, cat, bird, rabbit, other) and see only matching animals

**Given** I select a filter
**When** the filter is applied
**Then** the URL updates with filter params (e.g., /adoptar?species=dog), results update without page reload, and a clear filter button appears

**Given** I click on an animal card
**When** the click is registered
**Then** I navigate to the animal detail page (/animals/{id}) preserving filter state in URL

## Tasks

- T01: Create catalog page layout
- T02: Implement animal list component
- T03: Add pagination
