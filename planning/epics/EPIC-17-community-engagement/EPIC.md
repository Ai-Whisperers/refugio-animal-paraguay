---
epic_id: EPIC-17
epic_title: Community & Social Engagement
epic_status: planned
created_date: 2026-03-26
last_updated: 2026-03-26
epic_owner: Marketing & Community
target_release: FPUNA-2026 Wave 3
priority: medium
estimated_effort: 24 story points
---

# EPIC-17: Community & Social Engagement

## Overview

This epic builds community engagement capabilities enabling the Refugio to share adoption success stories, foster adopter community connections, recognize volunteer contributions, and amplify impact through social media integration. The platform enables staff to publish before/after animal rescue stories, adopters to connect with other adopters through an internal community forum, volunteers to earn recognition through achievement badges, and automated syndication to social media (Instagram, Facebook) where the organization's EU and Paraguayan supporters engage.

Success stories are critical for donor motivation, particularly for European supporters who cannot visit in person. The ability to show "before: abused street dog; after: happy home with the García family" creates emotional connection and justifies continued financial support. Community features transform isolated adopters into a network of brand advocates.

## Why This Epic Matters

EU donors are geographically disconnected from operations. They cannot visit the shelter or meet animals in person. Shareable success stories, professional photography, and emotional narrative bridge this distance and sustain engagement. Organizations with strong community and storytelling see 30-50% higher donor retention.

Social media presence is essential for reaching Paraguayan audience as well. Instagram and Facebook penetration in Paraguay is high; leveraging these channels for volunteer recruitment, adoption awareness, and community organizing is cost-effective marketing.

For adopters, connecting with other adopter families creates long-term engagement. Adopters who participate in community tend to donate, volunteer, and refer friends—becoming lifetime supporters rather than one-time transactional users.

Volunteer recognition (badges, leaderboards, public acknowledgment) increases retention and motivation, particularly important in Paraguay where volunteer culture may benefit from visible social recognition.

## Target Users

**Staff & Social Media Manager**: Publish stories, manage posts, schedule content across social media, monitor engagement.

**Adopters & Adopted Animals**: Share photos, connect with other adopter families, attend virtual/in-person events.

**Volunteers**: Earn recognition badges, track hours, see their contribution in context of organization-wide impact.

**EU & Paraguayan Community**: Follow social media, read impact stories, engage with content via likes/shares/comments.

**Dutch Owner & Leadership**: Monitor brand presence, analyze community engagement metrics, approve published content.

## Scope: In Scope

Success story publishing system enabling staff to create rich narrative stories with animal photo sequences (before/after), adoption outcome, adopter testimonials, and publication controls (public/private, featured, scheduled). Story templates for consistency (structure, naming, photography guidelines). Staff approval workflow for stories before publication.

Social media integration including automatic syndication of featured stories to Instagram and Facebook, hashtag management, analytics tracking (reach, engagement), and cross-posting scheduling. API integration with Meta/Instagram Business APIs for post creation and metrics.

Adopter community forum enabling adopters to post photos, share adoption tips, organize local meetups, and moderate discussions. User reputation system (likes, helpful comments) to encourage quality contributions. Privacy controls ensuring adopter contact info is not exposed.

Volunteer recognition system with achievement badges (e.g., "100 hours volunteered", "foster care specialist", "dog walking champion"), public volunteer hall of fame leaderboard, and weekly/monthly recognition features. Badges linked to actual data (hours logged, number of animals fostered).

Event coordination enabling staff to announce adoption events, foster care recruitment drives, or volunteer appreciation gatherings. Adopters/volunteers can RSVP, receive reminders, and post photos post-event.

Content moderation tools for forum and comments including spam detection, offensive content filtering, and staff review queue.

Analytics dashboard showing story reach, social media engagement rates, volunteer recognition badge distribution, and community forum activity trends.

## Scope: Out of Scope

Live streaming of shelter operations or adoption events (deferred). Advanced influencer partnership platform or ambassador program. Marketplace for adopter-created merchandise. Third-party social media management platforms (direct API integration only). Community gamification beyond simple badges. Localization to Spanish or Guaraní for public-facing content (English/Spanish bilingual deferred). User-generated video platform. Integration with Twitter/TikTok (Instagram/Facebook only).

