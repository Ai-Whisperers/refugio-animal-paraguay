# Project Overview — Refugio Animal Paraguay

## Fundadora

El proyecto es liderado por una ciudadana neerlandesa que se traslada a Paraguay con la misión de elevar el estándar de bienestar animal en el país. Cuenta con una red de apoyo en Europa (Países Bajos y comunidad europea) que financiará parcialmente las operaciones iniciales y campañas de rescate. Esta doble base — operaciones en Paraguay, donantes en Europa — define la estrategia de fundraising de la plataforma.

## Visión

Crear la plataforma digital de referencia para la adopción y bienestar animal en Paraguay: moderna, accesible desde móvil, culturalmente adaptada, y con alcance internacional de fundraising que conecte donantes europeos con el impacto real en los animales de Paraguay.

## Descripción

Refugio Animal Paraguay es un sitio web completo para un refugio de animales ubicado en el área de Gran Asunción, Paraguay. La plataforma cubre:

- Catálogo público de animales disponibles para adopción
- Sistema digital de solicitudes de adopción con seguimiento en tiempo real
- Programa foster (familias de acogida) con workflow dedicado
- Herramienta pública de animales perdidos y encontrados
- Sistema de donaciones y fundraising (local + internacional)
- Panel de administración interno para el equipo del refugio
- Portal autenticado para adoptantes, voluntarios, donantes y familias foster
- Hub de comunidad, educación y alcance social

## Problema que resuelve

**Para el público:**
- Los refugios de Paraguay operan mayormente por WhatsApp y Facebook de forma manual, sin sistema centralizado
- No existe una forma estructurada de aplicar para adoptar, rastrear el estado de la solicitud, ni gestionar el proceso post-adopción
- Los animales perdidos se reportan de forma desorganizada en grupos de Facebook

**Para el refugio:**
- Gestión de animales, aplicaciones, médicos, inventario y voluntarios en planillas o papel
- Comunicación con adoptantes 100% manual (WhatsApp personal del staff)
- Sin métricas ni reportes para tomar decisiones basadas en datos

## Alcance

### Incluido

| Área | Descripción |
|------|-------------|
| Sitio público | Catálogo, adopciones, donaciones, lost & found, comunidad |
| Portal de usuario | Adoptantes, voluntarios, donantes, familias foster |
| Panel admin | Gestión interna completa del refugio |
| Integraciones | WhatsApp Business, Tigo Money, Personal Pay, Google Analytics |
| Cumplimiento | Ley 4840/2013, Ley 7593/2025 |
| Idiomas | Español (primario), Guaraní (secciones clave) |

### Excluido (v1.0)

- App nativa iOS/Android (PWA cubre el caso de uso móvil)
- Integración con veterinarias externas en tiempo real
- Marketplace de insumos para mascotas
- Programa de adopción internacional

## Stakeholders

| Rol | Responsabilidad |
|-----|----------------|
| Dirección del refugio | Visión, aprobación de funcionalidades, operación |
| Staff veterinario | Registros médicos, evaluaciones de animales |
| Voluntarios | Cuidado diario, fotografía, logística de adopciones |
| Coordinador de adopciones | Revisión de aplicaciones, counseling, seguimiento |
| Familias adoptantes (usuarios) | Buscar y adoptar animales |
| Familias foster (usuarios) | Recibir animales temporalmente |
| Donantes (usuarios) | Financiar operaciones del refugio |
| Equipo técnico | Desarrollo, mantenimiento, infraestructura |

## Restricciones

- **Presupuesto**: Organización sin fines de lucro — priorizar stack open source y costos bajos
- **Conectividad**: Usuarios en zonas con 3G/4G variable — PWA y optimización agresiva de performance
- **Pagos**: Sin penetración de tarjetas de crédito en segmentos medios-bajos — Tigo Money obligatorio
- **Legal**: Cumplimiento con Ley 4840/2013 (bienestar animal) y Ley 7593/2025 (datos personales)
- **Idioma**: Contenido en español paraguayo, secciones clave también en guaraní

## Métricas de éxito

Ver [OBJECTIVES.md](OBJECTIVES.md) para métricas detalladas.

Indicadores principales:
- Tasa de adopción completada (objetivo: >70% de solicitudes aprobadas resultan en adopción)
- Tasa de retorno post-adopción (objetivo: <8% en 90 días)
- Tiempo promedio de estadía en refugio (objetivo: reducir 30%)
- Donaciones recurrentes (objetivo: 50 donantes mensuales en 6 meses)
- Animales perdidos resueltos via Lost & Found (objetivo: >40% de reportes)
