# Integraciones Externas — Refugio Animal Paraguay

---

## 1. WhatsApp Business API (Meta)

**Prioridad:** CRÍTICA — bloquea Fase 2
**Proceso de aprobación:** 2–4 semanas → iniciar en Semana 1

### Casos de uso

| Caso | Template | Trigger |
|------|---------|---------|
| Confirmación de solicitud recibida | `adoption_received` | POST /api/adoptions |
| Estado actualizado (aprobado/rechazado) | `adoption_status_update` | Admin actualiza estado |
| Recordatorio de visita acordada | `visit_reminder` | 24h antes de la visita |
| Seguimiento post-adopción | `followup_day_{2,7,30,90}` | BullMQ scheduled job |
| Coincidencia Lost & Found | `lost_found_match` | Matching engine |
| OTP de login | `otp_login` | Auth flow |
| Recordatorio de turno voluntario | `volunteer_shift_reminder` | 2h antes del turno |

### Configuración

```typescript
// lib/whatsapp/client.ts
const WHATSAPP_CONFIG = {
  phoneNumberId: process.env.WA_PHONE_NUMBER_ID,
  accessToken: process.env.WA_ACCESS_TOKEN,
  webhookVerifyToken: process.env.WA_WEBHOOK_VERIFY_TOKEN,
  apiVersion: 'v19.0',
  baseUrl: 'https://graph.facebook.com',
}

// Enviar mensaje con template
async function sendTemplate(to: string, templateName: string, params: string[]) {
  const response = await fetch(
    `${baseUrl}/${apiVersion}/${phoneNumberId}/messages`,
    {
      method: 'POST',
      headers: { Authorization: `Bearer ${accessToken}` },
      body: JSON.stringify({
        messaging_product: 'whatsapp',
        to,
        type: 'template',
        template: {
          name: templateName,
          language: { code: 'es' },
          components: [{ type: 'body', parameters: params.map(p => ({ type: 'text', text: p })) }]
        }
      })
    }
  )
  return response.json()
}
```

### Webhook (incoming messages)

```
POST /api/webhooks/whatsapp
```

Procesar respuestas de usuarios a los follow-ups post-adopción.

### Consideraciones

- Las **templates de mensajes** deben ser aprobadas por Meta antes de usar
- Solo se puede enviar mensajes template a usuarios que no iniciaron conversación en las últimas 24h
- Los mensajes de sesión (respuesta a mensaje del usuario) no requieren template
- Costo: ~$0.05–0.08 USD por conversación de negocio (no por mensaje)
- Proveedor alternativo si Meta es muy complejo para el MVP: **Twilio WhatsApp** o **WATI** (tienen SDK más simple)

---

## 2. Tigo Money

**Prioridad:** ALTA — bloquea Fase 3 donaciones
**Proceso:** Contrato comercial con Tigo → iniciar en Semana 10

### Flujo de pago

```
1. Usuario selecciona Tigo Money
2. Backend crea orden de pago → Tigo API devuelve transactionId + QR/código
3. Usuario paga desde app Tigo Money o kiosco
4. Tigo envía webhook de confirmación a POST /api/webhooks/tigo
5. Backend actualiza estado de pago → notifica por WhatsApp
```

### Variables de entorno requeridas

```env
TIGO_API_URL=https://api.tigo.com.py/...
TIGO_MERCHANT_ID=
TIGO_API_KEY=
TIGO_WEBHOOK_SECRET=
```

### Casos de uso en el sitio

- Pago de tarifa de adopción (Gs. 80,000–300,000)
- Donaciones únicas
- Donaciones recurrentes (push mensual desde Tigo)

---

## 3. Personal Pay

**Prioridad:** MEDIA
**Proceso:** Registro en portal de Personal (Telecom Paraguay)

Similar a Tigo Money pero para clientes de Personal. Flujo idéntico con webhook de confirmación.

---

## 4. PagoExpress

