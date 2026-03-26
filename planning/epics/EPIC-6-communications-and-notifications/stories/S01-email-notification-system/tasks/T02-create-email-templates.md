---
task: T02
story: S01
epic: EPIC-6
title: Create email templates
status: ready
priority: medium
created: 2026-03-25T17:13:26.732667
---

# T02: Create email templates

## Description

Build typed HTML email template functions for the four main transactional email events:
adoption approval, donation receipt, volunteer shift confirmation, and password reset.
Templates are plain TypeScript functions that return an HTML string — no templating engine
dependency. All UI text in Spanish (Paraguayan context).

**Approach**: Each template is a pure function `(data) => string`. No React Email, no
Handlebars, no MJML build step. Templates use inline CSS for maximum email client
compatibility. Tests assert that required data fields appear in the rendered output.

---

## Acceptance Criteria

- [ ] `src/lib/email/templates/` directory with one file per template
- [ ] `adoption-approval.ts` — adoption confirmed, animal name, adopter name, next steps
- [ ] `donation-receipt.ts` — amount (PYG and/or EUR), donor name, date, thank-you copy
- [ ] `volunteer-shift-confirmation.ts` — shift date/time, role, location, contact
- [ ] `password-reset.ts` — reset link with expiry notice
- [ ] `src/lib/email/templates/index.ts` — re-exports all four builders
- [ ] Vitest tests for each template verifying required fields appear in output (8 tests)
- [ ] All templates use `FROM_EMAIL` via the `sendEmail` wrapper (no standalone sends)

---

## Implementation Notes

### Directory structure

```
src/lib/email/
├── send-email.ts                    # T01 — Resend wrapper
└── templates/
    ├── adoption-approval.ts
    ├── donation-receipt.ts
    ├── volunteer-shift-confirmation.ts
    ├── password-reset.ts
    └── index.ts
```

### Shared layout helper — `src/lib/email/templates/_layout.ts`

A minimal wrapper to avoid repeating the outer HTML shell in every template:

```typescript
export function emailLayout(content: string, title: string): string {
  return `<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>${escapeHtml(title)}</title>
</head>
<body style="margin:0;padding:0;background-color:#f4f4f4;font-family:Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f4f4;padding:24px 0;">
    <tr>
      <td align="center">
        <table width="600" cellpadding="0" cellspacing="0"
               style="background-color:#ffffff;border-radius:8px;overflow:hidden;max-width:600px;">
          <!-- Header -->
          <tr>
            <td style="background-color:#2d6a4f;padding:24px 32px;">
              <p style="margin:0;color:#ffffff;font-size:20px;font-weight:bold;">
                🐾 Refugio Animal Paraguay
              </p>
            </td>
          </tr>
          <!-- Body -->
          <tr>
            <td style="padding:32px;">
              ${content}
            </td>
          </tr>
          <!-- Footer -->
          <tr>
            <td style="background-color:#f9f9f9;padding:16px 32px;border-top:1px solid #e0e0e0;">
              <p style="margin:0;color:#888;font-size:12px;text-align:center;">
                Refugio Animal Paraguay — Asunción, Paraguay<br/>
                Este es un correo automático. Para consultas, escribinos a
                <a href="mailto:info@refugioanimalpy.org" style="color:#2d6a4f;">
                  info@refugioanimalpy.org
                </a>
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>`;
}

/** Escape characters that could cause XSS in HTML output. */
export function escapeHtml(str: string): string {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}
```

### Template 1 — `src/lib/email/templates/adoption-approval.ts`

