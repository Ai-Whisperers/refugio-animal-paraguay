# Epics — Refugio Animal Paraguay

Project ID: `b9c81ffd-0904-4f58-8bc2-5b286462e46f`

> **Principio TDD**: Ningún feature se implementa sin un test fallando primero.
> Ver [TESTING-STRATEGY.md](TESTING-STRATEGY.md) para el stack completo y configuración.

---

## [EPIC-0] Testing Foundation & TDD Infrastructure
**ID:** `fa4226ef-ecbc-4bfa-b9aa-9bfac152ccdf` | **Prioridad:** 100

### Descripción
Setup completo del ecosistema de testing antes de escribir cualquier línea de feature code. Este epic es **prerequisito bloqueante** para todos los demás epics. Sin él, ningún otro epic puede comenzar.

### Funcionalidades clave

**Stack de testing:**
- Vitest 2.x configurado con cobertura V8 (thresholds: 80% lines, 75% branches)
- React Testing Library para componentes
- Playwright configurado para Chrome desktop + Pixel 7 (Android) + iPhone 14 (iOS)
- MSW (Mock Service Worker) para interceptar integraciones externas en tests
- @faker-js/faker para factories de datos realistas
- @axe-core/playwright para accessibility testing automatizado

**Infraestructura de datos de test:**
- Base de datos PostgreSQL aislada por suite de tests (transacciones con rollback)
- `.env.test` con todas las variables de entorno de testing
- Factories para todas las entidades principales:
  - `animal.factory.ts` — perros, gatos, urgentes, seniors
  - `user.factory.ts` — adoptante, admin, voluntario, donante europeo
  - `adoption.factory.ts` — solicitudes en cada estado del workflow
  - `donation.factory.ts` — donaciones locales (PYG) y europeas (EUR)
  - `lost-found.factory.ts` — reportes con coordenadas en Gran Asunción

**Mocks de integraciones externas:**
- WhatsApp Business API mock (no gastar cuota de mensajes en tests)
- Stripe mock (modo test keys + MSW handlers para webhooks)
- Tigo Money mock
- PayPal mock
- iDEAL / SEPA mock (para donaciones europeas)
- Cloudinary mock (no subir imágenes reales en tests)
- Google Maps mock

**CI/CD pipeline:**
- GitHub Actions con 4 jobs: unit+component → integration → E2E → Lighthouse CI
- Tests unitarios/componente: <30s, bloquean el PR si fallan
- Tests de integración: <3min con Postgres y Redis de test
- Tests E2E: <10min en CI con Playwright paralelo
- Lighthouse CI: score ≥75 Performance (4G throttled), ≥90 Accessibility, ≥90 SEO
- Coverage report publicado como artefacto en cada PR

**Configuración de scripts:**
```json
{
  "test": "vitest",
  "test:unit": "vitest run tests/unit tests/component",
  "test:integration": "vitest run tests/integration",
  "test:e2e": "playwright test",
  "test:coverage": "vitest run --coverage",
  "test:watch": "vitest --watch",
  "test:ci": "vitest run --coverage --reporter=junit && playwright test --reporter=github"
}
```

**Estructura de directorios:**
```
tests/
├── setup/          # vitest-setup.ts, db-setup.ts, test-env.ts
├── factories/      # Data factories para todas las entidades
├── mocks/          # MSW handlers para todas las integraciones
├── unit/           # Lógica pura: matching, scoring, validators, formatters
├── component/      # React components con RTL
├── integration/    # API routes + DB queries con datos reales
└── e2e/            # Flujos críticos completos en browser
```

**Checklist TDD por feature (integrado en DEFINITION-OF-DONE):**
- Test unitario escrito y fallando antes de implementar
- Código mínimo para pasar el test (green)
- Refactor sin romper tests
- Edge cases cubiertos (null, empty, invalid, network error)
- Si es flujo crítico (adopción, pago, admin) → E2E test obligatorio

### Gaps identificados y decisiones pendientes

| Gap | Decisión necesaria |
|-----|-------------------|
| ¿Usar Prisma test transactions o separate DB per suite? | Recomendado: transactions (más rápido) |
| ¿Load testing de endpoints de pago? | Artillery para checkout + donación |
| ¿Contract testing entre frontend y API? | Considerar MSW + Zod schema sharing |
| ¿Visual regression testing? | Playwright screenshots para componentes críticos |
| ¿Mutation testing? | Stryker opcional en Fase 3+ |

### Dependencias
- **Prerequisito de todos los epics** — debe completarse antes de comenzar cualquier feature
- EPIC-8 (infraestructura técnica — variables de entorno, DB, CI)

---

## [EPIC-1] Pet Catalog & Discovery
**ID:** `ec48c89f-6c0c-4c78-a81a-75f4a58e5221` | **Prioridad:** 90

### Descripción
Experiencia central de listado y búsqueda de animales. Todo visitante llega aquí primero.

