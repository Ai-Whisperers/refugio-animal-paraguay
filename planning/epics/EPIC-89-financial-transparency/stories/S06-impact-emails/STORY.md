---
story: S6
epic: EPIC-89
ticket: RAP-609
title: "Automated monthly impact emails"
status: ready
points: 4
priority: P0
track: Backend
sprint: 14
version: V14
created: 2026-03-27T20:00:00
---
# S06: Automated Monthly Donor Impact Email

## Story

As a regular donor, I want to receive a monthly email showing how my donations made a difference so that I stay connected to the organization's work.

## Description

Implement cron job that runs monthly (1st of month) to generate and send personalized impact emails to all donors with donations in the prior month. Email includes impact statistics, campaign progress, animal stories, and year-to-date totals in Spanish.

## Acceptance Criteria

- [ ] Implement monthly cron job: runs on 1st of each month at 8:00 AM
- [ ] Cron selects all donors with donations in prior month
- [ ] For each donor, generate personalized email with:
  - [ ] Greeting: "Hola [Nombre], gracias por tu apoyo a Refugio Animal Paraguay"
  - [ ] Summary: "En [Mes] donaste [Monto] PYG/USD y ayudaste a:"
  - [ ] Personal impact: "Tus donaciones hicieron posible:"
    - [ ] "Rescatar N animales"
    - [ ] "Financiar N castraciones"
    - [ ] "Proporcionar cuidado medico a N animales"
    - [ ] "Alimentar N animales por N dias"
  - [ ] Top campaign progress: show top 3 campaigns donor supports
  - [ ] Animal stories: include 1-2 specific animal rescue/adoption stories
  - [ ] Year-to-date total: "Hasta ahora en [YYYY] donaste [MONTO]"
  - [ ] Call to action: "Continua apoyando nuestra mision" with link to donate
  - [ ] Unsubscribe link: "Dejar de recibir estos correos" (Unsubscribe)
- [ ] Email template fully localized in Spanish
- [ ] Email design responsive for mobile and desktop
- [ ] Include Refugio logo and branding
- [ ] Track email opens: click tracking pixel or redirect link
- [ ] Handle email delivery failures gracefully
- [ ] Log email sending results: success, failure, bounce
- [ ] Implement email unsubscribe mechanism
- [ ] Store EmailLog with donor_id, sent_date, open_date nullable
- [ ] Respect email preferences: donor can opt-out of monthly emails
- [ ] Limit email size: <5MB including images
- [ ] Test email rendering in Gmail, Outlook, Apple Mail

## Definition of Done

- [ ] Code complete, peer reviewed
- [ ] Cron job scheduled and tested
- [ ] Email template created in Spanish
- [ ] Email generation logic tested with sample donors
- [ ] Email sending working (test against real mailbox)
- [ ] Unsubscribe links verified
- [ ] Email tracking implemented
- [ ] Database logging of emails sent
- [ ] Mobile email rendering tested
- [ ] Edge cases handled: new donors, inactive donors, bounced emails
- [ ] Manual testing: send test emails to real inbox
- [ ] Error handling: retry failed emails
- [ ] Deployed to staging and verified

## Technical Notes

- Use templating library for email generation (Jinja2, Nunjucks, etc.)
- Implement exponential backoff for email retries
- Use transactional email service (SendGrid, Mailgun, etc.)
- Include unsubscribe header per RFC 2369
- Track opens via pixel or click tracking
- Build email campaign in stages (batch 100 per minute)
- Monitor delivery rates and bounce rates
- Consider A/B testing subject lines for open rates

## Story Points: 5