## Stories

This epic consists of four major stories. Story S01 implements the success story publishing system with templates, media management, and approval workflow. Story S02 builds social media integration with Meta API for automated posting and analytics. Story S03 develops the adopter community forum with privacy, reputation, and moderation. Story S04 implements volunteer recognition badges, leaderboards, and event coordination.

## Dependencies

This epic depends on core animal/adoption records (EPIC-02), volunteer management (EPIC-06), and media hosting infrastructure. Social media API credentials and business account setup required before implementation. Professional photography guidelines and story templates should be developed by marketing team before engineering starts. Content moderation policy must be documented.

## Success Metrics

Success story publishing is successful when staff publish at least one featured story per week, stories average >100 views per publication, and stories are ranked as the most emotionally compelling content by survey respondents.

Social media integration is successful when stories reach at least 500 new followers per month across Instagram/Facebook, engagement rate (likes+comments per post) exceeds 3%, and organic reach grows 10-15% monthly.

Adopter community forum is successful when at least 20% of adopters participate in forum within first quarter, average thread gets 3+ replies, and adopter-to-adopter recommendations lead to measurable volunteer/donor conversions.

Volunteer recognition is successful when 75% of volunteers earn at least one badge within first quarter, leaderboard presence correlates with volunteer retention, and recognition program increases volunteer satisfaction scores by 15%.

Content moderation metrics require that 95% of published stories and forum posts are appropriate (zero false positives in moderation), response time to reported content is <24 hours, and spam detection catches >90% of spam without false positives.

## Risk Factors

**Brand risk**: Publishing stories with insufficient vetting could damage reputation. Mitigated by mandatory staff approval workflow, clear editorial guidelines, and regular content audits.

**Privacy risk**: Adopter photos/names published without explicit consent. Mitigated by clear opt-in/opt-out mechanisms, privacy policy, and model release forms for professional photos.

**Moderation risk**: Community forum could host unwanted content (spam, harassment, misinformation about animal care). Mitigated by proactive moderation, automated spam detection, user reporting mechanisms, and clear community guidelines.

**Social media account compromise**: Credentials leaked or account hacked. Mitigated by strong password management, two-factor authentication, limited token scope, and activity monitoring.

**Over-engagement risk**: Managing social media presence becomes staff time sink without clear ROI. Mitigated by templated posting, scheduled content, analytics-driven publishing, and realistic goals.

**Volunteer comparison risk**: Public leaderboard could demotivate lower-ranked volunteers. Mitigated by emphasizing collaborative nature, recognizing different volunteer types (not just hours), and private communication celebrating all contributions.

## Technical Notes

Stories are stored in a stories table with title, narrative text (rich text editor), publication_status, created_by (staff), featured boolean, and publish_date. Story media links to a story_media junction table with orderings, captions, and alt text. Template system uses Markdown or Jinja for generating story outlines.

Social media integration uses Meta Business API for Instagram and Facebook. Authorized credentials stored encrypted in environment. Posts are queued in a social_media_queue table with status (pending, posted, failed) and analytics snapshot. Metrics are synced nightly using API webhooks.

The forum uses a familiar threaded discussion model: posts, replies, nested comments. User reputation calculated from likes/helpful votes. Adopter privacy enforced by hiding email addresses and phone numbers; direct messages use internal system rather than exposing contact info.

Volunteer badges are data-driven: a badge definition includes criteria (e.g., hours_threshold: 100, is_foster_carer: true), and a background job evaluates volunteers nightly, awarding badges. Hall of fame is a ranked view of volunteers by badge count or hours.

Events table stores event details (date, location, description, volunteer_capacity, adopter_capacity). RSVP tracking links users to events with status (interested, confirmed, attended). Post-event, staff can upload photos to event gallery.

Content moderation uses ML-based profanity filtering (e.g., Perspective API) as first pass, with human review queue for edge cases. Spam detection uses heuristics (URL frequency, account age, rate of posts) and user reporting.

Analytics aggregates story/post data to a weekly report sent to admin dashboard. Metrics include reach, engagement rate, follower growth, and forum activity.