### Funcionalidades clave
- Perfil individual por animal:
  - Galería de fotos (mínimo 3) + video opcional
  - Nombre, especie, raza, edad, sexo, tamaño, peso, color
  - Nivel de energía, temperamento, evaluación conductual
  - Estado de salud, vacunas, esterilización, microchip
  - Bueno con: niños / perros / gatos (flags)
  - Necesidades especiales (médicas o conductuales)
  - Tiempo en el refugio
- Búsqueda y filtros por todos los atributos
- Badges de estado: Disponible / En Foster / Pendiente / Adoptado / **Urgente** / Estadía Larga (+30 días)
- Botón WhatsApp "Compartir este animal" por perfil
- Galería Alumni: animales adoptados con foto en su nuevo hogar
- Schema.org/Animal markup para Google rich results
- Orden por: reciente / más tiempo en refugio / urgentes primero

### Testing obligatorio (EPIC-0)

- **Unit**: lógica de filtros (especie, tamaño, edad, compatibilidad), ordenamiento (urgentes primero, estadía larga), cálculo de "tiempo en refugio"
- **Component**: `AnimalCard` (badges, favorito, share), `CatalogFilters` (all filter combinations), `AnimalGallery` (lazy loading)
- **Integration**: `GET /api/animals` con todos los parámetros de filtro, paginación, sin datos, con datos
- **E2E**: `browse-and-filter.spec.ts` — usuario busca perro mediano en móvil y llega al perfil en <60 segundos
- **Accesibilidad**: schema.org markup presente en perfiles (verificar con axe)

### Dependencias
- EPIC-0 (testing infrastructure)
- EPIC-8 (infraestructura, imágenes optimizadas)
- EPIC-5 (admin crea y actualiza perfiles)

---

## [EPIC-2] Adoption Process & Application System
**ID:** `c7c5c91f-e0b2-4584-91a3-a16c37a20645` | **Prioridad:** 95

### Descripción
Embudo digital completo de adopción: desde la primera solicitud hasta el contrato firmado y el seguimiento post-adopción.

### Funcionalidades clave
- Formulario de solicitud multi-paso:
  - Datos personales + cédula + tipo de vivienda
  - Composición del hogar (adultos, niños, otras mascotas)
  - Experiencia con animales, historial de mascotas previas
  - Estilo de vida, horarios, viajes frecuentes
  - Referencias (veterinario anterior, vecino, empleador)
  - Entorno del hogar (jardín, si está cercado)
  - Declaración económica (puede costear atención veterinaria)
- Cuestionario de matching (3 min) → lista de animales compatibles ordenada
- Portal de estado de solicitud:
  - Estados: Recibida → En Revisión → Aprobada → Visita Acordada → Completada
  - Barra de progreso visual
  - Mensajería con el staff del refugio
- Workflow foster-to-adopt (track separado, línea de tiempo extendida)
- Contrato digital con firma digital:
  - Cláusula Ley 4840/2013: certificado de esterilización, declaración de jardín cercado
  - Prohibición de reventa/regalo del animal
  - Cláusula de devolución obligatoria al refugio
- Gestión de lista de espera: posición transparente ("Eres #2 de 4 solicitantes para Toby")
- Tarifas escalonadas:
  - Cachorros: Gs. 150,000–300,000
  - Adultos: Gs. 80,000–150,000
  - Seniors / necesidades especiales: gratuito
- Pagos: Tigo Money, Personal Pay, PagoExpress, transferencia bancaria, efectivo
- Formulario de devolución/rendición (el animal siempre vuelve al refugio)
- Seguimientos automáticos post-adopción:
  - Día 2, Día 7, Día 30, Día 90 (WhatsApp + email)

### Testing obligatorio (EPIC-0)

- **Unit**: algoritmo de matching adopciones (scoring por compatibilidad del hogar), validación de todos los campos del formulario (Zod schemas), cálculo de tarifas escalonadas
- **Component**: `AdoptionForm` multi-paso (guardar estado en localStorage, validación por step), `ApplicationStatus` progress bar, `ContractViewer`
- **Integration**: `POST /api/adoptions/applications` (crear, validar, rechazar duplicados), `PATCH /api/adoptions/[id]/status` (workflow de estados), `POST /api/adoptions/[id]/contract`
- **E2E OBLIGATORIO**: `complete-adoption-flow.spec.ts` — flujo completo de 5 pasos en móvil (390px), incluyendo verificación de datos guardados en localStorage y confirmación por WhatsApp
- **E2E OBLIGATORIO**: `application-status-tracking.spec.ts` — adoptante ve el estado actualizado sin recargar
- **Legal**: test que verifica que el contrato generado incluye las cláusulas requeridas por Ley 4840/2013

### Dependencias
- EPIC-0 (testing infrastructure)
- EPIC-1 (perfiles de animales)
- EPIC-6 (portal de usuario para tracking de solicitudes)
- EPIC-8 (infraestructura de notificaciones WhatsApp)

