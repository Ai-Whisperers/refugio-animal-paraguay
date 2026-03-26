# Estrategia de Testing — Refugio Animal Paraguay

> **TDD First**: Ningún feature se implementa sin un test fallando primero.
> La suite de tests es documentación viva del comportamiento esperado del sistema.

---

## Stack de Testing

| Herramienta | Versión | Propósito |
|-------------|---------|-----------|
| **Vitest** | ^2.x | Unit + integration tests — rápido, TypeScript nativo, ESM |
| **React Testing Library** | ^16.x | Tests de componentes UI (comportamiento, no implementación) |
| **Playwright** | ^1.45+ | E2E — Chrome, Firefox, WebKit (iOS/Android simulation) |
| **MSW (Mock Service Worker)** | ^2.x | Interceptar requests HTTP en tests sin servidor real |
| **@faker-js/faker** | ^9.x | Factory de datos de prueba realistas |
| **prisma-test-environment** | custom | DB aislada por test suite con rollback automático |
| **@axe-core/playwright** | ^4.x | Accessibility testing automatizado en E2E |
| **lighthouse-ci** | ^0.14+ | Performance regression testing en CI |
| **Artillery** | ^2.x | Load testing para endpoints de pago |

---

## Pirámide de Testing

```
                    ┌─────────┐
                    │   E2E   │  ← ~20 tests (flujos críticos completos)
                    │Playwright│    Más lento, más costoso, más valor por test
                   /───────────\
                  /  Integration │  ← ~80 tests (API routes, DB, webhooks)
                 /    (Vitest)   \    Servidor real, base de datos de test
                /─────────────────\
               /   Component Tests │ ← ~150 tests (React Testing Library)
              /    (Vitest + RTL)  \   DOM real, sin browser completo
             /─────────────────────\
            /       Unit Tests      │ ← ~300+ tests (lógica pura)
           /        (Vitest)        \  Rápido, sin side effects
          /─────────────────────────\
```

### Distribución objetivo de tiempo de ejecución

| Suite | Tiempo objetivo | Ejecutar en |
|-------|----------------|-------------|
| Unit | <30 segundos | Pre-commit, cada save (watch) |
| Component | <60 segundos | Pre-commit |
| Integration | <3 minutos | Pre-push, PR |
| E2E | <10 minutos | PR, staging deploy |
| Lighthouse CI | <5 minutos | Solo en PR contra main |

---

## Configuración del Proyecto

### `vitest.config.ts`

```typescript
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import tsconfigPaths from 'vite-tsconfig-paths'

export default defineConfig({
  plugins: [react(), tsconfigPaths()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./tests/setup/vitest-setup.ts'],
    environmentOptions: {
      jsdom: {
        url: 'http://localhost:3000',
      },
    },
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'lcov', 'html'],
      exclude: [
        'node_modules/**',
        'tests/**',
        '**/*.config.*',
        '**/migrations/**',
        '.next/**',
      ],
      thresholds: {
        lines: 80,
        functions: 80,
        branches: 75,
        statements: 80,
      },
    },
  },
})
```

### `playwright.config.ts`

```typescript
import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [
    ['html'],
    ['json', { outputFile: 'playwright-report/results.json' }],
  ],
  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:3000',
    trace: 'on-first-retry',
    video: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
    // Desktop
    {
      name: 'chromium-desktop',
      use: { ...devices['Desktop Chrome'] },
    },
    // Mobile — Paraguay es 90% móvil
    {
      name: 'android-chrome',
      use: {
        ...devices['Pixel 7'],
        // Simular conexión 4G paraguaya
        launchOptions: {
          args: ['--enable-precise-memory-info'],
        },
      },
    },
    {
      name: 'ios-safari',
      use: { ...devices['iPhone 14'] },
    },
  ],
  webServer: {
    command: 'npm run dev:test',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  },
})
```

---

## Estructura de Directorios