```typescript
import { emailLayout, escapeHtml } from './_layout';

export interface AdoptionApprovalData {
  adopterName: string;
  animalName: string;
  animalSpecies: string;    // e.g. "perro", "gato"
  adoptionDate: string;     // ISO date string
  pickupInstructions: string;
  contactEmail: string;
}

export function buildAdoptionApprovalEmail(data: AdoptionApprovalData): string {
  const formattedDate = new Date(data.adoptionDate).toLocaleDateString('es-PY', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });

  const content = `
    <h2 style="color:#2d6a4f;margin:0 0 16px;">
      ¡Felicitaciones, ${escapeHtml(data.adopterName)}!
    </h2>
    <p style="color:#333;line-height:1.6;">
      Nos alegra comunicarte que tu solicitud de adopción para
      <strong>${escapeHtml(data.animalName)}</strong>
      (${escapeHtml(data.animalSpecies)}) fue <strong>aprobada</strong>.
    </p>
    <div style="background-color:#f0faf4;border-left:4px solid #2d6a4f;
                padding:16px;margin:24px 0;border-radius:4px;">
      <p style="margin:0 0 8px;font-weight:bold;color:#2d6a4f;">
        📅 Fecha acordada
      </p>
      <p style="margin:0;color:#333;">${escapeHtml(formattedDate)}</p>
    </div>
    <h3 style="color:#333;font-size:16px;">Instrucciones para el retiro</h3>
    <p style="color:#333;line-height:1.6;">${escapeHtml(data.pickupInstructions)}</p>
    <p style="color:#333;line-height:1.6;">
      Si tenés alguna pregunta, respondé este correo o contactanos a
      <a href="mailto:${escapeHtml(data.contactEmail)}"
         style="color:#2d6a4f;">${escapeHtml(data.contactEmail)}</a>.
    </p>
    <p style="color:#333;line-height:1.6;">
      ¡Gracias por darle un hogar a ${escapeHtml(data.animalName)}! 🐾
    </p>
  `;

  return emailLayout(content, `Adopción aprobada — ${data.animalName}`);
}
```

### Template 2 — `src/lib/email/templates/donation-receipt.ts`

```typescript
import { emailLayout, escapeHtml } from './_layout';

export interface DonationReceiptData {
  donorName: string;
  amountPyg?: number;   // Guaraníes (integer, no decimals)
  amountEur?: number;   // Euros (2 decimal places)
  donationDate: string; // ISO date string
  donationId: string;   // UUID for reference
  message?: string;     // Optional donor message
}

export function buildDonationReceiptEmail(data: DonationReceiptData): string {
  const formattedDate = new Date(data.donationDate).toLocaleDateString('es-PY', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });

  const amountLines: string[] = [];
  if (data.amountPyg) {
    amountLines.push(
      `<strong>${data.amountPyg.toLocaleString('es-PY')} Gs.</strong> (Guaraníes)`
    );
  }
  if (data.amountEur) {
    amountLines.push(
      `<strong>€${data.amountEur.toFixed(2)}</strong> (Euros)`
    );
  }

  const content = `
    <h2 style="color:#2d6a4f;margin:0 0 16px;">
      Recibo de donación — ¡Gracias, ${escapeHtml(data.donorName)}!
    </h2>
    <p style="color:#333;line-height:1.6;">
      Recibimos tu donación con éxito. Cada contribución nos permite seguir
      rescatando y cuidando animales en Paraguay.
    </p>
    <div style="background-color:#f0faf4;border:1px solid #b7dfca;
                padding:20px;margin:24px 0;border-radius:6px;">
      <table width="100%" cellpadding="4" cellspacing="0">
        <tr>
          <td style="color:#666;font-size:14px;">Fecha</td>
          <td style="color:#333;font-size:14px;text-align:right;">
            ${escapeHtml(formattedDate)}
          </td>
        </tr>
        <tr>
          <td style="color:#666;font-size:14px;">Monto</td>
          <td style="color:#333;font-size:14px;text-align:right;">
            ${amountLines.join('<br/>')}
          </td>
        </tr>
        <tr>
          <td style="color:#666;font-size:14px;">Referencia</td>
          <td style="color:#888;font-size:12px;text-align:right;">
            ${escapeHtml(data.donationId)}
          </td>
        </tr>
      </table>
    </div>
    ${data.message
      ? `<p style="color:#555;font-style:italic;border-left:3px solid #ccc;
                   padding-left:12px;margin:16px 0;">
           "${escapeHtml(data.message)}"
         </p>`
      : ''
    }
    <p style="color:#333;line-height:1.6;">
      Guardá este correo como comprobante de tu donación.
    </p>
  `;

  return emailLayout(content, 'Recibo de donación — Refugio Animal Paraguay');
}
```

### Template 3 — `src/lib/email/templates/volunteer-shift-confirmation.ts`

