# Tech Stack — Refugio Animal Paraguay

## Principios de Selección

1. **Open source + bajo costo**: Organización sin fines de lucro — sin licencias comerciales
2. **Mobile-first**: 90% de usuarios en móvil con 3G/4G variable
3. **PWA sobre app nativa**: Evitar App Store; instalable desde el navegador
4. **Fullstack JS/TS**: Un solo lenguaje reduce fricción para el equipo pequeño
5. **Hosting económico**: Vercel/Railway over AWS/GCP para reducir DevOps overhead

---

## Frontend

| Tecnología | Decisión | Justificación |
|-----------|----------|---------------|
| **Next.js 14** | ✅ Elegido | App Router, RSC, SSG/SSR híbrido, excelente SEO |
| **TypeScript** | ✅ Elegido | Type safety, mejor DX, reduce bugs en producción |
| **Tailwind CSS** | ✅ Elegido | Utility-first, bundle pequeño, responsive trivial |
| **shadcn/ui** | ✅ Elegido | Componentes accesibles, sin vendor lock-in |
| **React Hook Form + Zod** | ✅ Elegido | Formularios complejos (adopción multi-paso) con validación |
| **TanStack Query** | ✅ Elegido | Cache cliente, optimistic updates, revalidación automática |
| **Zustand** | ✅ Elegido | Estado global liviano (favoritos, session) |
| **next-pwa / Serwist** | ✅ Elegido | Service worker, cache offline, instalable |
| **next-intl** | ✅ Elegido | i18n para español/guaraní |

### Alternativas consideradas y descartadas

| Descartado | Razón |
|-----------|-------|
| Create React App | Deprecated, sin SSR |
| Vue/Nuxt | Ecosistema más chico, menos opciones de empleo local |
| Remix | Curva de aprendizaje mayor, menos plugins PWA |
| Gatsby | Excesivamente estático para admin dinámico |

---

## Backend

| Tecnología | Decisión | Justificación |
|-----------|----------|---------------|
| **Supabase** | ✅ Elegido | PostgreSQL + Auth + Storage + Edge Functions + Realtime en un solo proveedor |
| **SQL Migrations (supabase CLI)** | ✅ Elegido | Schema versionado en git — NO Prisma. `supabase db push` para local, `supabase db push --linked` para producción |
| **Supabase Auth** | ✅ Elegido | Auth con email/magic link/OAuth, JWT con roles custom — NO NextAuth |
| **Supabase Storage** | ✅ Elegido | Buckets para fotos y documentos con RLS integrado — NO Cloudinary |
| **Supabase Edge Functions** | ✅ Elegido | Jobs background (recurring donations, notificaciones) — NO BullMQ |
| **Server Actions (Next.js)** | ✅ Elegido | Mutaciones de formulario sin route handlers separados |
| **Resend** | ✅ Elegido | Emails transaccionales — free tier 3k/mes |

> **DECISIÓN FIRME**: No usar Prisma. No usar Cloudinary. No usar NextAuth. Todo el backend pasa por Supabase. Ver `docs/ARCHITECTURE.md` para patrones de implementación.

### Para Fase 2+ (si el backend crece)

Los Edge Functions de Supabase escalan horizontalmente. Si las queries se vuelven muy complejas, evaluar PostgreSQL functions directas. No extraer a microservicios prematuramente.

---

## Infraestructura y Hosting

| Servicio | Uso | Costo estimado |
|---------|-----|----------------|
| **Vercel** (Hobby → Pro) | Frontend + API Routes | $0–20/mes |
| **Supabase** | PostgreSQL + Auth + Storage + Edge Functions | $0–25/mes |
| **Upstash Redis** | Rate limiting + cache | $0–10/mes |
| **GitHub Actions** | CI/CD | $0 (proyectos open source) |
| **Cloudflare** | DNS + SSL + WAF básico | $0 |

> **Imágenes**: Supabase Storage (bucket `animals-photos`, público, CDN automático). NO Cloudinary.