**Prioridad:** MEDIA
**Caso de uso:** Usuarios sin smartphone (pagan en kiosco físico con un código)

```
1. Backend genera código de pago PagoExpress
2. Usuario lleva el código a cualquier kiosco adherido
3. Kiosco procesa el pago
4. PagoExpress envía webhook de confirmación
```

Cobertura: 2,000+ puntos de pago en todo Paraguay, incluyendo zonas sin acceso bancario.

---

## 5. Stripe — Pagos Internacionales y Europeos

**Prioridad:** ALTA para donaciones internacionales
**Cuenta necesaria:** Stripe cuenta paraguaya (con entidad legal) ó cuenta neerlandesa de la fundadora
**Nota:** Para processar iDEAL, SEPA y otros métodos europeos, Stripe recomienda la cuenta del país del banco receptor — usar cuenta NL de la fundadora para recibir EUR directamente.

### 5.1 Arquitectura de Monedas

```
Donante PY (Gs.) → Tigo Money / Personal Pay / PagoExpress
Donante internacional (USD) → Stripe (tarjeta, Google Pay, Apple Pay, Stripe Link)
Donante europeo (EUR) → Stripe (iDEAL, SEPA, Bancontact, Sofort) ó PayPal ó Donorbox
```

### 5.2 Configuración base

```typescript
// lib/payments/stripe.ts
import Stripe from 'stripe'

export const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, {
  apiVersion: '2024-06-20',
  typescript: true,
})

// Tipos de donación
export type DonationCurrency = 'PYG' | 'USD' | 'EUR'
export type PaymentMethodType =
  | 'card' | 'google_pay' | 'apple_pay' | 'link'   // internacional
  | 'ideal' | 'sepa_debit' | 'bancontact' | 'sofort' // europeos
```

### 5.3 Donaciones en USD (internacionales generales)

```typescript
export async function createUSDDonationIntent(
  amountUSD: number,
  donorEmail: string,
  metadata: Record<string, string> = {}
) {
  return stripe.paymentIntents.create({
    amount: Math.round(amountUSD * 100), // centavos
    currency: 'usd',
    receipt_email: donorEmail,
    metadata: { donorEmail, type: 'donation', ...metadata },
    automatic_payment_methods: { enabled: true },
  })
}
```

### 5.4 Donaciones en EUR — iDEAL (Países Bajos, método #1)

iDEAL es el método de pago online más usado en Países Bajos (~70% del e-commerce).
Requiere que el banco del receptor soporte IBAN europeo (usar cuenta bancaria NL de la fundadora).

```typescript
// app/donar/europa/page.tsx — página dedicada en inglés/neerlandés
export async function createIDEALPaymentIntent(
  amountEUR: number,
  donorEmail: string,
  donorName: string
) {
  const paymentIntent = await stripe.paymentIntents.create({
    amount: Math.round(amountEUR * 100), // céntimos
    currency: 'eur',
    payment_method_types: ['ideal'],
    receipt_email: donorEmail,
    metadata: {
      donorEmail,
      donorName,
      type: 'european_donation',
      source_country: 'NL',
    },
  })
  return paymentIntent
}

// Componente React (frontend)
// Usar @stripe/react-stripe-js con IbanElement para iDEAL
import { IdealBankElement, useStripe, useElements } from '@stripe/react-stripe-js'

const handleIDEALPayment = async () => {
  const { error } = await stripe!.confirmIdealPayment(clientSecret, {
    payment_method: {
      ideal: elements!.getElement(IdealBankElement)!,
      billing_details: { name: donorName, email: donorEmail },
    },
    return_url: `${window.location.origin}/donar/europa/gracias`,
  })
}
```

### 5.5 SEPA Direct Debit (donaciones recurrentes desde Europa)

SEPA permite débito directo desde cualquier cuenta bancaria de los 36 países SEPA.
Ideal para donantes recurrentes — se autoriza una vez y se cobra mensualmente.