```
tests/
├── setup/
│   ├── vitest-setup.ts          # Globals: jest-dom matchers, MSW lifecycle
│   ├── db-setup.ts              # Prisma test client con transacciones aisladas
│   └── test-env.ts              # Variables de entorno para tests
│
├── factories/
│   ├── animal.factory.ts        # createAnimal(), createDog(), createCat()
│   ├── user.factory.ts          # createAdopter(), createAdmin(), createVolunteer()
│   ├── adoption.factory.ts      # createApplication(), createContract()
│   ├── donation.factory.ts      # createDonation(), createCampaign()
│   └── lost-found.factory.ts    # createLostReport(), createFoundReport()
│
├── mocks/
│   ├── handlers/
│   │   ├── whatsapp.ts          # Mock WhatsApp Business API
│   │   ├── stripe.ts            # Mock Stripe API
│   │   ├── cloudinary.ts        # Mock Cloudinary upload
│   │   └── tigo-money.ts        # Mock Tigo Money API
│   └── server.ts                # MSW server setup
│
├── unit/
│   ├── lib/
│   │   ├── animal-matching.test.ts
│   │   ├── adoption-scoring.test.ts
│   │   ├── donation-receipts.test.ts
│   │   └── lost-found-matching.test.ts
│   └── utils/
│       ├── currency.test.ts     # ₲ formatting
│       ├── date-locale.test.ts  # es-PY date formatting
│       └── validators.test.ts   # Zod schemas
│
├── component/
│   ├── catalog/
│   │   ├── AnimalCard.test.tsx
│   │   ├── CatalogFilters.test.tsx
│   │   └── AnimalProfile.test.tsx
│   ├── adoption/
│   │   ├── AdoptionForm.test.tsx    # Multi-step form
│   │   ├── ApplicationStatus.test.tsx
│   │   └── ContractViewer.test.tsx
│   ├── donations/
│   │   ├── DonationForm.test.tsx    # Local payments
│   │   ├── EuropeanDonationForm.test.tsx  # iDEAL, SEPA, PayPal
│   │   └── CampaignProgress.test.tsx
│   └── admin/
│       ├── ApplicationQueue.test.tsx
│       └── AnimalForm.test.tsx
│
├── integration/
│   ├── api/
│   │   ├── animals/
│   │   │   ├── GET-animals.test.ts
│   │   │   ├── POST-animal.test.ts
│   │   │   └── PATCH-animal-status.test.ts
│   │   ├── adoptions/
│   │   │   ├── POST-application.test.ts
│   │   │   ├── PATCH-application-status.test.ts
│   │   │   └── POST-contract.test.ts
│   │   ├── donations/
│   │   │   ├── POST-donation-local.test.ts
│   │   │   ├── POST-donation-stripe.test.ts
│   │   │   └── POST-donation-ideal.test.ts
│   │   └── webhooks/
│   │       ├── POST-whatsapp-webhook.test.ts
│   │       └── POST-stripe-webhook.test.ts
│   └── db/
│       ├── animal-queries.test.ts
│       └── donation-aggregates.test.ts
│
└── e2e/
    ├── catalog/
    │   └── browse-and-filter.spec.ts
    ├── adoption/
    │   ├── complete-adoption-flow.spec.ts   # CRÍTICO — TDD obligatorio
    │   └── application-status-tracking.spec.ts
    ├── donations/
    │   ├── donate-tigo-money.spec.ts         # CRÍTICO
    │   ├── donate-stripe-card.spec.ts        # CRÍTICO
    │   ├── donate-paypal.spec.ts             # CRÍTICO
    │   └── donate-ideal-european.spec.ts     # CRÍTICO
    ├── lost-found/
    │   └── report-lost-pet.spec.ts
    ├── admin/
    │   ├── approve-adoption.spec.ts          # CRÍTICO
    │   ├── manage-animal.spec.ts
    │   └── role-based-access.spec.ts
    ├── auth/
    │   ├── login-whatsapp-otp.spec.ts
    │   └── register-user.spec.ts
    └── accessibility/
        └── wcag-aa-critical-pages.spec.ts
```

---

## Base de Datos de Testing

### Estrategia: Transacciones aisladas por test suite

