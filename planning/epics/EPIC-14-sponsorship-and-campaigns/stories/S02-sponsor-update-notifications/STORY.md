---
story: S02
epic: EPIC-14
title: Sponsor Update Notifications
status: ready
created: 2026-03-26T00:00:00.000000
effort: 6
---

# S02: Sponsor Update Notifications

## User Story

As a **sponsor**, I want to **receive periodic updates about my sponsored animal's health, milestones, and activities** so that **I feel connected to the animal and see the impact of my sponsorship**.

## Acceptance Criteria

**Given** I am an active sponsor
**When** the shelter publishes an update about my sponsored animal
**Then** I receive an email with photos, health status, and a personal message

**Given** my sponsored animal has a significant milestone (adoption, medical recovery, birthday)
**When** the milestone occurs
**Then** staff records it and I receive a special notification about the milestone

**Given** I have multiple sponsored animals
**When** I receive updates
**Then** I can distinguish which animal each update is about and can manage notification preferences per animal

**Given** staff wants to send bulk updates to multiple sponsors
**When** they publish an animal update
**Then** all sponsors of that animal receive the update automatically

**Given** I am a sponsor
**When** I log in to my account
**Then** I can see a timeline of all updates I've received about my sponsored animals

## Tasks

- T01: Implement animal update schema with photos, text, milestone tracking
- T02: Build staff interface for publishing animal updates
- T03: Create automatic notification trigger and email template system
- T04: Implement sponsor notification preferences (frequency, email/in-app)
- T05: Add update timeline to sponsor dashboard

## Definition of Done

- [ ] Staff can publish updates to animals with photos and text content
- [ ] Milestone types trackable: vaccination, recovery, adoption_ready, birthday, behavioral_progress, etc.
- [ ] Automatic emails sent to all active sponsors when update published
- [ ] Sponsors can customize notification frequency (daily, weekly, monthly digest)
- [ ] Update timeline shows in sponsor dashboard in reverse chronological order
- [ ] Sponsor notification preferences persist correctly
- [ ] Unit tests cover notification trigger logic and filtering (85%+ coverage)
- [ ] Integration tests verify email sending for bulk updates
- [ ] Email templates render correctly with animal photos and text

## Technical Notes

- Animal update model: id, animal_id, published_date, published_by_staff_id, title (text), content (text), photo_urls (array), milestone_type (enum), update_type (health, behavior, milestone, general)
- Milestone types enum: vaccination, medical_treatment, behavioral_progress, adoption_ready, birthday, recovered, deceased, returned_from_adoption
- Sponsor notification model: sponsor_id, frequency (enum: immediate, daily_digest, weekly_digest, monthly_digest), notification_enabled (bool)
- Email template: animal name, photo, update title, update content, link to sponsor dashboard
- Use background job system (Celery) to send emails asynchronously
- Optional: allow sponsors to leave comments or react to updates (heart, celebration emoji)

## Dependencies

- Depends on: S01-animal-sponsorship-tiers (sponsors must exist)
- Depends on: EPIC-6 (Notifications/email system)
- Blocks: S04-campaign-progress-social-proof (social proof may use sponsor updates)

## Story Points: 6