```typescript
// Paso 1: Crear SetupIntent para guardar mandato SEPA
export async function createSEPASetupIntent(
  donorEmail: string,
  donorName: string,
  anbiConsent: boolean // Para donantes NL con deducción fiscal ANBI
) {
  return stripe.setupIntents.create({
    payment_method_types: ['sepa_debit'],
    metadata: {
      donorEmail,
      donorName,
      anbi_consent: String(anbiConsent),
      mandate_date: new Date().toISOString(),
    },
  })
}

// Paso 2: Confirmar mandato SEPA con IBAN del donante
// Frontend: usar IbanElement de @stripe/react-stripe-js
import { IbanElement } from '@stripe/react-stripe-js'

const confirmSEPA = async () => {
  await stripe!.confirmSepaDebitSetup(clientSecret, {
    payment_method: {
      sepa_debit: elements!.getElement(IbanElement)!,
      billing_details: {
        name: donorName,
        email: donorEmail,
        address: { country: donorCountry }, // 'NL', 'DE', 'BE', etc.
      },
    },
  })
  // Guardar paymentMethodId → BullMQ crea job recurrente mensual
}

// Paso 3: Cobro mensual (servidor — BullMQ job)
export async function chargeRecurringSEPA(
  customerId: string,
  paymentMethodId: string,
  amountEUR: number
) {
  return stripe.paymentIntents.create({
    amount: Math.round(amountEUR * 100),
    currency: 'eur',
    customer: customerId,
    payment_method: paymentMethodId,
    payment_method_types: ['sepa_debit'],
    confirm: true,
    off_session: true,
    metadata: { type: 'recurring_donation', source: 'sepa_debit' },
  })
}
```

### 5.6 Bancontact (Bélgica)

```typescript
export async function createBancontactPaymentIntent(amountEUR: number, donorEmail: string) {
  return stripe.paymentIntents.create({
    amount: Math.round(amountEUR * 100),
    currency: 'eur',
    payment_method_types: ['bancontact'],
    receipt_email: donorEmail,
  })
}

// Frontend: confirmBancontactPayment con return_url
stripe!.confirmBancontactPayment(clientSecret, {
  payment_method: { billing_details: { name: donorName, email: donorEmail } },
  return_url: `${window.location.origin}/donar/europa/gracias`,
})
```

### 5.7 Sofort / Klarna (Alemania, Austria, Países Bajos)

```typescript
// Sofort: transferencia bancaria instantánea
export async function createSofortPaymentIntent(amountEUR: number, donorEmail: string, country: 'DE' | 'AT' | 'NL') {
  return stripe.paymentIntents.create({
    amount: Math.round(amountEUR * 100),
    currency: 'eur',
    payment_method_types: ['sofort'],
    payment_method_data: {
      type: 'sofort',
      sofort: { country },
    },
    receipt_email: donorEmail,
  })
}

// Klarna: permite pagar en cuotas (útil para donaciones más grandes)
// Añadir 'klarna' a payment_method_types en PaymentIntent
```

### 5.8 SEPA Credit Transfer (donaciones grandes, empresas)

Para donaciones corporativas o grandes importes donde el donante hace una transferencia manual desde su banco.

```typescript
// Crear PaymentIntent con SEPA Credit Transfer
const intent = await stripe.paymentIntents.create({
  amount: Math.round(amountEUR * 100),
  currency: 'eur',
  payment_method_types: ['customer_balance'],
  payment_method_data: { type: 'customer_balance' },
  confirm: true,
  customer: stripeCustomerId,
})

// Stripe devuelve datos bancarios (IBAN virtual de Stripe) para que el donante haga la transferencia
// intent.next_action.display_bank_transfer_instructions.financial_addresses[0].iban
```

### 5.9 Webhook Stripe — Manejo Unificado