---

## [EPIC-3] Lost & Found / Stray Reporting
**ID:** `044c68ec-7af1-44c0-b35b-4b3d862ea67e` | **Prioridad:** 75

### Descripción
Herramienta pública para reportar y buscar animales perdidos y encontrados en Gran Asunción y alrededores.

### Funcionalidades clave
- Formulario "Perdí a mi mascota":
  - Datos del dueño (nombre, teléfono, WhatsApp)
  - Descripción del animal (especie, raza, color, sexo, edad, señas particulares)
  - Fotos del animal
  - Última ubicación vista (pin en mapa de Google Maps)
  - Fecha y hora
  - Número de microchip (si tiene)
- Formulario "Encontré un animal":
  - Datos del encontrador
  - Descripción del animal + fotos
  - Ubicación donde fue encontrado
  - Estado actual: lo tengo / lo dejé / lo entregué al refugio
- Mapa público de reportes activos en Gran Asunción
- Búsqueda/filtro: especie, zona, fecha, color, raza
- Motor de matching automático:
  - Nuevo reporte cruzado con reportes existentes y con ingresos al refugio
  - Si hay coincidencia → notificación WhatsApp a ambas partes
- Panel admin:
  - Vincular reporte con animal en el refugio
  - Marcar como resuelto
  - Contactar al reportante
- Integración con EPIC-5: ingresos de animales callejeros aparecen en el mapa
- Alto valor SEO para búsquedas de tipo "perro perdido Asunción"

### Testing obligatorio (EPIC-0)

- **Unit**: algoritmo de matching perdido/encontrado (especie + color + zona + fecha), normalización de texto de descripción para búsqueda fuzzy
- **Component**: `LostReportForm` con pin en mapa, `FoundReportForm`, `LostFoundMap` con marcadores
- **Integration**: `POST /api/lost-found/reports` (crear reporte), motor de matching automático (cruzar nuevo reporte con existentes), `PATCH /api/lost-found/[id]/resolve`
- **E2E**: `report-lost-pet.spec.ts` — usuario reporta perro perdido con foto y pin en mapa en <5 minutos
- **Idempotencia**: reportar el mismo animal dos veces no crea dos registros activos

### Dependencias
- EPIC-0 (testing infrastructure)
- EPIC-8 (mapas, notificaciones WhatsApp, PWA offline)
- EPIC-5 (ingresos de animales callejeros)

---

## [EPIC-4] Donation & Fundraising Platform
**ID:** `ebc94885-fee4-48d2-a233-21bdab3a78ae` | **Prioridad:** 80

### Descripción
Sistema de ingresos para sostener las operaciones del refugio con donaciones locales e internacionales.

### Funcionalidades clave

**Donaciones generales:**
- Donaciones únicas y recurrentes mensuales
- Programa "Apadrinar un animal": donante elige animal específico, recibe updates mensuales (foto + informe), progress bar en perfil del animal
- Páginas de campaña con objetivo y barra de progreso (cirugías urgentes, reparación de instalaciones, campañas estacionales)
- Desglose transparente del uso de fondos (% alimentación, vet, infraestructura)
- Lista de deseos de donaciones en especie (alimentos, insumos, medicamentos)
- Recibos digitales PDF automáticos (válidos fiscalmente)
- Historial de donaciones en portal del usuario (EPIC-6)

**Pasarelas locales — Paraguay:**
- Tigo Money (pasarela primaria, 60% penetración)
- Personal Pay (Claro/Personal)
- PagoExpress
- Transferencia bancaria: instrucciones con QR + número de cuenta Banco Nacional
- Efectivo en sede (registrado manualmente por admin)

**Pasarelas internacionales (Stripe):**
- Tarjetas de crédito/débito Visa, Mastercard, Amex (internacionales)
- Google Pay / Apple Pay (via Stripe)
- Stripe Link (checkout guardado)

