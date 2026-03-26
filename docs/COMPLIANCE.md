# Cumplimiento Legal — Refugio Animal Paraguay

---

## Ley 4840/2013 — Protección y Bienestar Animal

**Promulgada:** 2013 | **Estado:** Vigente

### Requisitos que afectan el sistema de adopción

#### 1. Esterilización previa a adopción

**Requisito legal:** Todo animal adoptado de un refugio debe estar esterilizado antes de la entrega o el adoptante debe comprometerse a esterilizarlo dentro de los 30 días.

**Implementación:**

```typescript
// En AdoptionApplication
sterilized: boolean  // Campo del animal
sterilizationCertUrl?: string  // Adjunto al contrato

// En AdoptionContract
sterilizationCertUrl: string  // Obligatorio si el animal ya está esterilizado
sterilizationDeadline?: Date  // Si el animal aún no está esterilizado (fecha compromiso)
```

**Checklist de aceptación para EPIC-2:**
- [ ] Contrato incluye estado de esterilización del animal
- [ ] Si no esterilizado: campo de fecha compromiso obligatorio en contrato
- [ ] Certificado de esterilización cargable en PDF/foto
- [ ] Seguimiento del día 30 pregunta explícitamente sobre esterilización si aplica

#### 2. Jardín cercado (para perros)

**Requisito legal:** Para adopción de perros, el adoptante con jardín debe declarar que está cercado para prevenir escape y accidentes.

**Implementación:**

```typescript
// En formulario de adopción (step de vivienda)
hasFencedGarden: boolean  // Required si housingType === 'CASA'
declaresGardenFenced: boolean  // Declaración jurada en contrato
```

**Texto a mostrar en formulario:**
> "Declaro que mi propiedad cuenta con jardín cercado de manera segura, en cumplimiento de la Ley 4840/2013 de Bienestar Animal de la República del Paraguay."

#### 3. Prohibición de reventa y regalo

**Requisito legal:** El adoptante no puede vender, regalar ni transferir el animal a terceros. En caso de no poder conservarlo, debe devolverlo al refugio de origen.

**Implementación en contrato:**

```markdown
CLÁUSULA 3 — DEVOLUCIÓN OBLIGATORIA
El adoptante se compromete, de acuerdo con la Ley 4840/2013, a no vender, regalar
ni ceder el animal adoptado a ningún tercero bajo ninguna circunstancia.
En caso de no poder seguir haciéndose cargo del animal por cualquier motivo,
deberá contactar al Refugio Animal Paraguay para coordinar su devolución.
El incumplimiento de esta cláusula puede derivar en acciones legales.
```

#### 4. Seguimiento post-adopción

**Recomendación de la ley:** Las organizaciones de rescate deben hacer seguimiento del bienestar del animal adoptado.

**Implementación:**
- Seguimientos automáticos en día 2, 7, 30, 90 por WhatsApp
- Formularios de check-in con preguntas de bienestar

---

## Ley 7593/2025 — Protección de Datos Personales

**Promulgada:** 2025 | **Período de adecuación:** Hasta marzo 2027 | **Vigencia plena:** Marzo 2027

### Principios base

| Principio | Descripción | Implementación |
|-----------|-------------|----------------|
| **Licitud** | Solo recolectar datos con base legal válida | Consentimiento explícito en registro |
| **Finalidad** | Datos solo para el propósito declarado | DPA con cada proveedor externo |
| **Minimización** | Solo los datos estrictamente necesarios | Auditar cada campo del formulario |
| **Exactitud** | Datos actualizados y correctos | Portal para que usuarios editen sus datos |
| **Limitación del plazo** | No guardar datos más tiempo del necesario | Política de retención definida |
| **Integridad y confidencialidad** | Seguridad técnica adecuada | HTTPS, bcrypt, auditoría de accesos |
| **Responsabilidad proactiva** | Demostrar cumplimiento | Registro de consentimientos con timestamp |

### Derechos del titular de datos

#### Derecho al olvido (eliminación de cuenta)

**Requisito:** El usuario puede solicitar la eliminación total de sus datos en el plazo de 24 horas.

**Implementación:**

```typescript
// src/app/api/users/[id]/delete/route.ts
export async function POST(req: Request, { params }: { params: { id: string } }) {
  // 1. Verificar identidad del solicitante (debe ser el usuario mismo o admin)
  // 2. Anonymizar datos en lugar de borrar donde hay restricciones legales
  //    (registros de donaciones deben mantenerse por obligaciones fiscales)
  // 3. Eliminar: fotos, datos personales, historial de sesiones
  // 4. Enviar confirmación de eliminación

  await db.user.update({
    where: { id: params.id },
    data: {
      name: '[ELIMINADO]',
      email: null,
      phone: null,
      ci: null,
      status: 'DELETED',
      deletedAt: new Date(),
      // Mantener ID para referencias en registros históricos anonimizados
    }
  })

  // Programar eliminación de fotos en Cloudinary (inmediata o <24h)
  await scheduleCloudinaryCleanup(params.id)

  return Response.json({ success: true })
}
```