```typescript
// app/api/webhooks/stripe/route.ts
import { headers } from 'next/headers'

export async function POST(req: Request) {
  const body = await req.text()
  const sig = headers().get('stripe-signature')!

  let event: Stripe.Event
  try {
    event = stripe.webhooks.constructEvent(body, sig, process.env.STRIPE_WEBHOOK_SECRET!)
  } catch {
    return new Response('Webhook signature invalid', { status: 400 })
  }

  switch (event.type) {
    case 'payment_intent.succeeded':
      await handlePaymentSucceeded(event.data.object as Stripe.PaymentIntent)
      break
    case 'payment_intent.payment_failed':
      await handlePaymentFailed(event.data.object as Stripe.PaymentIntent)
      break
    case 'setup_intent.succeeded':
      // SEPA mandate guardado — activar donación recurrente
      await activateRecurringDonation(event.data.object as Stripe.SetupIntent)
      break
    case 'invoice.payment_succeeded':
      // Cobro mensual SEPA exitoso
      await recordRecurringDonation(event.data.object as Stripe.Invoice)
      break
    case 'charge.dispute.created':
      // Chargebacks — notificar al admin
      await notifyAdminOfDispute(event.data.object as Stripe.Dispute)
      break
  }

  return new Response('OK', { status: 200 })
}

async function handlePaymentSucceeded(intent: Stripe.PaymentIntent) {
  // Idempotencia: verificar si ya procesamos este intent
  const existing = await db.donation.findUnique({ where: { stripeIntentId: intent.id } })
  if (existing) return

  await db.donation.create({
    data: {
      stripeIntentId: intent.id,
      amountCents: intent.amount,
      currency: intent.currency.toUpperCase() as Currency,
      status: 'COMPLETED',
      paymentMethod: intent.payment_method_types[0].toUpperCase(),
      donorEmail: intent.metadata.donorEmail,
      anbiConsent: intent.metadata.anbi_consent === 'true',
    },
  })

  // Enviar recibo por email (con RSIN si anbiConsent = true)
  await sendDonationReceipt(intent)
}
```

### 5.10 Recibos ANBI (deducción fiscal Países Bajos)

Los donantes neerlandeses pueden deducir donaciones a organizaciones con estatus ANBI en su declaración de impuestos. El recibo debe incluir el número RSIN de la organización.

```typescript
// lib/email/donation-receipt.tsx
interface ANBIReceiptProps {
  donorName: string
  donorEmail: string
  amountEUR: number
  donationDate: Date
  donationId: string
  anbiRSIN: string // RSIN de la organización en NL, e.g. "123456789"
}

export function ANBIReceiptEmail({ donorName, amountEUR, donationDate, donationId, anbiRSIN }: ANBIReceiptProps) {
  return (
    <Html lang="nl">
      <Body>
        <Heading>Kwitantie donatie — Refugio Animal Paraguay</Heading>
        <Text>Geachte {donorName},</Text>
        <Text>Hartelijk dank voor uw donatie van €{amountEUR.toFixed(2)} op {formatDate(donationDate, 'nl')}.</Text>
        <Text><strong>RSIN: {anbiRSIN}</strong></Text>
        <Text>Deze kwitantie kunt u gebruiken voor uw belastingaangifte (giftenaftrek).</Text>
        <Text>Referentie: {donationId}</Text>
      </Body>
    </Html>
  )
}

// En handlePaymentSucceeded: si anbiConsent y currency === 'EUR' → enviar ANBI receipt en neerlandés
```

### 5.11 Variables de entorno Stripe

```env
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_ACCOUNT_COUNTRY=NL   # NL para procesar EUR/iDEAL; PY para PYG
```

---

## 6. PayPal

**Prioridad:** ALTA para donaciones europeas/internacionales
**Razón:** PayPal tiene ~50% penetración en NL y Alemania; muchos donantes europeos lo prefieren para donaciones a ONGs
**Flujo:** Donante tiene PayPal → 2 clicks → confirmación instantánea (sin ingresar datos bancarios)

### Integración

