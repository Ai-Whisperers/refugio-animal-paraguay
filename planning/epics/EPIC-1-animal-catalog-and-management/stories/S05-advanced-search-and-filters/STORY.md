---
story: S05
epic: EPIC-1
title: Advanced Search & Filters
status: ready
created: 2026-03-25T17:13:26.726964
version: V5
---

# S05: Advanced Search & Filters

## Description

Advanced filtering by species, breed, age range, health status, and name search with real-time results and saved filter preferences.

## Acceptance Criteria

**Given** I visit the animal catalog
**When** the page loads
**Then** I see an expandable filter panel with options for species, breed, age range (kitten/puppy, young, adult, senior), and health status

**Given** I use the search box
**When** I type an animal name
**Then** search results update in real-time without page reload, matching animals by name or breed substring

**Given** I apply multiple filters simultaneously (e.g., species=dog AND health_status=healthy)
**When** the filters are applied
**Then** only animals matching ALL selected criteria are displayed, filter count badge shows active filters, and results update instantly

**Given** I have multiple filters active
**When** I click an individual filter value
**Then** that filter is toggled off, results refresh, and the URL updates to reflect current filter state

**Given** I want to clear all filters
**When** I click "Clear All Filters"
**Then** all active filters are reset, URL returns to base /adoptar, and all animals are displayed

**Given** I found a useful filter combination
**When** I bookmark or save the page URL
**Then** returning to that URL restores all filters in their previous state (URL-based state persistence)

**Given** my browser is small
**When** I interact with the filter panel on mobile
**Then** the filter panel is collapsible/expandable and does not block animal listings

## Tasks

- T01: Build filter UI
- T02: Implement filter logic