```typescript
// tests/setup/db-setup.ts
import { PrismaClient } from '@prisma/client'
import { beforeEach, afterEach } from 'vitest'

const prisma = new PrismaClient()

export function useTestDB() {
  let tx: Parameters<Parameters<typeof prisma.$transaction>[0]>[0]

  beforeEach(async () => {
    // Cada test corre dentro de una transacción que se revierte
    await prisma.$executeRaw`BEGIN`
    tx = prisma  // En tests reales usar prisma.$transaction
  })

  afterEach(async () => {
    await prisma.$executeRaw`ROLLBACK`
  })

  return () => tx
}
```

### Variables de entorno para tests

```bash
# .env.test
DATABASE_URL="postgresql://admin:test_password@localhost:5432/refugio_test"
NEXTAUTH_SECRET="test-secret-not-for-production"
NEXTAUTH_URL="http://localhost:3000"
WHATSAPP_TOKEN="mock-token"
STRIPE_SECRET_KEY="sk_test_..."
CLOUDINARY_CLOUD_NAME="test-cloud"
```

---

## Factories de Datos

```typescript
// tests/factories/animal.factory.ts
import { faker } from '@faker-js/faker/locale/es'
import type { Animal, Species, AnimalStatus } from '@prisma/client'

export function createAnimal(overrides: Partial<Animal> = {}): Animal {
  return {
    id: faker.string.cuid(),
    name: faker.helpers.arrayElement(['Luna', 'Tobby', 'Max', 'Negra', 'Pelusa']),
    species: 'DOG' as Species,
    breed: faker.helpers.arrayElement(['Mestizo', 'Labrador', null]),
    sex: faker.helpers.arrayElement(['MALE', 'FEMALE']),
    estimatedAge: faker.number.int({ min: 1, max: 120 }),  // meses
    weight: faker.number.float({ min: 1, max: 50, fractionDigits: 1 }),
    size: faker.helpers.arrayElement(['SMALL', 'MEDIUM', 'LARGE']),
    status: 'AVAILABLE' as AnimalStatus,
    sterilized: faker.datatype.boolean(),
    vaccinated: faker.datatype.boolean(),
    microchipped: faker.datatype.boolean(),
    goodWithKids: faker.datatype.boolean(),
    goodWithDogs: faker.datatype.boolean(),
    goodWithCats: faker.datatype.boolean(),
    specialNeeds: null,
    description: faker.lorem.sentences(2),
    createdAt: new Date(),
    updatedAt: new Date(),
    ...overrides,
  }
}

export const createUrgentDog = () => createAnimal({ species: 'DOG', status: 'URGENT' })
export const createKitten = () => createAnimal({ species: 'CAT', estimatedAge: faker.number.int({ min: 1, max: 6 }) })
```

```typescript
// tests/factories/donation.factory.ts
import { faker } from '@faker-js/faker'
import type { Donation, PaymentMethod, Currency } from '@prisma/client'

export function createDonation(overrides: Partial<Donation> = {}): Donation {
  return {
    id: faker.string.cuid(),
    amount: faker.number.int({ min: 50000, max: 500000 }),  // Guaraníes
    currency: 'PYG' as Currency,
    paymentMethod: 'TIGO_MONEY' as PaymentMethod,
    status: 'COMPLETED',
    donorName: faker.person.fullName(),
    donorEmail: faker.internet.email(),
    receiptUrl: null,
    campaignId: null,
    sponsoredAnimalId: null,
    recurring: false,
    externalId: faker.string.alphanumeric(20),
    createdAt: new Date(),
    ...overrides,
  }
}

export const createEuropeanDonation = (overrides = {}) =>
  createDonation({
    currency: 'EUR',
    amount: faker.number.int({ min: 10, max: 500 }),
    paymentMethod: 'IDEAL',
    ...overrides,
  })
```

---

## MSW — Mock de Integraciones Externas

```typescript
// tests/mocks/handlers/stripe.ts
import { http, HttpResponse } from 'msw'

export const stripeHandlers = [
  // Crear PaymentIntent exitoso
  http.post('https://api.stripe.com/v1/payment_intents', () => {
    return HttpResponse.json({
      id: 'pi_test_mock_123',
      client_secret: 'pi_test_mock_123_secret_abc',
      status: 'requires_payment_method',
    })
  }),

  // Webhook de pago completado
  http.post('https://api.stripe.com/v1/webhook', () => {
    return HttpResponse.json({ received: true })
  }),
]

// tests/mocks/handlers/whatsapp.ts
export const whatsappHandlers = [
  http.post('https://graph.facebook.com/*/messages', () => {
    return HttpResponse.json({
      messaging_product: 'whatsapp',
      contacts: [{ wa_id: '595981123456' }],
      messages: [{ id: 'mock_msg_id_123' }],
    })
  }),
]
```