```typescript
// Usar @paypal/react-paypal-js (SDK oficial)
// app/donar/europa/page.tsx

import { PayPalScriptProvider, PayPalButtons } from '@paypal/react-paypal-js'

<PayPalScriptProvider options={{
  clientId: process.env.NEXT_PUBLIC_PAYPAL_CLIENT_ID!,
  currency: 'EUR',
  intent: 'capture',
  components: 'buttons',
}}>
  <PayPalButtons
    style={{ layout: 'vertical', color: 'gold', shape: 'rect', label: 'donate' }}
    createOrder={(data, actions) => {
      return actions.order.create({
        intent: 'CAPTURE',
        purchase_units: [{
          amount: { value: amountEUR.toFixed(2), currency_code: 'EUR' },
          description: `Donación — Refugio Animal Paraguay`,
        }],
      })
    }}
    onApprove={async (data, actions) => {
      const order = await actions.order!.capture()
      await fetch('/api/donations/paypal/confirm', {
        method: 'POST',
        body: JSON.stringify({ orderId: order.id, amount: amountEUR }),
      })
      router.push('/donar/europa/gracias')
    }}
  />
</PayPalScriptProvider>

// Suscripción mensual PayPal
<PayPalButtons
  createSubscription={(data, actions) => actions.subscription.create({
    plan_id: process.env.NEXT_PUBLIC_PAYPAL_MONTHLY_PLAN_ID!, // pre-crear en PayPal dashboard
  })}
  onApprove={(data) => {
    // data.subscriptionID → guardar en BD para seguimiento
  }}
/>
```

### Webhook PayPal (IPN / Webhooks API v2)

```typescript
// app/api/webhooks/paypal/route.ts
export async function POST(req: Request) {
  const body = await req.json()
  const webhookId = process.env.PAYPAL_WEBHOOK_ID!

  // Verificar autenticidad con PayPal SDK
  const isValid = await verifyPayPalWebhook(req.headers, body, webhookId)
  if (!isValid) return new Response('Invalid', { status: 400 })

  switch (body.event_type) {
    case 'PAYMENT.CAPTURE.COMPLETED':
      await recordPayPalDonation(body.resource)
      break
    case 'BILLING.SUBSCRIPTION.ACTIVATED':
      await activatePayPalSubscription(body.resource)
      break
    case 'BILLING.SUBSCRIPTION.CANCELLED':
      await cancelPayPalSubscription(body.resource.id)
      break
  }
  return new Response('OK')
}
```

### Variables de entorno PayPal

```env
NEXT_PUBLIC_PAYPAL_CLIENT_ID=AX...
PAYPAL_SECRET=EK...
PAYPAL_WEBHOOK_ID=WH-...
NEXT_PUBLIC_PAYPAL_MONTHLY_PLAN_ID=P-...
PAYPAL_MODE=live  # 'sandbox' para desarrollo
```

---

## 7. Donorbox — Plataforma de Crowdfunding ANBI

**Prioridad:** MEDIA-ALTA — habilita donaciones recurrentes europeas sin implementación custom
**Uso:** Widget embebido en `/donar/europa` ó campaña dedicada en Donorbox
**Ventaja:** ANBI-compatible (reconocido por Belastingdienst NL), acepta iDEAL, SEPA, tarjeta, PayPal en un solo widget
**Costo:** 1.5% por donación (mínimo — plan gratuito disponible)

### Integración (embed widget)

```html
<!-- En /donar/europa — versión en inglés/neerlandés -->
<script
  src="https://donorbox.org/widget.js"
  paypalExpress="false"
></script>
<iframe
  src="https://donorbox.org/embed/refugio-animal-paraguay-europa"
  name="donorbox"
  allowpaymentrequest="allowpaymentrequest"
  seamless="seamless"
  style="max-width: 500px; min-width: 310px; max-height: none !important"
  height="900px"
  width="100%"
/>
```

