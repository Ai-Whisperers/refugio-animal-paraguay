# Objetivos del Proyecto — Refugio Animal Paraguay

## Objetivo General

Digitalizar completamente las operaciones del refugio y la experiencia de adopción, reduciendo el tiempo de trabajo manual del staff en un 60% y aumentando las adopciones exitosas (no devueltas) en un 30% dentro de los primeros 12 meses de operación.

---

## Objetivos SMART por Área

### 1. Adopciones

| Objetivo | Métrica | Línea base | Meta 6 meses | Meta 12 meses |
|----------|---------|-----------|--------------|----------------|
| Aumentar adopciones | Adopciones completadas/mes | — | +20% | +40% |
| Reducir devoluciones | % retorno en 90 días | ~15% (estimado) | <10% | <8% |
| Mejorar matching | % adopciones sin devolución a 1 año | — | >85% | >90% |
| Reducir tiempo de proceso | Días desde solicitud hasta adopción | 14 días (estimado) | 7 días | 5 días |
| Seguimiento post-adopción | % check-ins completados (día 2, 7, 30) | 0% (manual) | 70% | 90% |

### 2. Animales

| Objetivo | Métrica | Línea base | Meta 6 meses | Meta 12 meses |
|----------|---------|-----------|--------------|----------------|
| Reducir estadía promedio | Días promedio en refugio | — | -20% | -30% |
| Registros completos | % animales con ficha digital completa | ~0% | 80% | 100% |
| Esterilización | % esterilizados antes de adopción | — | 100% | 100% |
| Microchipping | % microchipeados y registrados | — | 90% | 100% |

### 3. Donaciones y Financiamiento

| Objetivo | Métrica | Línea base | Meta 6 meses | Meta 12 meses |
|----------|---------|-----------|--------------|----------------|
| Donantes recurrentes | Número de donantes mensuales activos | 0 | 25 | 75 |
| Ingresos por donación | Gs./mes | — | Gs. 5M | Gs. 15M |
| Animales patrocinados | % de animales con un patrocinador | 0% | 30% | 60% |
| Campañas de emergencia | % del objetivo alcanzado por campaña | — | 70% | 85% |

### 4. Communidad y Alcance

| Objetivo | Métrica | Línea base | Meta 6 meses | Meta 12 meses |
|----------|---------|-----------|--------------|----------------|
| Tráfico web | Visitantes únicos/mes | 0 | 2,000 | 8,000 |
| Lost & Found | % reportes resueltos | — | 35% | 45% |
| Voluntarios activos | Número de voluntarios registrados y activos | — | 20 | 50 |
| Alumni wall | Familias con updates post-adopción | 0% | 40% | 65% |

### 5. Operaciones del Refugio

| Objetivo | Métrica | Línea base | Meta 3 meses | Meta 6 meses |
|----------|---------|-----------|--------------|---------------|
| Reducir trabajo manual | Horas staff/semana en admin | — | -40% | -60% |
| Registros médicos | % animales con historial digital | 0% | 70% | 100% |
| Inventario | % accuracy en inventario de insumos | — | 90% | 95% |
| Tiempo de respuesta a solicitudes | Horas para primer contacto con solicitante | >48h | <24h | <4h |

---

## Criterios de Éxito por Epic

### EPIC-1: Pet Catalog & Discovery
- [ ] Todos los animales del refugio tienen perfil digital completo (foto, datos, estado)
- [ ] Filtros funcionan correctamente en móvil 4G (carga <2.5s)
- [ ] Schema.org markup indexado por Google
- [ ] WhatsApp share genera preview correcto con foto y nombre

### EPIC-2: Adoption Process & Application System
- [ ] Formulario de solicitud completable en móvil sin fricciones
- [ ] Applicant recibe confirmación automática en <1 minuto
- [ ] 100% de solicitudes tienen seguimiento documentado
- [ ] Matching questionnaire reduce devoluciones (validar con datos a 6 meses)
- [ ] Contrato digital cumple Ley 4840 (certificado esterilización + jardín cercado)

### EPIC-3: Lost & Found
- [ ] Formulario de reporte funciona offline (PWA)
- [ ] Mapa de reportes carga en <3s en 4G
- [ ] Algoritmo de matching cruza con fichas del refugio automáticamente
- [ ] Notificación WhatsApp enviada en <5 minutos al detectar coincidencia

### EPIC-4: Donation & Fundraising
- [ ] Pago por Tigo Money completa en <3 pasos desde móvil
- [ ] Donaciones recurrentes procesadas automáticamente cada mes
- [ ] Recibo digital generado y enviado en <1 minuto

### EPIC-5: Admin Dashboard
- [ ] Intake de animal completo en <5 minutos
- [ ] Dashboard de reportes actualizado en tiempo real
- [ ] Roles correctamente aislados (vet no puede modificar solicitudes, etc.)

### EPIC-6: User Accounts & Portal
- [ ] Login con WhatsApp OTP funciona en <30 segundos
- [ ] Exportación de datos y eliminación de cuenta en <24 horas (Ley 7593)
- [ ] Portal funciona offline para lectura (PWA)

### EPIC-7: Community & Outreach
- [ ] Blog indexado en Google para búsquedas de adopción en Paraguay
- [ ] Todas las páginas estáticas tienen contenido en español y secciones clave en guaraní
- [ ] Formulario de contacto entrega a WhatsApp Business y email

### EPIC-8: Technical Foundation
- [ ] LCP <2.5s, INP <200ms, CLS <0.1 en 4G (validado con Lighthouse)
- [ ] Cookie banner con "Rechazar todo" funcional (Ley 7593)
- [ ] Backups automáticos diarios con retention de 30 días
- [ ] SSL A+ rating (SSL Labs)

---

## Priorización

```
MUST HAVE (MVP):     EPIC-2 (adopciones), EPIC-1 (catálogo), EPIC-8 (fundación técnica)
SHOULD HAVE:         EPIC-5 (admin), EPIC-6 (portal usuarios)
COULD HAVE:          EPIC-3 (lost & found), EPIC-4 (donaciones)
NICE TO HAVE (v2):   EPIC-7 (comunidad completa)
```