---

## Patrones TDD

### Red-Green-Refactor en la práctica

```typescript
// ❌ INCORRECTO: implementar primero, tests después
// ✅ CORRECTO: test fallando → código mínimo → refactor

// Ejemplo: matching de animal perdido con ingresos al refugio

// PASO 1: Escribir el test (RED)
// tests/unit/lib/lost-found-matching.test.ts
describe('matchLostReportWithIntakes', () => {
  it('returns a match when species, color, and neighborhood match', () => {
    const lostReport = createLostReport({
      species: 'DOG',
      colors: ['BROWN', 'WHITE'],
      neighborhood: 'San Lorenzo',
    })
    const intake = createAnimal({
      species: 'DOG',
      colors: ['BROWN', 'WHITE'],
      intakeAddress: 'San Lorenzo, barrio Mbocayaty',
    })

    const matches = matchLostReportWithIntakes(lostReport, [intake])

    expect(matches).toHaveLength(1)
    expect(matches[0].score).toBeGreaterThan(0.7)
    expect(matches[0].animal.id).toBe(intake.id)
  })

  it('does not match when species differ', () => {
    const lostReport = createLostReport({ species: 'CAT' })
    const intake = createAnimal({ species: 'DOG' })

    const matches = matchLostReportWithIntakes(lostReport, [intake])

    expect(matches).toHaveLength(0)
  })
})

// PASO 2: Implementar minimum code (GREEN)
// src/lib/lost-found-matching.ts
export function matchLostReportWithIntakes(report, intakes) {
  return intakes
    .filter(a => a.species === report.species)
    .map(a => ({ animal: a, score: calculateMatchScore(report, a) }))
    .filter(m => m.score > 0.5)
    .sort((a, b) => b.score - a.score)
}

// PASO 3: Refactor con más tests de edge cases
```

---

## Tests E2E Obligatorios (por DEFINITION-OF-DONE)

### Flujo de Adopción Completo

```typescript
// tests/e2e/adoption/complete-adoption-flow.spec.ts
import { test, expect } from '@playwright/test'
import { injectAxe, checkA11y } from 'axe-playwright'

test.describe('Flujo completo de adopción', () => {
  test('usuario puede completar solicitud de adopción en móvil', async ({ page }) => {
    // Simular condición de Paraguay: pantalla 390px, 4G
    await page.setViewportSize({ width: 390, height: 844 })

    // 1. Navegar al catálogo
    await page.goto('/adoptar')
    await expect(page.getByRole('heading', { name: 'Animales disponibles' })).toBeVisible()

    // 2. Buscar y seleccionar un animal
    await page.getByLabel('Filtrar por especie').selectOption('Perros')
    await page.getByRole('link', { name: /Conocer a/ }).first().click()

    // 3. Iniciar solicitud
    await page.getByRole('button', { name: 'Quiero adoptar' }).click()

    // Accesibilidad en el formulario
    await injectAxe(page)
    await checkA11y(page, null, {
      rules: { 'color-contrast': { enabled: true } },
    })

    // 4. Completar step 1: datos personales
    await page.getByLabel('Nombre completo').fill('Lorena García')
    await page.getByLabel('Número de cédula').fill('4123456')
    await page.getByLabel('Número de WhatsApp').fill('0981123456')
    await page.getByRole('button', { name: 'Siguiente' }).click()

    // 5. Verificar que el estado se guardó en localStorage (offline resilience)
    const savedData = await page.evaluate(() =>
      JSON.parse(localStorage.getItem('adoption-form-draft') || '{}')
    )
    expect(savedData.personalInfo.name).toBe('Lorena García')

    // ... continuar hasta submit

    // 6. Verificar confirmación
    await expect(page.getByText('¡Tu solicitud llegó!')).toBeVisible()
    await expect(page.getByText('Te confirmamos por WhatsApp')).toBeVisible()
  })
})
```