```typescript
// Alternativa: Redirect a campaña Donorbox desde nuestra página
// Pasar parámetros UTM para tracking en GA4
const donorboxUrl = new URL('https://donorbox.org/refugio-animal-paraguay-europa')
donorboxUrl.searchParams.set('utm_source', 'website')
donorboxUrl.searchParams.set('utm_medium', 'donate_button')
donorboxUrl.searchParams.set('amount', String(presetAmount))
```

### Webhook Donorbox → nuestra BD

```typescript
// app/api/webhooks/donorbox/route.ts
// Donorbox envía POST con Basic Auth
export async function POST(req: Request) {
  const authHeader = req.headers.get('authorization')
  const expected = Buffer.from(`${process.env.DONORBOX_WEBHOOK_USER}:${process.env.DONORBOX_WEBHOOK_PASS}`).toString('base64')
  if (authHeader !== `Basic ${expected}`) return new Response('Unauthorized', { status: 401 })

  const donation = await req.json()
  await db.donation.upsert({
    where: { externalId: `donorbox_${donation.donation.id}` },
    create: {
      externalId: `donorbox_${donation.donation.id}`,
      amountCents: Math.round(donation.donation.amount * 100),
      currency: donation.donation.currency.toUpperCase(),
      status: 'COMPLETED',
      paymentMethod: 'DONORBOX',
      donorEmail: donation.donor.email,
      donorName: `${donation.donor.first_name} ${donation.donor.last_name}`,
      recurring: donation.donation.recurring,
    },
    update: { status: 'COMPLETED' },
  })
}
```

### Variables de entorno Donorbox

```env
DONORBOX_CAMPAIGN_ID=refugio-animal-paraguay-europa
DONORBOX_WEBHOOK_USER=refugiopar
DONORBOX_WEBHOOK_PASS=...
```

---

## 8. Tikkie (Países Bajos — peer-to-peer)

**Prioridad:** BAJA-MEDIA — para campañas de fundraising viral en NL
**Uso:** La fundadora comparte un link Tikkie en grupos de WhatsApp/Instagram neerlandeses
**Límite:** Máximo €2,500 por Tikkie. Solo funciona con cuentas bancarias NL.
**No requiere integración técnica** — se usa directamente desde la app/web de Tikkie (ABN AMRO)

### Flujo operacional

```
1. Fundadora crea campaña en app.tikkie.me → genera link de pago
2. Comparte en WhatsApp/Instagram con texto + foto animal
3. Donante (banco NL) escanea/abre → paga con su app bancaria
4. Fondos llegan en minutos a cuenta ABN AMRO de la fundadora
5. Fundadora transfiere manualmente a cuenta del refugio cada semana
```

### Integración opcional (Tikkie API — ABN AMRO Business)

Para NGOs con cuenta ABN AMRO Business, hay una API REST para crear links programáticamente:

```typescript
// lib/payments/tikkie.ts
const TIKKIE_API_URL = 'https://api.abnamro.com/v2/tikkie/paymentrequests'

export async function createTikkieLink(
  amountEUR: number,
  description: string,
  expiryDate: Date
) {
  const response = await fetch(TIKKIE_API_URL, {
    method: 'POST',
    headers: {
      'API-Key': process.env.TIKKIE_API_KEY!,
      Authorization: `Bearer ${await getTikkieToken()}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      amountInCents: Math.round(amountEUR * 100),
      currency: 'EUR',
      description,
      expiryDate: expiryDate.toISOString().split('T')[0],
    }),
  })
  const data = await response.json()
  return data.url // https://tikkie.me/pay/...
}
```

---

## 6. Cloudinary

**Prioridad:** ALTA — necesario desde Fase 1

### Uso

| Recurso | Transformación | Entregado como |
|---------|---------------|----------------|
| Foto principal animal | 400×400, WebP, quality 80 | `f_webp,w_400,h_400,c_fill,q_80` |
| Galería animal | 800×600, WebP | `f_webp,w_800,h_600,c_fill,q_80` |
| Thumbnail catálogo | 200×200, WebP | `f_webp,w_200,h_200,c_fill,q_auto` |
| Lost & Found | 600×400, WebP | `f_webp,w_600,h_400,c_limit,q_80` |
| Contrato PDF | Sin transformación | CDN URL directo |

### Configuración

```typescript
import { v2 as cloudinary } from 'cloudinary'

