---
story: S3
epic: EPIC-79
ticket: RAP-527
title: "Integration with vet voucher system"
status: ready
points: 5
priority: P0
track: Backend
sprint: 12
version: V1
created: 2026-03-27T20:00:00
---

# S3: Integration with vet voucher system

## Story
As a **system**, I want **to automatically track castrations performed under campaign** so that **campaign progress updates automatically**.

## Description
Link castration campaign to vet voucher system so that when castration vouchers are redeemed, campaign completed_count increments and triggers milestones.

## Acceptance Criteria
- [ ] Donation target type: donations with target_type='campaign' and target_id=campaign_id auto-create castration vouchers at partner clinics
- [ ] Voucher creation: when donation made to campaign, create VetVoucher records for castration_dog or castration_cat services at each partner clinic (distribute proportionally)
- [ ] When VetVoucher redeemed: check if service_type in (castration_dog, castration_cat) AND clinic_id in campaign.partner_clinics, increment campaign.completed_count
- [ ] Milestone triggers: when completed_count hits 25%, 50%, 75%, 100% of target_count:
  - Send email to all donors: "Congratulations! We've reached X% of our castration goal!"
  - Send WhatsApp to donors (if opted in)
  - Publish social media post (if enabled)
- [ ] Real-time updates: completed_count updates visible immediately on campaign page
- [ ] Event logging: log each redemption with campaign_id, animal_id, clinic_id
- [ ] Completion notification: when campaign reaches 100%, mark as 'completed', send special congratulation email to donors and admin

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage) - test voucher creation, completed_count increment, milestone triggers
- [ ] Integration test: donation to campaign creates vouchers
- [ ] Integration test: voucher redemption increments completed_count
- [ ] Integration test: milestone notifications sent at 25/50/75/100%
- [ ] Integration test: campaign marked completed at 100%
- [ ] Manual testing: verify end-to-end flow
- [ ] Deployed to staging and verified

## Technical Notes
- Event hook: subscribe to vet_voucher.redeemed event
- Completed count increment: atomic update to campaign.completed_count
- Milestone check: if completed_count / target_count crosses 0.25/0.50/0.75/1.0 threshold
- Voucher creation: when donation.target_type='campaign', create vouchers proportionally across partner clinics
- Notifications: use existing notification system (email, WhatsApp)
- Social media: if campaign has social_media_enabled flag, post to connected accounts

## Story Points: 5