**Costo total estimado Fase 1**: ~$0–45/mes

---

## Integraciones Externas

Ver [INTEGRATIONS.md](INTEGRATIONS.md) para detalles. Resumen:

| Integración | SDK/Método |
|------------|-----------|
| WhatsApp Business API | Meta Cloud API via webhook |
| Tigo Money | REST API (previa firma de contrato) |
| Personal Pay | REST API |
| PagoExpress | REST API |
| Stripe | `stripe` npm package |
| Google Maps | `@vis.gl/react-google-maps` |
| Google Analytics 4 | `@next/third-parties/google` |
| Facebook Pixel | `@next/third-parties` |

---

## Calidad y Testing

| Herramienta | Uso |
|------------|-----|
| **Vitest** | Unit tests (componentes, utils, lógica de negocio) |
| **Playwright** | E2E tests (flujo de adopción, admin, pagos) |
| **ESLint + eslint-config-next** | Linting |
| **Prettier** | Formateo |
| **Lighthouse CI** | Core Web Vitals en cada PR |
| **Sentry** | Error tracking en producción |

---

## Estructura del Repositorio

```
refugio-animal-paraguay/
├── src/
│   ├── app/                    # Next.js App Router
│   │   ├── (public)/           # Rutas públicas (catálogo, adoptar, donar)
│   │   ├── (auth)/             # Autenticación (login, registro)
│   │   ├── (portal)/           # Portal autenticado (adoptante, voluntario, foster)
│   │   ├── admin/              # Panel admin (protegido por rol)
│   │   └── api/                # Route Handlers
│   │       ├── animals/
│   │       ├── adoptions/
│   │       ├── donations/
│   │       ├── lost-found/
│   │       └── webhooks/       # WhatsApp, pagos
│   ├── components/
│   │   ├── ui/                 # shadcn/ui + componentes base
│   │   ├── animals/            # Catálogo, perfil, galería
│   │   ├── adoption/           # Formularios, tracking
│   │   ├── admin/              # Tablas, dashboards
│   │   └── shared/             # Header, Footer, Nav
│   ├── services/               # BaseService + domain services (Supabase queries)
│   ├── actions/                # Next.js Server Actions (form mutations)
│   ├── hooks/                  # React custom hooks (useAsyncData, useModal, etc.)
│   ├── store/                  # Zustand stores (favoritos, session)
│   ├── lib/
│   │   ├── supabase/           # Supabase client (browser + server + admin)
│   │   ├── whatsapp/           # WhatsApp Business API client
│   │   ├── payments/           # Tigo Money, Stripe, etc.
│   │   ├── matching/           # Algoritmo pet-adopter matching
│   │   └── utils/
│   ├── styles/                 # CSS variables, tokens, cva variants
│   ├── types/                  # TypeScript type definitions
│   └── content/
│       ├── i18n/               # Traducciones es-PY / gn (next-intl)
│       └── seo/                # Metadata por ruta
├── supabase/
│   ├── config.toml             # Supabase project config
│   ├── migrations/             # SQL migrations (versionadas en git)
│   └── seed.sql                # Datos de prueba
├── public/
│   └── images/                 # Solo assets estáticos pequeños
├── tests/
│   ├── unit/
│   ├── e2e/
│   └── fixtures/
└── docs/                       # Esta carpeta
```

---

## Decisiones Clave Pendientes (Fase 0)

| Decisión | Opciones | Deadline |
|---------|---------|---------|
| Hosting DB | Supabase vs Railway vs NeonDB | Semana 1 |
| WhatsApp API provider | Meta directo vs Twilio vs WATI | Semana 1 (proceso largo) |
| CMS para blog | MDX (archivos) vs Payload CMS vs Contentlayer | Semana 2 |
| Firma digital | DocuSeal (self-hosted) vs HelloSign vs PDF manual | Semana 2 |
| Push notifications | Web Push API nativo vs OneSignal | Semana 3 |