cloudinary.config({
  cloud_name: process.env.CLOUDINARY_CLOUD_NAME,
  api_key: process.env.CLOUDINARY_API_KEY,
  api_secret: process.env.CLOUDINARY_API_SECRET,
  secure: true,
})

// Upload desde server action
export async function uploadAnimalPhoto(file: Buffer, animalId: string) {
  return cloudinary.uploader.upload_stream(
    { folder: `animals/${animalId}`, resource_type: 'image' },
    (error, result) => result
  )
}
```

**Límite free tier:** 25GB storage, 25GB bandwidth/mes — suficiente para MVP
**Paid tier:** $89/mes para plan Plus si se supera

---

## 7. Google Maps Platform

**Prioridad:** MEDIA — necesario para Lost & Found (Fase 3)

### APIs usadas

| API | Uso |
|-----|-----|
| Maps JavaScript API | Mapa de reportes Lost & Found |
| Geocoding API | Convertir dirección textual → coordenadas |
| Places API (Autocomplete) | Campo de dirección en formularios |

```typescript
// Componente de mapa con React
import { APIProvider, Map, AdvancedMarker } from '@vis.gl/react-google-maps'

<APIProvider apiKey={process.env.NEXT_PUBLIC_GOOGLE_MAPS_KEY}>
  <Map
    defaultCenter={{ lat: -25.2867, lng: -57.6470 }} // Asunción
    defaultZoom={12}
    mapId="lost-found-map"
  >
    {reports.map(r => (
      <AdvancedMarker key={r.id} position={{ lat: r.lat, lng: r.lng }} />
    ))}
  </Map>
</APIProvider>
```

**Variables de entorno:**
```env
NEXT_PUBLIC_GOOGLE_MAPS_KEY=AIza...
GOOGLE_MAPS_SERVER_KEY=AIza...  # Para geocoding server-side
```

**Costo estimado:** $0 hasta 28,000 cargas de mapa/mes (free tier). Para Lost & Found en MVP: ~$5–15/mes.

---

## 8. Google Analytics 4

**Prioridad:** ALTA desde Fase 1 (medir conversiones)

```typescript
// Usando @next/third-parties (recomendado - no bloquea render)
import { GoogleAnalytics } from '@next/third-parties/google'

// En layout.tsx
<GoogleAnalytics gaId={process.env.NEXT_PUBLIC_GA4_ID} />

// Evento custom: adopción completada
import { sendGAEvent } from '@next/third-parties/google'
sendGAEvent('event', 'adoption_completed', { animal_id: id, species: 'PERRO' })
```

### Eventos a trackear

| Evento | Trigger |
|--------|---------|
| `catalog_filter_used` | Usuario aplica filtro en catálogo |
| `animal_profile_viewed` | Usuario abre perfil de animal |
| `adoption_form_started` | Paso 1 del formulario |
| `adoption_form_completed` | Formulario enviado |
| `donation_initiated` | Llega a página de pago |
| `donation_completed` | Pago confirmado |
| `lost_found_report_submitted` | Formulario enviado |
| `whatsapp_button_clicked` | Click en botón flotante |

---

## 9. Facebook Pixel

**Prioridad:** MEDIA (para campañas de Facebook Ads en Fase 3+)

```typescript
import { FacebookPixel } from '@next/third-parties/facebook'
<FacebookPixel id={process.env.NEXT_PUBLIC_FB_PIXEL_ID} />
```

Eventos a trackear: `ViewContent` (animal profile), `Lead` (formulario adopción enviado), `Donate` (donación completada).

---

## 10. Resend (Email Transaccional)

**Prioridad:** MEDIA — complementa WhatsApp

```typescript
import { Resend } from 'resend'
const resend = new Resend(process.env.RESEND_API_KEY)