```typescript
import { emailLayout, escapeHtml } from './_layout';

export interface ShiftConfirmationData {
  volunteerName: string;
  shiftDate: string;      // ISO date string
  shiftStartTime: string; // e.g. "08:00"
  shiftEndTime: string;   // e.g. "12:00"
  role: string;           // e.g. "Cuidado de animales"
  location: string;       // e.g. "Refugio Central, Luque"
  coordinatorName: string;
  coordinatorPhone: string;
}

export function buildShiftConfirmationEmail(data: ShiftConfirmationData): string {
  const formattedDate = new Date(data.shiftDate).toLocaleDateString('es-PY', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });

  const content = `
    <h2 style="color:#2d6a4f;margin:0 0 16px;">
      Turno confirmado, ${escapeHtml(data.volunteerName)}
    </h2>
    <p style="color:#333;line-height:1.6;">
      Tu turno de voluntariado fue registrado. ¡Gracias por tu compromiso!
    </p>
    <div style="background-color:#f0faf4;border:1px solid #b7dfca;
                padding:20px;margin:24px 0;border-radius:6px;">
      <table width="100%" cellpadding="6" cellspacing="0">
        <tr>
          <td style="color:#666;font-size:14px;width:40%;">📅 Fecha</td>
          <td style="color:#333;font-size:14px;">
            ${escapeHtml(formattedDate)}
          </td>
        </tr>
        <tr>
          <td style="color:#666;font-size:14px;">🕐 Horario</td>
          <td style="color:#333;font-size:14px;">
            ${escapeHtml(data.shiftStartTime)} – ${escapeHtml(data.shiftEndTime)}
          </td>
        </tr>
        <tr>
          <td style="color:#666;font-size:14px;">🐾 Tarea</td>
          <td style="color:#333;font-size:14px;">${escapeHtml(data.role)}</td>
        </tr>
        <tr>
          <td style="color:#666;font-size:14px;">📍 Lugar</td>
          <td style="color:#333;font-size:14px;">${escapeHtml(data.location)}</td>
        </tr>
      </table>
    </div>
    <p style="color:#333;line-height:1.6;">
      Si necesitás cancelar o tenés alguna pregunta, contactá a
      <strong>${escapeHtml(data.coordinatorName)}</strong>
      al <strong>${escapeHtml(data.coordinatorPhone)}</strong>
      con al menos 24 horas de anticipación.
    </p>
  `;

  return emailLayout(content, 'Confirmación de turno — Refugio Animal Paraguay');
}
```

### Template 4 — `src/lib/email/templates/password-reset.ts`

```typescript
import { emailLayout, escapeHtml } from './_layout';

export interface PasswordResetData {
  userName: string;
  resetUrl: string;
  expiresInMinutes: number; // typically 60
}

export function buildPasswordResetEmail(data: PasswordResetData): string {
  const content = `
    <h2 style="color:#2d6a4f;margin:0 0 16px;">
      Restablecer contraseña
    </h2>
    <p style="color:#333;line-height:1.6;">
      Hola ${escapeHtml(data.userName)}, recibimos una solicitud para
      restablecer la contraseña de tu cuenta.
    </p>
    <div style="text-align:center;margin:32px 0;">
      <a href="${escapeHtml(data.resetUrl)}"
         style="background-color:#2d6a4f;color:#ffffff;text-decoration:none;
                padding:14px 32px;border-radius:6px;font-size:16px;
                font-weight:bold;display:inline-block;">
        Restablecer contraseña
      </a>
    </div>
    <p style="color:#888;font-size:13px;line-height:1.6;">
      Este enlace es válido por
      <strong>${data.expiresInMinutes} minutos</strong>.
      Si no solicitaste este cambio, ignorá este correo — tu contraseña
      no será modificada.
    </p>
    <p style="color:#aaa;font-size:12px;word-break:break-all;">
      Si el botón no funciona, copiá este enlace en tu navegador:<br/>
      ${escapeHtml(data.resetUrl)}
    </p>
  `;

  return emailLayout(content, 'Restablecer contraseña — Refugio Animal Paraguay');
}
```

### `src/lib/email/templates/index.ts`

```typescript
export { buildAdoptionApprovalEmail } from './adoption-approval';
export type { AdoptionApprovalData } from './adoption-approval';

export { buildDonationReceiptEmail } from './donation-receipt';
export type { DonationReceiptData } from './donation-receipt';

export { buildShiftConfirmationEmail } from './volunteer-shift-confirmation';
export type { ShiftConfirmationData } from './volunteer-shift-confirmation';

export { buildPasswordResetEmail } from './password-reset';
export type { PasswordResetData } from './password-reset';
```

### Unit tests — `src/lib/email/templates/__tests__/email-templates.test.ts`