**Plazo:** <24 horas desde la solicitud
**Excepciones:** Registros de donaciones (retención por obligaciones fiscales de 5 años, anonimizados)

#### Portabilidad de datos

**Requisito:** El usuario puede exportar todos sus datos en formato legible (JSON/PDF).

**Campos a exportar:**
- Perfil personal (nombre, email, teléfono, CI)
- Historial de solicitudes de adopción
- Historial de donaciones
- Animales guardados
- Fecha de registro y último acceso
- Historial de consentimientos

```typescript
// src/app/api/users/[id]/export/route.ts
// Generar ZIP con: datos.json + recibos-donaciones.pdf
// Entregar link de descarga válido por 1 hora
```

#### Gestión de consentimientos

```typescript
model ConsentRecord {
  id          String   @id @default(cuid())
  userId      String
  type        ConsentType // TERMS | PRIVACY | MARKETING_EMAIL | MARKETING_WA | ANALYTICS
  granted     Boolean
  ipAddress   String
  userAgent   String
  timestamp   DateTime @default(now())
}
```

**Importante:** Cada vez que el usuario actualiza sus preferencias de consentimiento, se registra un nuevo entry (nunca se sobrescribe el histórico).

### Banner de Cookies

**Requisito:** Cookie banner con opción "Rechazar todo" funcional — no solo decorativa.

**Categorías:**
| Categoría | Necesario | Puede rechazar |
|-----------|-----------|----------------|
| Esenciales (auth, carrito) | Sí | No |
| Analytics (GA4) | No | Sí |
| Marketing (FB Pixel) | No | Sí |
| Preferencias (idioma, filtros) | No | Sí |

**Comportamiento si rechaza analytics:**
```typescript
// No cargar GA4 si no hay consentimiento
const hasAnalyticsConsent = useConsent('analytics')
if (hasAnalyticsConsent) {
  // Cargar GA4
}
```

**Librerías recomendadas:** `@cookie-consent/react` o implementación propia (no usar soluciones que ignoren "Rechazar todo").

### Data Protection Agreements (DPA)

Proveedores que reciben datos personales de usuarios del sitio:

| Proveedor | Datos compartidos | DPA requerido |
|-----------|------------------|---------------|
| **Meta (WhatsApp)** | Número de teléfono | ✅ |
| **Google (Analytics)** | IP, comportamiento | ✅ (Google DPA estándar) |
| **Cloudinary** | Fotos de usuarios y animales | ✅ |
| **Resend** | Email, nombre | ✅ |
| **Stripe** | Datos de pago, email | ✅ (PCI DSS + DPA) |
| **Supabase/Railway** | Todos los datos | ✅ |
| **Vercel** | IP, logs | ✅ |

### Política de Retención de Datos

| Tipo de dato | Retención | Justificación |
|-------------|-----------|---------------|
| Datos de usuario activo | Mientras esté activo | Necesario para el servicio |
| Datos post-eliminación de cuenta | 0 días (eliminación inmediata) | Derecho al olvido |
| Registros de donaciones (anonimizados) | 5 años | Obligación fiscal |
| Logs de acceso | 90 días | Seguridad/auditoría |
| Consentimientos | Indefinido (registro de cumplimiento) | Demostrar cumplimiento legal |
| Contratos de adopción | 5 años | Obligación legal |

---

## Checklist de Implementación

### Fase 1 — MVP (Obligatorio desde el inicio)

- [ ] HTTPS configurado (SSL A+)
- [ ] Política de privacidad publicada (en español, lenguaje claro)
- [ ] Términos y condiciones publicados
- [ ] Cookie banner con "Rechazar todo" funcional
- [ ] Consentimiento explícito en formulario de registro
- [ ] Registro de consentimiento con timestamp en BD
- [ ] Contrato de adopción digital con cláusulas Ley 4840

### Fase 2

- [ ] Portal de usuario con exportación de datos (JSON)
- [ ] Flujo de eliminación de cuenta (<24h)
- [ ] Gestión de preferencias de comunicación (WhatsApp, email)

### Fase 4

- [ ] Auditoría completa de cumplimiento Ley 7593
- [ ] DPA firmados con todos los proveedores
- [ ] Proceso de notificación de brechas documentado
- [ ] Registro de actividades de tratamiento (RAT)

---

## Disclaimer

Este documento no constituye asesoramiento legal. Para asegurar el cumplimiento completo, consultar con un abogado especializado en derecho digital paraguayo antes del lanzamiento público.