await resend.emails.send({
  from: 'Refugio Animal Paraguay <hola@refugiopar.org>',
  to: applicant.email,
  subject: 'Tu solicitud de adopción fue recibida',
  react: <AdoptionConfirmationEmail applicant={applicant} animal={animal} />,
})
```

**Free tier:** 3,000 emails/mes — suficiente para MVP
**Templates:** React Email para templates type-safe

---

## Tabla Resumen de Variables de Entorno

```env
# WhatsApp Business
WA_PHONE_NUMBER_ID=
WA_ACCESS_TOKEN=
WA_WEBHOOK_VERIFY_TOKEN=

# Pagos locales Paraguay
TIGO_API_URL=
TIGO_MERCHANT_ID=
TIGO_API_KEY=
TIGO_WEBHOOK_SECRET=

# Stripe (internacional + europeo)
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_ACCOUNT_COUNTRY=NL

# PayPal (europeo)
NEXT_PUBLIC_PAYPAL_CLIENT_ID=
PAYPAL_SECRET=
PAYPAL_WEBHOOK_ID=
NEXT_PUBLIC_PAYPAL_MONTHLY_PLAN_ID=
PAYPAL_MODE=live

# Donorbox (crowdfunding ANBI)
DONORBOX_CAMPAIGN_ID=
DONORBOX_WEBHOOK_USER=
DONORBOX_WEBHOOK_PASS=

# Tikkie (opcional, NL peer-to-peer)
TIKKIE_API_KEY=

# ANBI (organización neerlandesa)
ANBI_RSIN=                    # Número RSIN para recibos fiscales NL

# Cloudinary
CLOUDINARY_CLOUD_NAME=
CLOUDINARY_API_KEY=
CLOUDINARY_API_SECRET=

# Google
NEXT_PUBLIC_GOOGLE_MAPS_KEY=
GOOGLE_MAPS_SERVER_KEY=
NEXT_PUBLIC_GA4_ID=

# Facebook
NEXT_PUBLIC_FB_PIXEL_ID=

# Email (Resend)
RESEND_API_KEY=

# Auth
NEXTAUTH_SECRET=
NEXTAUTH_URL=

# Database
DATABASE_URL=
REDIS_URL=
```

---

## Resumen de Métodos de Pago por Región

| Método | Región | Proveedor | Tipo | Moneda | Fase |
|--------|--------|-----------|------|--------|------|
| Tigo Money | Paraguay | Tigo API | Wallet móvil | PYG | 3 |
| Personal Pay | Paraguay | Personal API | Wallet móvil | PYG | 3 |
| PagoExpress | Paraguay (rural) | PagoExpress API | Kiosco físico | PYG | 3 |
| Tarjeta (Visa/MC) | Internacional | Stripe | Tarjeta | USD/EUR | 3 |
| Google Pay / Apple Pay | Internacional | Stripe | Digital wallet | USD/EUR | 3 |
| Stripe Link | Internacional | Stripe | Saved cards | USD/EUR | 3 |
| iDEAL | Países Bajos | Stripe | Banco online | EUR | 4 |
| SEPA Direct Debit | Zona SEPA (36 países) | Stripe | Débito bancario | EUR | 4 |
| SEPA Credit Transfer | Zona SEPA (empresas) | Stripe | Transferencia | EUR | 4 |
| Bancontact | Bélgica | Stripe | Banco online | EUR | 4 |
| Sofort | DE/AT/NL | Stripe | Banco online | EUR | 4 |
| Klarna | DE/AT/NL/SE | Stripe | BNPL/cuotas | EUR | 4 |
| PayPal | Europa (NL/DE/FR) | PayPal SDK | Digital wallet | EUR | 4 |
| Donorbox widget | Global (ANBI-NL) | Donorbox | Crowdfunding | EUR/USD | 4 |
| Tikkie | Países Bajos | ABN AMRO | P2P link | EUR | 4 |