```typescript
import { describe, it, expect } from 'vitest';
import { buildAdoptionApprovalEmail } from '../adoption-approval';
import { buildDonationReceiptEmail } from '../donation-receipt';
import { buildShiftConfirmationEmail } from '../volunteer-shift-confirmation';
import { buildPasswordResetEmail } from '../password-reset';

describe('buildAdoptionApprovalEmail', () => {
  it('includes adopter name and animal name', () => {
    const html = buildAdoptionApprovalEmail({
      adopterName: 'María García',
      animalName: 'Pelusa',
      animalSpecies: 'gato',
      adoptionDate: '2026-04-10',
      pickupInstructions: 'Venir a las 9am con DNI.',
      contactEmail: 'adopciones@refugio.org',
    });

    expect(html).toContain('María García');
    expect(html).toContain('Pelusa');
    expect(html).toContain('gato');
  });

  it('escapes HTML special characters in adopter name', () => {
    const html = buildAdoptionApprovalEmail({
      adopterName: '<script>alert("xss")</script>',
      animalName: 'Firulais',
      animalSpecies: 'perro',
      adoptionDate: '2026-04-10',
      pickupInstructions: 'Venir a las 9am.',
      contactEmail: 'info@refugio.org',
    });

    expect(html).not.toContain('<script>');
    expect(html).toContain('&lt;script&gt;');
  });
});

describe('buildDonationReceiptEmail', () => {
  it('includes donor name and PYG amount', () => {
    const html = buildDonationReceiptEmail({
      donorName: 'Juan Pérez',
      amountPyg: 150000,
      donationDate: '2026-03-25',
      donationId: 'uuid-1234',
    });

    expect(html).toContain('Juan Pérez');
    expect(html).toContain('150');
    expect(html).toContain('Gs.');
  });

  it('shows EUR amount when provided', () => {
    const html = buildDonationReceiptEmail({
      donorName: 'Hans Müller',
      amountEur: 50.0,
      donationDate: '2026-03-25',
      donationId: 'uuid-5678',
    });

    expect(html).toContain('€50.00');
    expect(html).toContain('Euros');
  });
});

describe('buildShiftConfirmationEmail', () => {
  it('includes shift date, times, and role', () => {
    const html = buildShiftConfirmationEmail({
      volunteerName: 'Ana López',
      shiftDate: '2026-04-15',
      shiftStartTime: '08:00',
      shiftEndTime: '12:00',
      role: 'Cuidado de perros',
      location: 'Refugio Central',
      coordinatorName: 'Carlos Díaz',
      coordinatorPhone: '0981-123456',
    });

    expect(html).toContain('Ana López');
    expect(html).toContain('08:00');
    expect(html).toContain('12:00');
    expect(html).toContain('Cuidado de perros');
  });
});

describe('buildPasswordResetEmail', () => {
  it('includes reset URL and expiry notice', () => {
    const html = buildPasswordResetEmail({
      userName: 'Carlos',
      resetUrl: 'https://app.refugio.org/reset?token=abc123',
      expiresInMinutes: 60,
    });

    expect(html).toContain('https://app.refugio.org/reset?token=abc123');
    expect(html).toContain('60 minutos');
  });

  it('escapes the reset URL in the plain-text fallback', () => {
    const html = buildPasswordResetEmail({
      userName: 'Test',
      resetUrl: 'https://example.org/reset?a=1&b=2',
      expiresInMinutes: 60,
    });

    // URL in text should have & escaped to &amp;
    expect(html).toContain('a=1&amp;b=2');
  });
});
```

---

## Files to Create / Modify

| Path | Action | Notes |
|------|--------|-------|
| `src/lib/email/templates/_layout.ts` | Create | `emailLayout()` + `escapeHtml()` helpers |
| `src/lib/email/templates/adoption-approval.ts` | Create | Adoption approved template |
| `src/lib/email/templates/donation-receipt.ts` | Create | Donation receipt template |
| `src/lib/email/templates/volunteer-shift-confirmation.ts` | Create | Shift confirmed template |
| `src/lib/email/templates/password-reset.ts` | Create | Password reset template |
| `src/lib/email/templates/index.ts` | Create | Re-exports all four builders |
| `src/lib/email/templates/__tests__/email-templates.test.ts` | Create | 8 vitest unit tests |

---

## Definition of Done

- [ ] All 4 templates created with typed data interfaces
- [ ] `_layout.ts` shared helper prevents HTML/CSS duplication
- [ ] `escapeHtml()` applied to all user-supplied string interpolations
- [ ] `index.ts` re-exports all builders and types
- [ ] All 8 unit tests pass with `npm run test`
- [ ] No email sends inside template files — templates only build strings
- [ ] All UI text in Spanish
