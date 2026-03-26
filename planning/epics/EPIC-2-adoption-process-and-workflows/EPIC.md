---
epic: EPIC-2
title: Adoption Process & Workflows
status: ready
created: 2026-03-25T17:13:26.727270
updated: 2026-03-25T17:13:26.727273
---

# EPIC-2: Adoption Process & Workflows

## Overview

**Goal**: Implement the complete adoption lifecycle from initial application through final approval and contract generation, enabling prospective adopters to apply online and shelter staff to manage and communicate decisions efficiently.

**Why it matters**: Adoptions are the shelter's primary mission outcome. An online application process reduces friction for prospective adopters, improves staff efficiency compared to paper-based processes, and creates an auditable record of every adoption decision. For a shelter in Paraguay where the owner has a European background, a structured, documented process also demonstrates organizational credibility to international donors and partners who expect professional-grade operations.

**Target users**: Prospective adopters (members of the public, including those who found the shelter through the European donor network); shelter staff who review applications and make approval decisions; shelter administrators who need full oversight of all adoption activity; existing adopters who want to track the status of their application.

---

## Scope

### In Scope

- Adoption application form submission: capturing adopter contact details, household information, motivation for adopting, prior pet ownership history, and agreement to the shelter's terms
- Application status lifecycle: submitted, under review, approved, rejected, and withdrawn — with automated status timestamps and the staff user who made each status change
- Staff review workflow: a protected API endpoint that allows staff or admin users to update an application's status, add internal review notes, and record the reason for a rejection
- Duplicate application detection: preventing the same adopter from submitting multiple simultaneous applications for the same animal
- Animal reservation logic: when an application moves to under review, the animal's status updates to reserved in EPIC-1's animal catalog, preventing concurrent applications for the same animal
- Notification triggers: when application status changes, the relevant notification events are emitted for EPIC-6's notification system to deliver via email and other channels
- Adoption contract generation: producing a structured document with adopter details, animal details, and the shelter's standard terms that staff can download as a PDF after approval
- Basic reporting: counts of applications by status and by time period for the admin dashboard in EPIC-7

### Out of Scope

- Online payment for adoption fees (adoption at this shelter is free; if a fee is introduced in the future, this would require EPIC-3 integration)
- Video or virtual meet-and-greet scheduling (a future enhancement)
- Integration with government animal registration databases (subject to Paraguayan regulatory requirements; tracked as a future research item)
- Automated ML-based applicant scoring or ranking
- Multi-animal adoption applications in a single submission (a future enhancement)

---

## Stories

- **S01: Adoption Application Form** — Design the application data model and implement the POST endpoint that receives and validates a completed adoption application. The endpoint is accessible to unauthenticated users but captures email address for follow-up. Validate that the referenced animal exists and is in an adoptable state before accepting the submission. Return a confirmation with the application's UUID identifier so the applicant can reference it in future communications.

- **S02: Application Review Workflow** — Implement the staff-facing PATCH endpoint for updating application status. Enforce the valid status transition rules. When transitioning to under review, trigger the animal reservation in the catalog. When transitioning to approved or rejected, record the decision timestamp and the staff user who made the decision. Internal staff review notes are stored separately from the public-facing application record.

- **S03: Adoption Notifications** — Define the notification event payloads for each application status transition (submitted, approved, rejected) and emit them to EPIC-6's notification queue. The notification content should include the applicant's name, the animal's name, and a human-readable explanation of the next steps or outcome. Notification delivery is handled by EPIC-6; this story only defines the events.

- **S04: Adoption Contracts & Documents** — Implement PDF contract generation triggered when an application is approved. The contract includes the adopter's details, the animal's profile, the adoption date, the shelter's standard terms and conditions, and a signature field. The generated PDF is stored associated with the adoption record and accessible to both staff and the adopter via a secure download link.

---

## Dependencies

**Depends on**:
- EPIC-1 (Animal Catalog & Management) — adoption applications reference specific animal records; animal status updates (reserved, adopted) are the responsibility of the adoption workflow
- EPIC-10 (Authentication & User Accounts) — staff review actions require authenticated users with the staff or admin role; adopters who register accounts can track their application status
- EPIC-6 (Communications & Notifications) — adoption status change notifications are delivered by the notification system; this epic only emits the event payloads

**Blocks**:
- EPIC-7 (Admin Dashboards) — adoption activity feeds and reporting metrics depend on the adoption data model established here

---

## Success Metrics

- An adopter can submit a complete application in under ten minutes from first loading the application form
- Staff can process an application review decision (review, approve, or reject) in under two minutes from opening the application record
- Zero duplicate approved adoptions for the same animal — the reservation logic must prevent concurrent approvals
- Notification delivery rate for application status changes exceeds 95 percent (measured via EPIC-6's notification log)
- Generated adoption contracts are produced within five seconds of approval

---

## Risk Factors

- **Concurrent application race condition**: Two staff members could theoretically approve different applications for the same animal simultaneously. Mitigation: the animal reservation transition must use a database-level locking mechanism or a serializable transaction to prevent double-booking.
- **Applicant drop-off**: Long application forms have high abandonment rates. Mitigation: capture email address early in the form flow so that partial completions can be followed up; keep the form focused on genuinely necessary information.
- **Legal requirements for Paraguayan adoptions**: Paraguayan animal welfare law (Ley 4840/2013) may require specific documentation or disclosures in adoption contracts. Mitigation: the shelter owner reviews the contract template before deployment; contract fields are designed to be configurable rather than hardcoded.

---

## Effort & Priority

**Priority**: High. Adoptions are the core mission. This epic is the most visible operational workflow and should be delivered promptly after EPIC-1.

**Estimated effort**: Two sprints. The application form and review workflow (S01, S02) form the critical path. Notifications (S03) depend on EPIC-6 being available. Contract generation (S04) can be delivered later without blocking the core workflow.
