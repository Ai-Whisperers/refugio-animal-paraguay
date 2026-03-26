---
story: S03
epic: EPIC-7
title: Content & Settings Management
status: ready
created: 2026-03-25T17:13:26.734271
version: V5
---

# S03: Content & Settings Management

## Description

Admin interface for managing site content, configuring system settings, and managing static pages like About, Donate, and FAQs.

## Acceptance Criteria

**Given** I am an admin
**When** I access Settings & Content
**Then** I see sections for: Organization Info, Page Content, Email Configuration, Payment Settings, and System Configuration

**Given** I want to update organization information
**When** I click on Organization Info
**Then** I can edit: shelter name, address, phone, email, logo, and operating hours with save confirmation

**Given** I need to manage static pages
**When** I access Page Content
**Then** I see list of pages: Home, About, Adopt, Donate, FAQs, Volunteer with edit buttons and preview links

**Given** I want to edit a page
**When** I click Edit on a page
**Then** a rich text editor opens with current content, I can edit, preview, and save (with draft/publish options)

**Given** I configure email settings
**When** I access Email Configuration
**Then** I can set: from_email, from_name, SMTP server (or email service), and test send

**Given** I configure payment settings
**When** I access Payment Settings
**Then** I can manage: Stripe API keys (masked after first 8 chars), PayPal credentials, Tigo Money API keys, and test mode toggle

**Given** a setting is changed
**When** the setting is saved
**Then** change is logged in audit trail with admin user, timestamp, and previous/new values for all critical settings

**Given** I need to reset to defaults
**When** I view a settings section
**Then** there is a "Reset to Defaults" button (with confirmation) to restore settings to initial state

## Tasks

- T01: Build settings interface
- T02: Implement configuration system