### Flujo de Donación Europeo (iDEAL)

```typescript
// tests/e2e/donations/donate-ideal-european.spec.ts
test('donante holandés puede donar vía iDEAL', async ({ page }) => {
  await page.goto('/donar/europa')

  // Verificar que la página está en inglés/neerlandés
  await expect(page.getByText('Support animal welfare in Paraguay')).toBeVisible()

  // Seleccionar iDEAL
  await page.getByLabel('Payment method').selectOption('iDEAL')

  // Seleccionar banco holandés
  await page.getByLabel('Select your bank').selectOption('ING')

  await page.getByLabel('Amount (EUR)').fill('25')
  await page.getByRole('button', { name: 'Donate now' }).click()

  // Verificar redirect a Stripe + iDEAL
  await expect(page).toHaveURL(/stripe\.com/)
})
```

### Seguridad de Roles en Admin

```typescript
// tests/e2e/admin/role-based-access.spec.ts
test('voluntario no puede aprobar adopciones', async ({ page }) => {
  await loginAs(page, 'volunteer')
  await page.goto('/admin/adopciones/123/aprobar')

  await expect(page).toHaveURL('/admin/dashboard')
  await expect(page.getByText('No tenés permisos para esta acción')).toBeVisible()
})
```

---

## CI/CD Pipeline de Testing

### `.github/workflows/test.yml`

```yaml
name: Test Suite

on: [push, pull_request]

jobs:
  unit-and-component:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - run: npm ci
      - run: npm run test:unit -- --coverage
      - uses: actions/upload-artifact@v4
        with:
          name: coverage-report
          path: coverage/

  integration:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_DB: refugio_test
          POSTGRES_PASSWORD: test_password
        ports:
          - 5432:5432
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20', cache: 'npm' }
      - run: npm ci
      - run: npx prisma migrate deploy
        env:
          DATABASE_URL: postgresql://postgres:test_password@localhost:5432/refugio_test
      - run: npm run test:integration
        env:
          DATABASE_URL: postgresql://postgres:test_password@localhost:5432/refugio_test

  e2e:
    runs-on: ubuntu-latest
    needs: [unit-and-component]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20', cache: 'npm' }
      - run: npm ci
      - run: npx playwright install --with-deps chromium webkit
      - run: npm run build:test
      - run: npm run test:e2e
      - uses: actions/upload-artifact@v4
        if: failure()
        with:
          name: playwright-report
          path: playwright-report/

  lighthouse:
    runs-on: ubuntu-latest
    needs: [e2e]
    if: github.event_name == 'pull_request'
    steps:
      - uses: actions/checkout@v4
      - run: npm ci && npm run build:test
      - name: Run Lighthouse CI
        run: |
          npm install -g @lhci/cli
          lhci autorun
        env:
          LHCI_GITHUB_APP_TOKEN: ${{ secrets.LHCI_GITHUB_APP_TOKEN }}
```

### `lighthouserc.yml`

```yaml
ci:
  collect:
    url:
      - 'http://localhost:3000/adoptar'
      - 'http://localhost:3000/adoptar/luna-abc123'
      - 'http://localhost:3000/donar'
    settings:
      throttlingMethod: simulate
      throttling:
        rttMs: 150          # Paraguay 4G typical RTT
        throughputKbps: 1638  # ~4G Paraguay
        cpuSlowdownMultiplier: 4  # Mid-range Android
  assert:
    preset: lighthouse:recommended
    assertions:
      first-contentful-paint: [warn, { maxNumericValue: 3000 }]
      largest-contentful-paint: [error, { maxNumericValue: 4000 }]
      cumulative-layout-shift: [error, { maxNumericValue: 0.1 }]
      total-blocking-time: [warn, { maxNumericValue: 600 }]
      interactive: [warn, { maxNumericValue: 5000 }]
```

---

## `package.json` — Scripts de Testing

