# Exemplar: Good User Story

_This is a calibration example. When generating user stories, produce output matching this quality._

---

## Example: Adoption Application Status

**As an** adopter, **I want** to see the real-time status of my adoption application **so that** I know what to expect next and don't need to call the shelter.

### Context
Adopters currently have no visibility after submitting an application. Staff receive 10–15 calls per week from people asking "what's happening with my application?" This story eliminates that friction.

### Acceptance Criteria

**Given** I have submitted an adoption application
**When** I navigate to "My Applications" in my account
**Then** I see each application with:
- Animal name and photo
- Status: `Pending Review` | `Under Review` | `Approved` | `Rejected` | `Awaiting Visit`
- Date submitted
- Next action required (if any)

**Given** the shelter updates my application status
**When** the status changes
**Then** I receive an email notification within 5 minutes with the new status and next steps

**Given** my application is rejected
**When** I view the rejection
**Then** I see a reason and a list of currently available animals

### Definition of Done
- [ ] Status page displays all applications for authenticated adopter
- [ ] Email notification triggers on status change
- [ ] Status labels and transitions defined in shared enum
- [ ] Unit tests: status transitions, notification trigger
- [ ] Integration test: full apply → status update → notification flow
- [ ] Deployed to staging and verified by QA

### Story Points: 3

### Notes
Status enum must align with the animal adoption state machine in `src/models/adoption.py`. Email template lives in `src/notifications/templates/`.