**Pasarelas europeas — Canal prioritario (fundadora neerlandesa + red de apoyo europea):**
- **iDEAL** (método #1 en Países Bajos, procesado vía Stripe): selección de banco (ING, Rabobank, ABN AMRO, etc.)
- **SEPA Direct Debit** (débito automático de cuentas bancarias europeas — ideal para donaciones recurrentes)
- **SEPA Credit Transfer** (transferencia bancaria IBAN/BIC con instrucciones claras)
- **PayPal** (ampliamente usado en Europa, 200+ países)
- **Bancontact** (Bélgica, vía Stripe)
- **Sofort / Klarna** (Alemania, Austria, Países Bajos)
- **Tikkie** (pagos peer-to-peer en Países Bajos, link de pago compartible por WhatsApp/email)

**Plataformas de crowdfunding / fundraising:**
- **GoFundMe**: campañas específicas (cirugías, rescates de emergencia) — enlace externo con widget embebido
- **Donorbox** (ANBI-compatible, recurring donations, widget embebible en sitio)
- **Betterplace.org** (Alemania — plataforma de donaciones para ONGs)
- **Geef.nl** (Países Bajos — directorio de organizaciones benéficas)
- **GiveSendGo** (alternativa internacional)

**Programa ANBI (Países Bajos):**
- Página dedicada explicando el estatus ANBI y beneficios fiscales para donantes holandeses
- Formulario de donación con campos RSIN (Rechtspersonen en Samenwerkingsverbanden Informatienummer)
- Recibos compatibles con declaración fiscal holandesa (formato adecuado)
- Guía paso a paso: "¿Cómo deducir tu donación al refugio en tu declaración de impuestos en los Países Bajos?"

**Página de donación europea (/donar/europa o /donate):**
- Idioma: inglés (primary) + neerlandés opcional
- Moneda: EUR (Stripe) o local seleccionable
- Métodos de pago familiares para europeos
- Transparencia: "Your €25 feeds 5 animals for a month" (impact messaging)
- Trust signals: ANBI status, financial reports, animal sponsor updates

**Patrocinio corporativo:**
- Tiers: Amigo (€50/mes), Protector (€150/mes), Guardián (€500/mes), Padrino Fundador (€1,500/mes)
- Visibilidad: logo en sitio, mención en redes, certificado digital
- Contacto directo con fundadora para empresas neerlandesas/europeas

**Transparencia e impacto:**
- Contador en tiempo real: "X animales rescatados este mes"
- Informe anual de fondos (PDF descargable)
- Feed de updates: cómo se usaron las donaciones del mes
- Galería de animales rescatados gracias a donaciones específicas

### Testing obligatorio (EPIC-0)

- **Unit**: lógica de conversión de monedas (EUR ↔ PYG), cálculo de recibos, matching de donación con campaña
- **Integration**: webhooks de Stripe (payment_intent.succeeded, charge.refunded), webhook PayPal, Tigo Money callback
- **E2E obligatorios**:
  - `donate-tigo-money.spec.ts` — flujo completo local en móvil
  - `donate-stripe-card.spec.ts` — donación con tarjeta internacional
  - `donate-ideal-european.spec.ts` — flujo iDEAL con selección de banco holandés
  - `donate-paypal.spec.ts` — donación PayPal desde Europa
  - `campaign-progress.spec.ts` — donación a campaña específica actualiza barra en tiempo real
- **Idempotencia**: tests de que el mismo webhook de Stripe procesado 2 veces no crea 2 donaciones

### Dependencias
- EPIC-0 (testing infrastructure — los flujos de pago son los más críticos de probar)
- EPIC-6 (portal de donante)
- EPIC-8 (pasarelas de pago, seguridad, rate limiting en endpoints de pago)

---

## [EPIC-5] Shelter Operations & Admin Dashboard
**ID:** `cc128627-fecd-44a0-bb9f-1fd9a177a279` | **Prioridad:** 85

### Descripción
CMS interno para que el equipo del refugio gestione todo: animales, solicitudes, voluntarios, inventario y reportes.

### Funcionalidades clave
- Ficha de ingreso de animal:
  - Tipo: callejero, entregado por dueño, rescate, transferencia de otro refugio
  - Datos completos + fotos iniciales
  - Estado de salud al ingreso
- Historial médico por animal:
  - Visitas veterinarias, vacunas, tratamientos
  - Estado de esterilización + fecha
  - Registro de microchip
  - Prescripciones activas
- Gestión de ubicación física (jaula/kennel/área)
- Cola de revisión de solicitudes de adopción:
  - Ver todas las pendientes, asignar a consejero
  - Añadir notas internas, aprobar/rechazar con motivo
  - Historial de comunicaciones con el solicitante
- Gestión de voluntarios:
  - Roles: paseador, cuidador, fotógrafo, admin, coordinador foster
  - Horarios y asistencia
  - Horas registradas
- Gestión de familias foster:
  - Animales asignados
  - Check-ins semanales
  - Notas de comportamiento
- Inventario:
  - Stock de alimentos, medicamentos, insumos
  - Alertas de stock bajo
- Dashboard de reportes:
  - Ingresos vs. adopciones vs. devoluciones
  - Estadía promedio por especie/edad
  - Tasa de adopción, tasa de retorno
  - Capacidad actual vs. máxima
  - Totales de donaciones
- Gestión de Lost & Found (EPIC-3)
- Control de acceso por roles:
  - Admin (acceso total)
  - Veterinario (fichas médicas)
  - Voluntario (tareas asignadas)
  - Fotógrafo (subir fotos)
  - Coordinador foster (gestión de fosters)
- Notificaciones automáticas vía WhatsApp Business API

### Testing obligatorio (EPIC-0)

- **Unit**: lógica de control de acceso por rol (admin > coordinador > veterinario > voluntario > fotógrafo), cálculo de estadísticas de dashboard (tasa de adopción, estadía promedio), alertas de stock bajo
- **Component**: `ApplicationQueue` (acciones rápidas, color coding), `AnimalForm` (validación de campos médicos), `InventoryAlert`
- **Integration**: `PATCH /api/admin/applications/[id]/status` (verificar que solo admin/coordinador puede aprobar), `POST /api/admin/animals` (crear animal con fotos), audit log de acciones
- **E2E OBLIGATORIO**: `approve-adoption.spec.ts` — admin aprueba solicitud en <30 segundos en tablet (768px)
- **E2E OBLIGATORIO**: `role-based-access.spec.ts` — voluntario no puede aprobar adopciones (403 redirect)
- **Seguridad**: tests de que todos los endpoints de admin requieren autenticación y el rol correcto

### Dependencias
- EPIC-0 (testing infrastructure)
- EPIC-6 (autenticación de staff)
- EPIC-8 (WhatsApp Business API, infraestructura)

---

## [EPIC-6] User Accounts & Portal
**ID:** `ddbdec93-346c-45d7-b686-1660da064f60` | **Prioridad:** 70

### Descripción
Portal autenticado para todos los tipos de usuario público: adoptantes, voluntarios, donantes y familias foster.

### Funcionalidades clave
- Registro y login:
  - Email + contraseña
  - OTP por WhatsApp (preferido en Paraguay)
  - Recuperación por email o WhatsApp
- Portal adoptante:
  - Enviar y rastrear solicitudes (barra de progreso)
  - Animales guardados / favoritos
  - Historial de adopciones
  - Responder check-ins post-adopción
  - Subir documentos (CI, comprobante de domicilio)
- Portal voluntario:
  - Calendario de turnos disponibles
  - Registro de disponibilidad
  - Materiales de capacitación
  - Registro de horas
- Portal donante:
  - Historial de donaciones
  - Gestión de donaciones recurrentes (pausar, cancelar)
  - Descargar recibos digitales
  - Ver updates del animal apadrinado
- Portal familia foster:
  - Animal asignado actualmente
  - Formularios de check-in semanal
  - Diario de comportamiento
  - Informes médicos
  - Comunicación directa con coordinador
- Cumplimiento Ley 7593/2025:
  - Eliminar cuenta y todos los datos en <24 horas
  - Exportar datos personales (JSON/PDF)
  - Gestión de consentimientos (qué datos acepta compartir)
- Admin: gestión de todos los usuarios, roles, suspensiones

### Testing obligatorio (EPIC-0)

- **Unit**: flujo de eliminación de cuenta (anonimización de datos, Ley 7593), exportación de datos personales (todos los campos requeridos presentes), validación de OTP WhatsApp (expiración, intentos máximos)
- **Component**: `ConsentManager` (marcar/desmarcar categorías, mostrar fecha de consentimiento), `AccountDeletionFlow` (confirmación, countdown)
- **Integration**: `POST /api/auth/whatsapp-otp` (enviar, verificar, expirar), `POST /api/users/[id]/delete` (anonimizar en <24h, no eliminar registros fiscales), `GET /api/users/[id]/export` (ZIP con todos los datos)
- **E2E**: `login-whatsapp-otp.spec.ts` — usuario se loguea con OTP de WhatsApp, `register-user.spec.ts` — registro con consentimientos explícitos
- **Legal**: test que verifica que el export incluye todos los datos requeridos por Ley 7593/2025, test de que los registros de donaciones anonimizados se retienen 5 años

### Dependencias
- EPIC-0 (testing infrastructure)
- EPIC-8 (autenticación segura, WhatsApp OTP)
- EPIC-2, 4, 5 (los portales consumen datos de estos epics)

---

## [EPIC-7] Community, Education & Outreach
**ID:** `d4254af9-5e1a-4635-bf02-45ea96a1153b` | **Prioridad:** 65

### Descripción
Hub de contenido y comunidad para construir confianza, generar tráfico orgánico y educar a la población.

### Funcionalidades clave

**Páginas estáticas (obligatorias):**
- Inicio (homepage con CTA a adoptar, donar, reportar perdido)
- Sobre Nosotros: misión, equipo, historia del refugio
- Cómo Adoptar: guía paso a paso
- Cómo Donar: opciones de donación explicadas
- Contacto: formulario, dirección, teléfono, WhatsApp
- Ubicación y horarios (mapa embebido)
- Voluntariado: cómo unirse
- Política de Privacidad, Términos, Cookies
- Socios y aliados

**Blog y contenido editorial:**
- Noticias del refugio
- Artículos educativos: tenencia responsable, Ley 4840, señales de maltrato
- Guías prácticas: "Cómo preparar tu hogar para un perro", "Costo real de tener una mascota en Paraguay"
- Contenido en español paraguayo, secciones en guaraní para alcance rural

**Galería de éxitos:**
- Fotos "antes y después" de animales adoptados
- Actualizaciones enviadas por las familias
- Testimonios de adoptantes

**Eventos:**
- Calendario: ferias de adopción, campañas de vacunación, eventos de fundraising
- Registro de asistentes online
- Recordatorios vía WhatsApp

**Social y comunicación:**
- Feed de Facebook e Instagram embebido
- Botón flotante WhatsApp Business en todas las páginas
- Newsletter: lista de difusión WhatsApp + email (Mailchimp / similar)

**Recursos para la comunidad:**
- Mapa de veterinarias aliadas en Gran Asunción
- Directorio de tiendas de insumos para mascotas
- Línea de emergencia para maltrato animal

### Testing obligatorio (EPIC-0)

- **Component**: renderizado correcto de mensajes i18n en es-PY y guaraní, `BlogCard` SEO, `EventCalendar`
- **Integration**: generación de sitemap con todos los perfiles de animales activos, Open Graph tags por tipo de página
- **E2E**: `wcag-aa-critical-pages.spec.ts` — todas las páginas públicas sin violaciones WCAG AA (axe-core)
- **Performance**: Lighthouse CI score ≥75 Performance en homepage, /adoptar, /donar (4G throttled)

### Dependencias
- EPIC-0 (testing infrastructure)
- EPIC-8 (CMS, SEO, multiidioma)

---

## [EPIC-8] Technical Foundation & Compliance
**ID:** `d175c007-4b2a-4274-b9cc-695f94f40112` | **Prioridad:** 60

### Descripción
Infraestructura, performance, seguridad y cumplimiento legal. Habilita todos los demás epics.

### Funcionalidades clave

**Performance (Paraguay = 90% móvil, 3G/4G):**
- PWA (Progressive Web App) con soporte offline
- Core Web Vitals en 4G: LCP <2.5s, INP <200ms, CLS <0.1
- Imágenes: pipeline WebP/AVIF + lazy loading + CDN
- Code splitting agresivo, prefetch inteligente

**SEO:**
- Meta tags en español (es-PY)
- Schema.org markup (Animal, Organization, Event)
- Sitemap.xml automático
- Google My Business integration
- Open Graph para Facebook/WhatsApp previews

**Legal — Ley 7593/2025 (datos personales, vigente marzo 2027):**
- Banner de cookies con "Rechazar todo" funcional
- Política de privacidad detallada
- Derecho al olvido: eliminación de cuenta en <24h
- Exportación de datos personales
- Registro de consentimientos con timestamp
- DPA (Data Protection Agreement) con proveedores externos

**Legal — Ley 4840/2013 (bienestar animal):**
- Contrato de adopción digital con cláusulas obligatorias
- Registro de esterilización pre-adopción
- Declaración jurada de jardín cercado

**Seguridad:**
- HTTPS con SSL A+ (Let's Encrypt / Cloudflare)
- Rate limiting en formularios públicos
- Anti-spam en solicitudes de adopción
- Autenticación segura (bcrypt, JWT, refresh tokens)
- Sanitización de inputs, protección XSS/CSRF/SQLi

**Integraciones (ver [INTEGRATIONS.md](INTEGRATIONS.md)):**
- WhatsApp Business API (notificaciones automáticas)
- Tigo Money, Personal Pay, PagoExpress
- Stripe (tarjetas internacionales)
- Google Analytics 4 + Facebook Pixel
- Google Maps (Lost & Found, mapa de vets)
- Cloudinary o similar (gestión de imágenes)

**Internacionalización:**
- es-PY (español paraguayo) — primario
- gn (guaraní) — secciones clave

**Infraestructura:**
- CI/CD: GitHub Actions con deploy a staging y producción
- Backups automáticos diarios (30 días de retención)
- Monitoreo de uptime y alertas
- Staging environment para QA antes de producción

### Testing obligatorio (EPIC-0)

- **Unit**: rate limiting logic (ventana de tiempo, contador por IP/usuario), sanitización de inputs (XSS, SQLi edge cases), generación de tokens JWT
- **Integration**: `POST /api/webhooks/whatsapp` (verificar firma HMAC, idempotencia), pipeline de imágenes Cloudinary (WebP output, tamaño correcto), cookie banner (rechazar analytics no carga GA4)
- **E2E**: comportamiento offline (catálogo disponible sin conexión vía Service Worker), Core Web Vitals medidos con Lighthouse en páginas críticas
- **Security**: test que API routes de admin sin token retornan 401, test que rate limiting bloquea después de N requests

### Dependencias
- EPIC-0 (testing infrastructure — este epic es co-dependiente)
- Es prerequisito para todos los demás epics

---

## [EPIC-9] Visual Assets & Brand Image Library
**ID:** `34036918-b794-4bf9-9932-998636fec98f` | **Prioridad:** 55

### Descripción
Producción completa de todos los assets visuales del sitio web: desde la identidad de marca hasta imágenes de ejemplo de animales, banners de campaña, ilustraciones UI, y guía de fotografía para el equipo del refugio.

### Identidad de marca

**Logo y variantes:**
- Logo principal horizontal (color, blanco, negro)
- Logo símbolo/ícono solo (para favicon, app icon, WhatsApp Business)
- Versiones en SVG + PNG (1x, 2x, 3x)
- Favicon `.ico` + `apple-touch-icon.png` + `manifest` icons (192px, 512px)
- Marca de agua para fotos de animales (opcional, sutil)
- Variante en guaraní/bilingüe para materiales de comunidad

**Paleta aplicada:**
- Naranja primario `#E8622A`, Verde `#2A7E62`, Blanco cálido `#FAFAF8`
- Imágenes de marca deben usar la paleta — no colores genéricos

### Imágenes de la interfaz

**Hero & Secciones clave:**
| Imagen | Dimensiones | Uso | Formato |
|--------|------------|-----|---------|
| Hero homepage — animales felices en refugio | 1440×800 + 390×600 (mobile) | Fondo principal | WebP |
| Hero donaciones — animal siendo cuidado | 1440×800 + 390×600 | Página /donar | WebP |
| Hero adopción — familia con mascota | 1440×800 + 390×600 | /como-adoptar | WebP |
| Hero Lost & Found — animal en calle | 1440×800 | /perdidos-encontrados | WebP |
| Hero Europa — donor page en inglés | 1440×800 + 390×600 | /donate (EU) | WebP |
| Foto equipo del refugio (real) | 1200×800 | /nosotros | WebP |
| Foto instalaciones del refugio (real) | Múltiples | /nosotros | WebP |

**Imágenes de placeholder (antes de tener animales reales):**
- 10-15 fotos de perros con nombres ficticios (Luna, Tobby, Max, etc.)
- 5-8 fotos de gatos con nombres ficticios
- 2-3 fotos de animales "urgentes" con badge overlay
- 2-3 fotos de animales seniors ("adopción especial")
- Formato: 4:3 para catálogo, 1:1 para Open Graph/WhatsApp
- Estilo: fondo neutro, animal bien encuadrado, mirada a cámara (guidelines en sección Fotografía)

**Ilustraciones UI:**
- Estado vacío catálogo: "Todos los animales encontraron hogar 🎉" (ilustración cálida)
- Estado vacío favoritos: "Aún no guardaste ningún animal" (ilustración con corazón)
- Estado vacío solicitudes: "No tenés solicitudes activas"
- Error 404: animal confundido buscando su hogar
- Error 500: animal durmiendo "Volveremos en un momento"
- Loading skeleton: subtle pattern con colores de marca
- Éxito de solicitud: animal feliz "¡Tu solicitud llegó!"
- Confirmación de donación: corazón con patas de animal
- Email/WhatsApp confirmation illustration

**Íconos específicos del dominio:**
- Especie: perro, gato, conejo, ave, otro (SVG icon set)
- Atributos: bueno con niños, bueno con perros, bueno con gatos, necesidades especiales
- Tamaño: pequeño, mediano, grande, gigante (peso/talla)
- Estado: disponible, urgente, en foster, pendiente, adoptado, estadía larga
- Íconos de métodos de pago: Tigo Money, Personal Pay, iDEAL, PayPal, Stripe, SEPA

### Open Graph & Social Media

**Imágenes Open Graph (1200×630):**
- Homepage OG (logo + foto refugio + tagline)
- Página de donaciones OG (impacto visual)
- Página Lost & Found OG
- Template dinámico para perfiles de animales (nombre + foto + especie)
- Página europea de donaciones OG (en inglés)

**Imágenes cuadradas 1200×1200 (WhatsApp-optimized):**
- Template para compartir perfil de animal por WhatsApp
- Template de campaña de emergencia (rojo/urgente)
- Template de "Animal adoptado" para compartir en redes

**Instagram/Facebook posts:**
- Template de nuevo ingreso (animal recibido en el refugio)
- Template de historia de éxito (antes + después)
- Template de campaña de fundraising
- Template de animal urgente
- Formato: 1080×1080 (feed) + 1080×1920 (stories)

### Imágenes para Email & WhatsApp

**Templates de email (Resend):**
- Header email con logo (600px ancho)
- Footer email con redes sociales e íconos
- Banner "Bienvenido al refugio" (onboarding)
- Banner "Tu solicitud fue aprobada"
- Banner "Donación recibida — gracias"
- Banner para donantes europeos (en inglés)

**WhatsApp Business:**
- Foto de perfil de la cuenta (400×400)
- Cover image del catálogo de productos/servicios
- Imágenes adjuntas para templates de notificación (check-in día 7, etc.)

### Fotografía — Guía para el Refugio

**Especificaciones técnicas:**
- Cámara: smartphone en modo retrato o modo foto (no video)
- Resolución mínima: 12MP (la mayoría de smartphones modernos)
- Formato de entrega: JPEG o HEIC (se convierte a WebP automáticamente)

**Composición para fotos de animales:**
```
✅ Fondo limpio (pasto verde, pared blanca/beige, o área interior limpia)
✅ Animal centrado y bien encuadrado (no cortarle patas o cabeza)
✅ Mirada hacia la cámara o lateral — NO trasero
✅ Luz natural, sin flash directo (luz de costado es ideal)
✅ Al menos 3 fotos por animal: frente, perfil, plano general
✅ Una foto mostrando escala (junto a objeto conocido o persona)

❌ Fondo de jaula visible
❌ Foto borrosa o movida
❌ Animal asustado o bajo stress visible
❌ Contraluz (animal oscuro, fondo brillante)
❌ Flash directo (ojos rojos, sombras duras)
```

**Mínimo de fotos por animal para publicar:**
- 3 fotos requeridas (frente, perfil, plano general)
- 5-8 fotos recomendadas
- 1 video corto (15-30s) opcional pero altamente recomendado

**Fotos del refugio (para /nosotros y trust-building):**
- Instalaciones limpias y ordenadas
- Equipo con animales (sonrisas genuinas)
- Proceso de cuidado (baño, alimentación, paseo)
- Visita de adoptantes
- Eventos de adopción

### Formatos y optimización

```
Todos los assets de producción se procesan por Cloudinary:
- Conversión automática a WebP (con fallback JPEG para Safari antiguo)
- Tamaños responsive: 400w, 800w, 1200w, 1600w
- Lazy loading nativo + BlurHash placeholder
- Compresión: calidad 80 para fotos, 90 para UI assets
- CDN: global edge delivery

Nombrado de archivos:
- Logo: logo-horizontal.svg, logo-icon.svg, favicon.ico
- Placeholders: placeholder-dog-luna.jpg, placeholder-cat-michi.jpg
- Ilustraciones: empty-catalog.svg, error-404.svg, success-donation.svg
- OG images: og-homepage.jpg, og-donate.jpg, og-animal-template.jpg
```

### Herramientas de producción

| Asset | Herramienta sugerida | Responsable |
|-------|---------------------|-------------|
| Logo + íconos SVG | Figma, Illustrator, o Canva Pro | Diseñador/a |
| Ilustraciones UI | undraw.co (free) + customizar colores de marca | Dev o diseñador |
| Fotos de placeholder | Unsplash (licencia gratuita) + validar uso comercial | Dev |
| OG templates dinámicos | `@vercel/og` (Next.js edge function) | Dev |
| Social media templates | Canva Pro con brand kit | Marketing/fundadora |
| Íconos especie/estado | Lucide Icons (ya incluido con shadcn/ui) + SVG custom | Dev |

### Íconos de pago (para EPIC-4)

SVGs oficiales de:
- Stripe (disponible en kit oficial)
- PayPal (brand assets)
- Tigo Money (pedir a Tigo Paraguay)
- Personal Pay (pedir a Personal/Claro Paraguay)
- iDEAL (Currence — disponible en kit de prensa)
- SEPA (logo oficial BCE)
- Visa / Mastercard / Amex (brand guidelines)

### Priorización por fase

**Fase 1 — MVP (obligatorio antes del lanzamiento):**
- [ ] Logo + favicon + app icons
- [ ] 5 fotos placeholder de animales (perros/gatos)
- [ ] Íconos de especie y estado (SVG)
- [ ] Imagen OG homepage
- [ ] Ilustraciones de estado vacío y error 404
- [ ] Header/footer de email
- [ ] Foto de perfil WhatsApp Business

**Fase 2:**
- [ ] 10-15 fotos placeholder adicionales
- [ ] Imágenes hero de todas las páginas principales
- [ ] Templates OG dinámicos (via @vercel/og)
- [ ] Íconos de métodos de pago

**Fase 3:**
- [ ] Templates de Instagram/Facebook
- [ ] Guía de fotografía impresa para el refugio
- [ ] Templates de WhatsApp con imágenes
- [ ] Imágenes hero de página europea (/donate)

**Fase 4+:**
- [ ] Fotos reales del refugio (una vez operativo en Paraguay)
- [ ] Reemplazar todos los placeholders con animales reales
- [ ] Video institucional corto (30-60s)

### Gaps identificados

| Gap | Decisión necesaria |
|-----|-------------------|
| ¿Contratar diseñador local en Paraguay? | Recomendado para logo y brand identity — costo estimado USD 500-1,500 |
| ¿Usar @vercel/og para OG dinámico? | Sí — genera imágenes de animales con nombre y foto en el servidor |
| ¿Watermark en fotos de animales? | Protege contra re-uso, pero puede reducir calidad percibida |
| ¿Video de presentación del refugio? | Alta prioridad para la página europea de donaciones |
| Íconos de Tigo Money / Personal Pay | Pedir kits de prensa oficiales o crear SVG equivalentes |

### Dependencias
- EPIC-7 (blog y contenido editorial usan estos assets)
- EPIC-4 (íconos de pago para página de donaciones)
- EPIC-8 (pipeline de Cloudinary para optimización)
