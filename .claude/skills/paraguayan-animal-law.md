---
name: paraguayan-animal-law
description: Legal and regulatory context for animal shelter operations in Paraguay. Load when working on adoption workflows, registration, contracts, or compliance features.
triggers: registration, legal, permit, municipal, adoption contract, Paraguay law, vaccination, microchip, sterilization, animal welfare, ley, municipalidad, registro
---

# Paraguayan Animal Shelter Legal Context

## Overview

Paraguay's animal welfare legal framework is decentralized — national laws set baselines, but municipalities have significant authority over shelter registration and operational requirements. The shelter must comply at both levels.

---

## National Legal Framework

### Ley 4840/2013 — Animal Welfare Law

The primary national animal welfare legislation:
- Prohibits animal cruelty and abandonment
- Establishes basic standards for shelter conditions
- Requires adequate food, water, and veterinary care
- Mandates that shelters maintain health records per animal

### Ley 3140/2006 — Animal Disease Control

- **Rabies vaccination**: Mandatory before any animal transfer/adoption
- Establishes national vaccination campaigns (annual)
- Shelters must maintain vaccination records

### Decreto 1237 — Veterinary Registry

- Veterinarians treating shelter animals must be registered with SENACSA (Servicio Nacional de Calidad y Salud Animal)
- SENACSA issues health certificates for animal transport

---

## Municipal Requirements

Each municipalidad has its own ordinances. Key requirements typically include:

### Shelter Registration

- Register with the local Dirección de Sanidad Animal (or equivalent)
- Required documents typically:
  - Legal personería jurídica (legal entity registration)
  - Property title or lease of shelter facility
  - Veterinary professional attached to the shelter
  - Operational plan describing capacity and procedures

### Capacity Limits

- Many municipalities set animal-per-area ratios
- Typical: 1 dog per 6-10m² of kennel space
- Overcrowding can result in operating permit revocation

### Inspection Regime

- Municipal veterinary inspection: typically annual, may be more frequent
- SENACSA may conduct independent inspections
- Prepare: vaccination records, feeding logs, medical records per animal

---

## Adoption Process — Legal Requirements

### Minimum Documentation for Adoption

1. **Animal health certificate** (from registered vet): vaccination status, current health assessment
2. **Adoption contract** (signed by adopter): establishes legal transfer of animal
3. **Adopter ID**: Cédula de identidad (Paraguayan) or passport (foreign nationals)
4. **Vaccination record**: Proof of rabies vaccination (required by Ley 3140/2006)

### Recommended Adoption Contract Clauses

```
1. Animal description: species, breed, sex, approximate age, physical description
2. Adopter identification: full name, cédula/passport, address, phone, email
3. Vaccination history: documented vaccines with dates
4. Sterilization clause: commitment to sterilize if not already done (with timeline)
5. Return policy: adopter agrees to return animal to shelter rather than abandon
6. Home inspection clause (recommended): shelter may verify living conditions
7. Prohibition on resale: animal may not be sold or transferred without shelter consent
8. Cruelty prohibition: adopter acknowledges animal welfare law obligations
9. Microchip acknowledgment: if microchipped, adopter agrees not to remove/alter
```

### Adoption Contract Data Model

```sql
CREATE TABLE adoptions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    animal_id       UUID NOT NULL REFERENCES animals(id),
    adopter_id      UUID NOT NULL REFERENCES adopters(id),
    adopted_at      DATE NOT NULL,
    contract_signed BOOLEAN NOT NULL DEFAULT FALSE,
    contract_pdf_url TEXT,                          -- stored document
    vet_certificate_url TEXT,                       -- health cert at adoption
    sterilization_required BOOLEAN NOT NULL,
    sterilization_deadline DATE,                    -- if required
    follow_up_date  DATE,                           -- scheduled check-in
    status          TEXT NOT NULL DEFAULT 'active', -- active / returned / unknown
    notes           TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

## Veterinary Requirements

### Mandatory Records Per Animal

- Species, breed, sex, estimated age, color/markings
- Intake date and source (found, surrendered, rescued)
- Vaccination dates: rabies (mandatory), parvovirus, distemper (recommended)
- Deworming dates
- Medical treatments and diagnoses
- Sterilization date (if performed)
- Microchip number (if implanted)

### Sterilization

- **Not nationally mandated** as of 2026, but strongly encouraged by animal welfare ordinances in Asunción and major municipalities
- Many adoption programs condition adoption on sterilization (before or post-adoption with verification)
- Some municipalities run free sterilization campaigns — track and integrate

### Microchipping

- **Not nationally mandated** as of 2026
- ISO 11784/11785 standard (15-digit code) is the international standard to follow
- Increasingly required for dogs > 6 months in Asunción metropolitan area
- Database: register chips with SENACSA national registry when available

---

## Data Implications for the Platform

### Required Fields at Intake

```python
# Minimum viable animal record
class AnimalIntake:
    species: Literal["dog", "cat", "other"]
    intake_date: date
    intake_source: Literal["found", "surrendered", "rescued", "transferred"]
    estimated_age_months: int | None
    sex: Literal["male", "female", "unknown"]
    is_sterilized: bool
    rabies_vaccinated: bool
    rabies_vaccine_date: date | None
    microchip_number: str | None  # 15-digit ISO, None if not chipped
    health_status: Literal["healthy", "under_treatment", "quarantine", "critical"]
```

### Animal Status Transitions

```
intake → quarantine → available_for_adoption → adopted
                   ↘ foster → available_for_adoption → adopted
                   ↘ under_treatment → available_for_adoption → adopted
                   ↘ deceased
```

Valid transition rules:
- `quarantine` minimum: 10 days (standard veterinary observation)
- `available_for_adoption` requires: rabies vaccination + vet clearance
- `adopted` requires: signed contract + health certificate
- `deceased` is terminal — no transitions out

---

## Cross-Border Considerations (EU Donors Visiting / Dutch Owner)

### Animal Export (if owner brings animals to Europe)

- EU health certificate required (TRACES system)
- Rabies vaccination: must be at least 21 days before travel, chip before vaccine
- Tapeworm treatment for dogs entering some EU countries
- Contact SENACSA for export health certificates

### Import of Foreign Donation Goods (food, medicine, equipment)

- Non-commercial donations: may be exempt from import duties with DGEEC documentation
- Veterinary medicines: require SENACSA import permit
- Keep all customs documentation for audit purposes
