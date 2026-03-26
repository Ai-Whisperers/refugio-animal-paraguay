---
story: S05
epic: EPIC-7
title: Admin Panel Localization
status: ready
created: 2026-03-26T00:00:00.000000
effort: 5
---

# S05: Admin Panel Localization

## User Story

As a **staff member in Paraguay**, I want to **use the admin panel in Spanish (es-PY) with fallback to English for international staff** so that **I can manage the shelter operations in my native language and EU staff can still access the system**.

## Acceptance Criteria

**Given** I am a staff member with Spanish locale preference
**When** I log in to the admin panel
**Then** all labels, buttons, error messages, and navigation are displayed in Spanish

**Given** I am an EU staff member
**When** I access the admin panel
**Then** I can view the interface in English (default fallback)

**Given** I want to change my interface language
**When** I access my user settings
**Then** I can select my preferred language (Spanish or English) and the interface updates immediately

**Given** the system detects my language preference from my profile
**When** I log in
**Then** the interface automatically displays in my preferred language

**Given** a new error message is generated
**When** the error is displayed
**Then** the message is shown in my selected language

**Given** the admin panel has been localized
**When** I review the translation quality
**Then** all Spanish translations are accurate and follow Paraguay Spanish conventions

## Tasks

- T01: Extract all admin UI strings (labels, buttons, messages, validation errors) to i18n resource files
- T02: Create Spanish (es-PY) translation file with all extracted strings translated
- T03: Implement locale switching in admin user settings with persistence to user profile
- T04: Add locale detection from user profile and apply at login, with fallback to English
- T05: Write unit tests for language switching, locale detection, and translation loading

## Definition of Done

- [ ] All admin UI strings extracted to i18n resource keys (no hardcoded strings in templates)
- [ ] Spanish (es-PY) translation file created with 100% translation coverage
- [ ] English fallback provided for any untranslated keys
- [ ] Locale switching implemented in user settings with UI reload on change
- [ ] Locale persisted to user profile (preferred_language column)
- [ ] Login flow detects user.preferred_language and loads correct translation bundle
- [ ] Error messages, validation messages, and system notifications are localized
- [ ] Date and time formatting follows locale conventions (es-PY for Spanish)
- [ ] Unit tests verify translation key loading and locale switching (80%+ coverage)
- [ ] Integration tests verify end-to-end language switching and persistence
- [ ] No broken translation keys in production (tests catch missing keys)

## Technical Notes

- I18n framework: Use Flask-Babel (Python) or similar for FastAPI backend, or Fluent/i18next for frontend
- Locale codes: "es-PY" (Spanish Paraguay), "en-US" (English US fallback)
- Translation file structure: JSON or YAML with nested keys (e.g., "admin.animals.create_button": "Crear Animal")
- Locale detection flow: Check user.preferred_language → if null, detect from browser Accept-Language → default to en-US
- Persistence: Store preferred_language in users table, update via PATCH /users/me endpoint
- Date/time formatting: Use locale-aware formatting (e.g., "2026-03-26" en-US vs "26/03/2026" es-PY)
- Shared i18n infrastructure: Coordinate with EPIC-11 S03 (public portal localization) to avoid duplicate translations
- Translation coverage: All admin strings, error messages, validation messages, navigation labels, table headers
- Database indexes: users.preferred_language for analytics on language usage

## Dependencies

- Depends on: EPIC-11 S03 (Multi-language foundation for shared i18n infrastructure), EPIC-7 S01-S04 (Admin panel must exist)
- Coordinates with: EPIC-11 S03 for shared translation infrastructure

## Story Points: 5