```json
{
  "scripts": {
    "test": "vitest",
    "test:unit": "vitest run tests/unit tests/component",
    "test:integration": "vitest run tests/integration",
    "test:e2e": "playwright test",
    "test:e2e:ui": "playwright test --ui",
    "test:e2e:headed": "playwright test --headed",
    "test:all": "npm run test:unit && npm run test:integration && npm run test:e2e",
    "test:coverage": "vitest run --coverage",
    "test:watch": "vitest --watch",
    "test:accessibility": "playwright test tests/e2e/accessibility/",
    "test:ci": "vitest run --coverage --reporter=junit && playwright test --reporter=github"
  }
}
```

---

## Cobertura Mínima por Módulo

| Módulo | Lines | Branches | Justificación |
|--------|-------|----------|---------------|
| `lib/adoption-scoring` | 90% | 85% | Lógica de negocio crítica |
| `lib/lost-found-matching` | 90% | 80% | Impacto en seguridad de animales |
| `lib/payment-processing` | 95% | 90% | Manejo de dinero real |
| `lib/whatsapp-templates` | 85% | 80% | Comunicación con usuarios |
| `components/` | 80% | 70% | UI — combinado con E2E |
| `api/` | 85% | 80% | Endpoints públicos |
| `utils/` | 90% | 85% | Utilidades compartidas |

---

## Testing de Accesibilidad

```typescript
// tests/e2e/accessibility/wcag-aa-critical-pages.spec.ts
import { test, expect } from '@playwright/test'
import AxeBuilder from '@axe-core/playwright'

const CRITICAL_PAGES = [
  { url: '/adoptar', name: 'Catálogo' },
  { url: '/adoptar/luna-abc123', name: 'Perfil de animal' },
  { url: '/adoptar/solicitud', name: 'Formulario adopción' },
  { url: '/donar', name: 'Página donaciones' },
  { url: '/perdidos-encontrados', name: 'Lost & Found' },
  { url: '/admin/dashboard', name: 'Panel admin' },
]

for (const { url, name } of CRITICAL_PAGES) {
  test(`${name} no tiene violaciones WCAG AA`, async ({ page }) => {
    await page.goto(url)
    await page.waitForLoadState('networkidle')

    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .analyze()

    expect(results.violations).toEqual([])
  })
}
```

---

## Checklist TDD por Feature

Antes de escribir código para cualquier historia de usuario:

```
□ ¿Escribí el test unitario para la lógica de negocio?
□ ¿El test falla por la razón correcta (red)?
□ ¿El código implementado es el mínimo para pasar (green)?
□ ¿Refactoricé sin romper tests?
□ ¿Los edge cases están cubiertos (null, empty, invalid)?
□ ¿Los estados de error tienen tests?
□ ¿El flujo crítico tiene test E2E si aplica?
□ ¿La cobertura del módulo está en el threshold definido?
```

---

## Convenciones de Naming

```typescript
// Tests unitarios: describe + it pattern
describe('matchLostReportWithIntakes', () => {
  it('returns empty array when no species match', () => {})
  it('returns sorted results by match score descending', () => {})
  it('throws error when report is null', () => {})
})

// Tests de componente: user behavior focus
describe('AnimalCard', () => {
  it('shows URGENT badge when animal status is URGENT', () => {})
  it('navigates to animal profile when card is clicked', () => {})
  it('adds animal to favorites when heart button is clicked', () => {})
})

// E2E: user journey format
test('adoptante completa formulario de 5 pasos sin perder datos al recargar')
test('donante europeo dona 25 EUR vía iDEAL y recibe recibo automático')
test('admin aprueba solicitud de adopción desde panel en tablet')
```

---

## Métricas de Calidad

| Métrica | Umbral mínimo | Herramienta |
|---------|--------------|-------------|
| Cobertura de líneas | 80% | Vitest + v8 |
| Cobertura de ramas | 75% | Vitest + v8 |
| E2E pass rate en CI | 100% | Playwright |
| Lighthouse Performance (4G mobile) | ≥ 75 | Lighthouse CI |
| Lighthouse Accessibility | ≥ 90 | Lighthouse CI |
| Lighthouse SEO | ≥ 90 | Lighthouse CI |
| Violaciones axe-core WCAG AA | 0 | @axe-core/playwright |
| Tests flaky en CI (últimos 30 días) | <2% | GitHub Actions |
