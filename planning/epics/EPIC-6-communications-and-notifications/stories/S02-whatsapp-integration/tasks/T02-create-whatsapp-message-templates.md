---
task: T02
story: S02
epic: EPIC-6
title: Create WhatsApp message templates
status: ready
priority: medium
created: 2026-03-25T17:13:26.732971
---

# T02: Create WhatsApp message templates

## Description

Build typed WhatsApp message template functions for the four main transactional events.
WhatsApp messages are plain text (no HTML), kept concise (under 800 characters), and
friendly in tone. Templates follow Twilio's approved message template format — required
for production WhatsApp Business API (non-sandbox) sends.

**Character discipline**: WhatsApp displays messages in a chat bubble. Long blocks of text
are unreadable on mobile. Each template targets 200–500 characters. Use line breaks (`\n`)
for structure.

**Template pre-registration**: For production sends outside the 24-hour customer service
window, Twilio requires WhatsApp-approved message templates (registered in the Twilio
Console). Template functions here generate strings matching registered template bodies
(parameter substitution via Twilio's Content API or inline body with identical wording).

---

## Acceptance Criteria

- [ ] `src/lib/whatsapp/templates/` directory with one file per event type
- [ ] `adoption-approved.ts` — adoption approved notification
- [ ] `donation-received.ts` — donation receipt acknowledgement
- [ ] `shift-reminder.ts` — volunteer shift reminder (sent 24h before)
- [ ] `general-message.ts` — free-form admin-to-volunteer message builder
- [ ] `src/lib/whatsapp/templates/index.ts` — re-exports all builders
- [ ] 8 vitest unit tests verifying message content and character limits

---

## Implementation Notes

### Directory structure

```
src/lib/whatsapp/
├── send-whatsapp.ts              # T01 — Twilio wrapper
└── templates/
    ├── adoption-approved.ts
    ├── donation-received.ts
    ├── shift-reminder.ts
    ├── general-message.ts
    └── index.ts
```

### Shared constants — `src/lib/whatsapp/templates/_constants.ts`

```typescript
export const WA_MAX_CHARS = 1600; // Twilio/WhatsApp hard limit
export const WA_RECOMMENDED_CHARS = 600; // Target for readability on mobile
export const SHELTER_NAME = 'Refugio Animal Paraguay';
export const SHELTER_PHONE = '+595 21 XXX-XXXX'; // Update with real number
```

### Template 1 — `src/lib/whatsapp/templates/adoption-approved.ts`

```typescript
import { SHELTER_NAME } from './_constants';

export interface AdoptionApprovedWAData {
  adopterName: string;
  animalName: string;
  pickupDate: string;   // formatted date string, e.g. "miércoles 10 de abril"
  contactPhone: string; // staff contact for questions
}

/**
 * WhatsApp message sent to adopter when their adoption request is approved.
 * Matches registered template: 'adoption_approved_v1'
 */
export function buildAdoptionApprovedWA(data: AdoptionApprovedWAData): string {
  return [
    `🐾 *${SHELTER_NAME}*`,
    ``,
    `¡Hola ${data.adopterName}! 🎉`,
    `Tu solicitud de adopción para *${data.animalName}* fue *aprobada*.`,
    ``,
    `📅 Retiro: ${data.pickupDate}`,
    `📞 Consultas: ${data.contactPhone}`,
    ``,
    `¡Gracias por darle un hogar! 🐶`,
  ].join('\n');
}
```

### Template 2 — `src/lib/whatsapp/templates/donation-received.ts`

```typescript
import { SHELTER_NAME } from './_constants';

export interface DonationReceivedWAData {
  donorName: string;
  amountDisplay: string; // e.g. "150.000 Gs." or "€50"
}

/**
 * WhatsApp receipt sent to donor after a successful donation.
 * Matches registered template: 'donation_received_v1'
 */
export function buildDonationReceivedWA(data: DonationReceivedWAData): string {
  return [
    `🐾 *${SHELTER_NAME}*`,
    ``,
    `¡Muchas gracias, ${data.donorName}! 💚`,
    `Recibimos tu donación de *${data.amountDisplay}* con éxito.`,
    ``,
    `Tu apoyo nos permite seguir rescatando y cuidando animales.`,
    `Revisá tu correo para el recibo completo.`,
  ].join('\n');
}
```

### Template 3 — `src/lib/whatsapp/templates/shift-reminder.ts`

```typescript
import { SHELTER_NAME } from './_constants';

export interface ShiftReminderWAData {
  volunteerName: string;
  shiftDate: string;      // e.g. "mañana, martes 15 de abril"
  shiftStartTime: string; // e.g. "08:00"
  shiftEndTime: string;   // e.g. "12:00"
  role: string;           // e.g. "Cuidado de animales"
  location: string;       // e.g. "Refugio Central, Luque"
  coordinatorPhone: string;
}

/**
 * Reminder sent ~24 hours before a volunteer shift.
 * Matches registered template: 'shift_reminder_v1'
 */
export function buildShiftReminderWA(data: ShiftReminderWAData): string {
  return [
    `🐾 *${SHELTER_NAME}*`,
    ``,
    `Hola ${data.volunteerName}, te recordamos tu turno de mañana:`,
    ``,
    `📅 ${data.shiftDate}`,
    `🕐 ${data.shiftStartTime} – ${data.shiftEndTime}`,
    `🐕 ${data.role}`,
    `📍 ${data.location}`,
    ``,
    `Si no podés asistir, avisanos al ${data.coordinatorPhone}.`,
    `¡Gracias por tu dedicación! 🙏`,
  ].join('\n');
}
```

### Template 4 — `src/lib/whatsapp/templates/general-message.ts`

Free-form messages sent by admins to volunteers via the admin dashboard.
These are session messages (within the 24h customer service window) and do not
require pre-registration.

```typescript
import { SHELTER_NAME } from './_constants';

export interface GeneralMessageWAData {
  recipientName: string;
  messageBody: string;
  senderName: string;  // staff member sending the message
}

/**
 * General-purpose WhatsApp message from a staff member to a volunteer.
 * Used for custom notifications not covered by other templates.
 * Only valid within a 24-hour WhatsApp session window.
 */
export function buildGeneralMessageWA(data: GeneralMessageWAData): string {
  return [
    `🐾 *${SHELTER_NAME}*`,
    ``,
    `Hola ${data.recipientName},`,
    ``,
    data.messageBody,
    ``,
    `— ${data.senderName}`,
  ].join('\n');
}
```

### `src/lib/whatsapp/templates/index.ts`

```typescript
export { buildAdoptionApprovedWA } from './adoption-approved';
export type { AdoptionApprovedWAData } from './adoption-approved';

export { buildDonationReceivedWA } from './donation-received';
export type { DonationReceivedWAData } from './donation-received';

export { buildShiftReminderWA } from './shift-reminder';
export type { ShiftReminderWAData } from './shift-reminder';

export { buildGeneralMessageWA } from './general-message';
export type { GeneralMessageWAData } from './general-message';
```

### Unit tests — `src/lib/whatsapp/templates/__tests__/whatsapp-templates.test.ts`

```typescript
import { describe, it, expect } from 'vitest';
import { buildAdoptionApprovedWA } from '../adoption-approved';
import { buildDonationReceivedWA } from '../donation-received';
import { buildShiftReminderWA } from '../shift-reminder';
import { buildGeneralMessageWA } from '../general-message';
import { WA_MAX_CHARS } from '../_constants';

describe('buildAdoptionApprovedWA', () => {
  it('includes adopter name and animal name', () => {
    const msg = buildAdoptionApprovedWA({
      adopterName: 'María',
      animalName: 'Pelusa',
      pickupDate: 'miércoles 10 de abril',
      contactPhone: '0981-123456',
    });

    expect(msg).toContain('María');
    expect(msg).toContain('Pelusa');
    expect(msg).toContain('aprobada');
  });

  it('stays within WhatsApp character limit', () => {
    const msg = buildAdoptionApprovedWA({
      adopterName: 'A'.repeat(50),
      animalName: 'B'.repeat(50),
      pickupDate: 'lunes',
      contactPhone: '0981-000000',
    });

    expect(msg.length).toBeLessThanOrEqual(WA_MAX_CHARS);
  });
});

describe('buildDonationReceivedWA', () => {
  it('includes donor name and amount', () => {
    const msg = buildDonationReceivedWA({
      donorName: 'Juan',
      amountDisplay: '€50',
    });

    expect(msg).toContain('Juan');
    expect(msg).toContain('€50');
    expect(msg).toContain('donación');
  });
});

describe('buildShiftReminderWA', () => {
  it('includes shift time, role, and location', () => {
    const msg = buildShiftReminderWA({
      volunteerName: 'Ana',
      shiftDate: 'mañana, martes 15 de abril',
      shiftStartTime: '08:00',
      shiftEndTime: '12:00',
      role: 'Cuidado de perros',
      location: 'Refugio Central',
      coordinatorPhone: '0981-999999',
    });

    expect(msg).toContain('08:00');
    expect(msg).toContain('12:00');
    expect(msg).toContain('Cuidado de perros');
    expect(msg).toContain('Refugio Central');
  });

  it('includes coordinator phone for cancellation', () => {
    const msg = buildShiftReminderWA({
      volunteerName: 'Luis',
      shiftDate: 'mañana',
      shiftStartTime: '07:00',
      shiftEndTime: '11:00',
      role: 'Limpieza',
      location: 'Luque',
      coordinatorPhone: '0991-555555',
    });

    expect(msg).toContain('0991-555555');
  });
});

describe('buildGeneralMessageWA', () => {
  it('includes recipient name, body, and sender', () => {
    const msg = buildGeneralMessageWA({
      recipientName: 'Carlos',
      messageBody: 'El turno del sábado fue cancelado.',
      senderName: 'Laura (Coordinadora)',
    });

    expect(msg).toContain('Carlos');
    expect(msg).toContain('El turno del sábado fue cancelado.');
    expect(msg).toContain('Laura (Coordinadora)');
  });
});
```

### Twilio template registration (production checklist)

Before going to production, register the following templates in Twilio Console →
Messaging → Content Template Builder:

| Template Name | Matches Function | Category |
|---|---|---|
| `adoption_approved_v1` | `buildAdoptionApprovedWA` | UTILITY |
| `donation_received_v1` | `buildDonationReceivedWA` | UTILITY |
| `shift_reminder_v1` | `buildShiftReminderWA` | UTILITY |

General messages (`buildGeneralMessageWA`) use the session window — no pre-registration
needed but only valid within 24h of the recipient initiating contact.

---

## Files to Create / Modify

| Path | Action | Notes |
|------|--------|-------|
| `src/lib/whatsapp/templates/_constants.ts` | Create | `WA_MAX_CHARS`, `SHELTER_NAME`, etc. |
| `src/lib/whatsapp/templates/adoption-approved.ts` | Create | Adoption approved WA template |
| `src/lib/whatsapp/templates/donation-received.ts` | Create | Donation receipt WA template |
| `src/lib/whatsapp/templates/shift-reminder.ts` | Create | Shift reminder WA template |
| `src/lib/whatsapp/templates/general-message.ts` | Create | Free-form admin message template |
| `src/lib/whatsapp/templates/index.ts` | Create | Re-exports all four builders |
| `src/lib/whatsapp/templates/__tests__/whatsapp-templates.test.ts` | Create | 8 unit tests |

---

## Definition of Done

- [ ] All 4 template functions created with typed data interfaces
- [ ] All messages stay under `WA_MAX_CHARS` (1600) even with max-length inputs
- [ ] All UI text in Spanish
- [ ] No HTML in message bodies — plain text and `*bold*` markdown only
- [ ] `index.ts` re-exports all builders and types
- [ ] All 8 unit tests pass
- [ ] Twilio production template registration checklist documented
