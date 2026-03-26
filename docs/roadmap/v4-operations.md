# V4 — Shelter Operations: Volunteers, Medical Records & Fostering

**Version**: 4.0.0
**Timeline**: Weeks 13-18 (after V3 launch)
**Prerequisites**: V3 complete (notifications working, adoption flow complete)
**Theme**: *"The shelter runs itself — volunteers know their shifts, vets track every treatment, fosters stay connected"*

---

## Goal

Digitize the daily operations that currently happen on paper or WhatsApp groups. Volunteer coordination, medical record-keeping, and foster family management become structured workflows. After V4, the shelter has a complete operational backbone — not just adoptions and donations, but the full daily reality of running an animal rescue.

---

## What V4 Adds

### 1. Volunteer Management (EPIC-5)

| Feature | Description | Priority |
|---------|-------------|----------|
| Volunteer registration | Public sign-up form with skills, availability, phone | P0 |
| Volunteer profiles | Staff view: contact info, skills, hours logged, reliability score | P0 |
| Shift scheduling | Weekly calendar with available slots, self-sign-up | P0 |
| Shift reminders | WhatsApp/email 24h before scheduled shift | P1 |
| Task assignment | Staff assigns tasks to volunteers (feeding, cleaning, walking) | P1 |
| Hours tracking | Check-in/check-out, monthly hours report | P1 |
| Volunteer recognition | Monthly top volunteers, certificate generation | P2 |
| Volunteer dashboard | Personal view: upcoming shifts, hours logged, tasks | P1 |

### 2. Medical Records (EPIC-4)

| Feature | Description | Priority |
|---------|-------------|----------|
| Medical record schema | Per-animal medical history with timestamped entries | P0 |
| Veterinary notes | Vet creates examination notes, diagnosis, treatment plan | P0 |
| Vaccination tracking | Vaccine type, date, next due date, batch number | P0 |
| Medication log | Current medications, dosage, schedule, administering staff | P0 |
| Medical timeline | Chronological view of all medical events per animal | P1 |
| Surgery records | Pre-op, procedure, post-op notes, recovery status | P1 |
| Medical alerts | Flag animals with upcoming vaccinations or treatments due | P1 |
| Vet assignment | Assign external vets to animals, track visits | P2 |
| Medical hold status | Animals under treatment can't be listed for adoption | P0 |
| Weight/growth tracking | Periodic weight entries, growth chart visualization | P2 |

### 3. Foster Program (New — not in current epics)

| Feature | Description | Priority |
|---------|-------------|----------|
| Foster family registration | Sign-up with home details, experience, capacity | P1 |
| Foster placement | Assign animal to foster family with expected duration | P1 |
| Foster check-ins | Periodic status updates from foster family (form + photos) | P1 |
| Foster-to-adopt pathway | Foster families get priority adoption option | P2 |
| Foster dashboard | Active placements, upcoming check-ins, return dates | P2 |

### 4. Animal Profile Enhancements

| Feature | Description | Priority |
|---------|-------------|----------|
| Behavior notes | Temperament, training progress, special needs | P1 |
| Intake records | Where found, condition on arrival, intake photos | P0 |
| Animal timeline | Combined view: intake, medical, foster, adoption events | P1 |
| QR code per animal | Print QR → scan → view profile (useful for shelter visits) | P2 |

---

## Acceptance Criteria

V4 is complete when:

- [ ] Volunteer can register through the public website
- [ ] Staff can create weekly shift schedules with available slots
- [ ] Volunteer can self-assign to open shifts
- [ ] Volunteer receives reminder 24h before their shift
- [ ] Staff can log volunteer check-in and check-out times
- [ ] Vet can create medical examination notes for an animal
- [ ] Vaccination records track type, date, and next-due date
- [ ] Animals with medical holds are excluded from adoption listings
- [ ] Medical timeline shows chronological history per animal
- [ ] Foster family can register and receive animal placements
- [ ] Foster family can submit check-in updates with photos
- [ ] Animal detail page shows combined timeline (medical + foster + adoption)
- [ ] All new features have test coverage >80%
- [ ] All new API endpoints enforce role-based access (vet, staff, admin)

---

## What V4 Does NOT Include

