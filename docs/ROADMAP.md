# Roadmap de Desarrollo — Refugio Animal Paraguay

## Estrategia de Fases

El desarrollo sigue una estrategia de valor mínimo viable primero: lanzar con las funcionalidades que generan el mayor impacto inmediato (adopciones + catálogo), luego iterar hacia la plataforma completa.

---

## Fase 0 — Configuración y Diseño (Semanas 1–3)

**Objetivo:** Decisiones técnicas tomadas, diseño del sistema aprobado, entorno de desarrollo listo.

### Deliverables
- [ ] Stack tecnológico final aprobado (ver [TECH-STACK.md](TECH-STACK.md))
- [ ] Wireframes de páginas principales (homepage, catálogo, perfil animal, formulario solicitud)
- [ ] Sistema de diseño: paleta de colores, tipografía, componentes base
- [ ] Repositorio creado con CI/CD básico (GitHub Actions)
- [ ] Base de datos diseñada y migración inicial (ver [DATA-MODEL.md](DATA-MODEL.md))
- [ ] Entorno de desarrollo local documentado
- [ ] Dominio y hosting contratados
- [ ] WhatsApp Business API solicitud enviada

### Epics involucrados
- EPIC-8 (fundación técnica)

---

## Fase 1 — MVP: Catálogo + Adopciones (Semanas 4–10)

**Objetivo:** Sitio funcional con catálogo de animales y sistema de adopciones básico. Primer animal adoptado digitalmente.

### Deliverables
- [ ] Homepage con CTA principales
- [ ] Catálogo de animales con búsqueda y filtros
- [ ] Perfil individual de animal
- [ ] Formulario de solicitud de adopción (multi-paso)
- [ ] Email de confirmación automático al solicitante
- [ ] Panel admin básico: gestión de animales + vista de solicitudes
- [ ] Contrato digital básico (Ley 4840 compliant)
- [ ] PWA básica (installable, cache de catálogo)
- [ ] SSL, dominio live, Core Web Vitals validados

### Epics involucrados
- EPIC-1 (catálogo)
- EPIC-2 (adopciones — flujo básico)
- EPIC-5 (admin — funcionalidad mínima)
- EPIC-8 (fundación)

### Criterio de éxito de fase
> Primera adopción procesada digitalmente de inicio a fin.

---

## Fase 2 — Portal de Usuarios + Notificaciones (Semanas 11–16)

**Objetivo:** Adoptantes tienen su propio espacio. Comunicaciones automatizadas por WhatsApp.

### Deliverables
- [ ] Sistema de autenticación (email + WhatsApp OTP)
- [ ] Portal adoptante: tracking de solicitudes, favoritos
- [ ] Portal admin completo: roles, cola de revisión, notas
- [ ] Notificaciones WhatsApp automáticas (estado de solicitud, aprobación, cita)
- [ ] Seguimiento post-adopción automatizado (día 2, 7, 30, 90)
- [ ] Cuestionario de matching adoptante-animal
- [ ] Gestión de lista de espera con posición transparente
- [ ] Formulario de devolución digital

### Epics involucrados
- EPIC-6 (portal usuarios)
- EPIC-2 (adopciones — flujo completo)
- EPIC-5 (admin completo)

---

## Fase 3 — Donaciones + Lost & Found (Semanas 17–23)

**Objetivo:** El refugio tiene ingresos digitales y la comunidad tiene una herramienta de Lost & Found.

### Deliverables
- [ ] Página de donaciones (única + recurrente)
- [ ] Integración Tigo Money + Personal Pay + PagoExpress
- [ ] Programa "Apadrinar un animal" con progress bar
- [ ] Stripe para tarjetas internacionales
- [ ] Portal donante (historial, recibos, gestión de recurrencias)
- [ ] Formularios Lost & Found (perdí / encontré)
- [ ] Mapa de reportes en Gran Asunción
- [ ] Motor de matching Lost & Found ↔ ingresos al refugio
- [ ] Notificación WhatsApp en caso de coincidencia

### Epics involucrados
- EPIC-4 (donaciones)
- EPIC-3 (lost & found)
- EPIC-6 (portal donante)

---

## Fase 4 — Comunidad, Contenido y Optimización (Semanas 24–30)

**Objetivo:** Plataforma completa con presencia editorial, SEO maduro y operaciones optimizadas.

### Deliverables
- [ ] Blog + sección de éxitos (alumni)
- [ ] Todas las páginas estáticas (About, Voluntariado, Socios, etc.)
- [ ] Contenido en guaraní para secciones clave
- [ ] Calendario de eventos con registro online
- [ ] Feed de Instagram/Facebook embebido
- [ ] Newsletter (WhatsApp broadcast + Mailchimp)
- [ ] Mapa de veterinarias aliadas
- [ ] Portal voluntario (turnos, horas, materiales)
- [ ] Portal familia foster completo
- [ ] Inventario del refugio
- [ ] Dashboard de reportes completo con métricas
- [ ] Cumplimiento completo Ley 7593/2025 (cookie consent, exportación de datos)
- [ ] SEO audit y optimizaciones

### Epics involucrados
- EPIC-7 (comunidad)
- EPIC-5 (admin — inventario + reportes)
- EPIC-6 (portales voluntario y foster)
- EPIC-8 (cumplimiento legal completo)

---

## Fase 5 — Estabilización y Escala (Semana 31+)

**Objetivo:** Producto maduro, retroalimentación incorporada, preparado para escalar a otros refugios.

### Deliverables
- [ ] Campañas de fundraising avanzadas (emergencias, eventos)
- [ ] Integración Facebook/Instagram Fundraisers
- [ ] Reportes avanzados (tasa de retorno por perfil, análisis de matching)
- [ ] Refinar matching algorithm con datos reales de adopciones
- [ ] Optimizaciones de performance basadas en datos de usuarios reales
- [ ] Documentación técnica completa para mantenimiento
- [ ] Capacitación del equipo del refugio
- [ ] Evaluación para expansion a otros refugios en Paraguay

---

## Timeline Resumido

```
Sem 1-3    │ Fase 0 — Setup y Diseño
Sem 4-10   │ Fase 1 — MVP Catálogo + Adopciones ★ LANZAMIENTO SOFT
Sem 11-16  │ Fase 2 — Portal Usuarios + WhatsApp Notificaciones
Sem 17-23  │ Fase 3 — Donaciones + Lost & Found        ★ LANZAMIENTO PÚBLICO
Sem 24-30  │ Fase 4 — Comunidad + Contenido + Optimización
Sem 31+    │ Fase 5 — Escala y Madurez
```

---

## Dependencias Críticas

| Dependencia | Bloquea | Acción requerida |
|-------------|---------|-----------------|
| WhatsApp Business API aprobada | Fase 2 notificaciones | Solicitar en semana 1 (proceso 2-4 semanas) |
| Tigo Money / Personal Pay API acceso | Fase 3 donaciones | Contactar Tigo en semana 10 (proceso 3-4 semanas) |
| Dominio .py o .com contratado | Fase 1 launch | Registrar en semana 1 |
| Fotos profesionales de animales | Fase 1 catálogo | Sesión de fotos antes de semana 8 |
| Certificado de esterilización format | Fase 1 contrato | Definir con equipo veterinario semana 2 |
