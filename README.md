# Refugio Animal Paraguay

> Plataforma web integral para la gestión y adopción de animales en Paraguay.

## ¿Qué es esto?

Refugio Animal Paraguay es un sitio web completo para un refugio de animales en Paraguay. Cubre el ciclo de vida completo: desde que un animal ingresa al refugio hasta su adopción, incluyendo donaciones, programa de familias de acogida (foster), reportes de animales perdidos/encontrados, y gestión operativa interna.

El proyecto fue diseñado con el contexto local en mente: 90% de usuarios móviles, WhatsApp como canal de comunicación dominante (97.5% de penetración), pagos locales (Tigo Money, Personal Pay, PagoExpress), bilingüismo español/guaraní, y cumplimiento de la Ley 4840/2013 y Ley 7593/2025 de Paraguay.

---

## Documentación

| Archivo | Descripción |
|---------|-------------|
| [PROJECT-OVERVIEW.md](docs/PROJECT-OVERVIEW.md) | Visión general, objetivos y alcance |
| [OBJECTIVES.md](docs/OBJECTIVES.md) | Objetivos SMART y métricas de éxito |
| [EPICS.md](docs/EPICS.md) | Los 8 epics con descripción detallada |
| [ROADMAP.md](docs/ROADMAP.md) | Fases de desarrollo y cronograma |
| [TECH-STACK.md](docs/TECH-STACK.md) | Decisiones tecnológicas y justificación |
| [USER-PERSONAS.md](docs/USER-PERSONAS.md) | Perfiles de usuarios objetivo |
| [PARAGUAY-CONTEXT.md](docs/PARAGUAY-CONTEXT.md) | Contexto local: legal, cultural, infraestructura |
| [UX-PRINCIPLES.md](docs/UX-PRINCIPLES.md) | Principios de diseño y UX |
| [DATA-MODEL.md](docs/DATA-MODEL.md) | Modelo de datos principal |
| [INTEGRATIONS.md](docs/INTEGRATIONS.md) | Integraciones externas (WhatsApp, pagos, etc.) |
| [COMPLIANCE.md](docs/COMPLIANCE.md) | Cumplimiento legal (Ley 4840, Ley 7593) |
| [CONTENT-STRATEGY.md](docs/CONTENT-STRATEGY.md) | Estrategia de contenido y SEO |
| [DEFINITION-OF-DONE.md](docs/DEFINITION-OF-DONE.md) | Criterios de aceptación estándar |

---

## Epics (resumen)

```
[EPIC-1] Pet Catalog & Discovery               ← prioridad 90
[EPIC-2] Adoption Process & Application System ← prioridad 95
[EPIC-3] Lost & Found / Stray Reporting        ← prioridad 75
[EPIC-4] Donation & Fundraising Platform       ← prioridad 80
[EPIC-5] Shelter Operations & Admin Dashboard  ← prioridad 85
[EPIC-6] User Accounts & Portal                ← prioridad 70
[EPIC-7] Community, Education & Outreach       ← prioridad 65
[EPIC-8] Technical Foundation & Compliance     ← prioridad 60
```

---

## Base de datos del proyecto

```
psql postgresql://admin:pg_shared_s3cur3_2026@localhost:5433/projects
```

Project ID: `b9c81ffd-0904-4f58-8bc2-5b286462e46f`

Ver tareas activas:
```sql
SELECT t.title, t.status, t.agent_type, s.title AS story, e.title AS epic
FROM tasks t
JOIN stories s ON t.story_id = s.id
JOIN epics e ON s.epic_id = e.id
WHERE e.project_id = 'b9c81ffd-0904-4f58-8bc2-5b286462e46f'
ORDER BY t.priority DESC;
```