- Real-time admin dashboard (V5)
- Advanced analytics and reporting (V5)
- Full-text search optimization (V5)
- Public volunteer leaderboard (V5)
- Telemedicine / video vet consultations (future)
- Inventory management (food, medicine stock — future)

---

## Technical Notes

### New Database Models

```
MedicalRecord
  - id, animal_id (FK), vet_id (FK), record_type (exam/vaccine/surgery/medication)
  - title, notes, diagnosis, treatment_plan
  - created_at, updated_at

Vaccination
  - id, medical_record_id (FK), vaccine_name, batch_number
  - administered_at, next_due_at

Medication
  - id, animal_id (FK), name, dosage, frequency
  - started_at, ended_at, prescribed_by (FK)

Volunteer
  - id, user_id (FK), phone, skills (ARRAY), availability (JSONB)
  - hours_logged, reliability_score, status

Shift
  - id, date, start_time, end_time, location, capacity
  - description, required_skills

ShiftAssignment
  - id, shift_id (FK), volunteer_id (FK), status (assigned/checked_in/completed/no_show)
  - checked_in_at, checked_out_at

FosterFamily
  - id, user_id (FK), home_type, experience_level, max_animals
  - status (active/inactive/on_hold)

FosterPlacement
  - id, animal_id (FK), foster_family_id (FK)
  - placed_at, expected_return_at, actual_return_at, status
```

### New Alembic Migrations

- `005_add_medical_records.py` — Medical records, vaccinations, medications
- `006_add_volunteers_and_shifts.py` — Volunteer profiles, shifts, assignments
- `007_add_foster_program.py` — Foster families, placements

### New API Routers

- `src/api/medical.py` — CRUD for medical records, vaccinations, medications
- `src/api/volunteers.py` — Volunteer registration, shift management
- `src/api/foster.py` — Foster family management, placements

### Role Additions

| Role | New Permissions |
|------|----------------|
| **vet** | Create/edit medical records, view animal profiles |
| **volunteer** | View own shifts, check-in/out, view assigned tasks |
| **foster** | View placed animal, submit check-ins |

---

## Risk Register

| Risk | Impact | Mitigation |
|------|--------|------------|
| Scope creep from medical features | V4 takes 8+ weeks | Strict P0-only for first pass, P1/P2 in patch releases |
| Volunteer no-shows | Scheduling system looks broken | No-show tracking + reliability score informs future assignments |
| Vet data entry resistance | Medical records stay empty | Mobile-friendly forms, minimal required fields |
| Foster liability concerns | Legal exposure for shelter | Foster agreement template, clear terms of responsibility |
| Complex role matrix | Auth bugs, permission leaks | Integration tests for every role + endpoint combination |

---

## Estimated Effort

| Area | New Tickets | Story Points | Weeks |
|------|-------------|-------------|-------|
| Medical records system | 4-5 | 15-18 | 2-3 |
| Volunteer management | 4-5 | 13-15 | 2-2.5 |
| Foster program | 3-4 | 10-12 | 1.5-2 |
| Animal profile enhancements | 2-3 | 5-8 | 0.5-1 |
| Frontend pages (staff + public) | 4-5 | 10-12 | 1.5-2 |
| **Total** | **17-22** | **53-65** | **8-10** |

---

## Demo Script (Client Presentation)

1. Show a volunteer registering on the website
2. Staff creates next week's shift schedule
3. Volunteer signs up for a feeding shift — gets WhatsApp confirmation
4. Vet logs a medical examination for a rescued dog
5. Show vaccination record with next-due-date alert
6. Place an animal with a foster family
7. Foster family submits a check-in with photos
8. Show the animal's combined timeline: intake, medical, foster, available

*"From the moment an animal arrives to the day it goes home — every step is tracked, every person is connected."*

---

## Dependencies

- **Requires**: V3 notification engine (shift reminders, medical alerts)
- **Requires**: V1 auth system (new vet/volunteer/foster roles)
- **Blocks V5**: Dashboard analytics consume volunteer + medical data
- **External**: Veterinary terminology review (Spanish), foster agreement legal template

---

*Epics touched: EPIC-4 (complete), EPIC-5 (complete), plus new Foster epic*
*Target release tag: `v4.0.0`*
