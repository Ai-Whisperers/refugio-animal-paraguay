# Principios de UX y Diseño — Refugio Animal Paraguay

---

## Principios Fundamentales

### 1. Mobile-First, Always

El 90% de los usuarios accede desde celular. No es "responsive design" como afterthought — es diseñar para el celular primero y adaptar para escritorio.

**Reglas:**
- Tamaño mínimo de tap target: 44×44px (Apple HIG) / 48×48px (Material)
- Texto mínimo legible: 16px (evitar scroll horizontal, zoom involuntario)
- Formularios: teclado numérico para teléfonos (`inputMode="tel"`), email (`inputMode="email"`)
- Botones de acción principales al alcance del pulgar (zona inferior de la pantalla)
- Gestos de scroll vertical: no implementar scroll horizontal para contenido principal

### 2. WhatsApp-First para Comunicación

WhatsApp es la expectativa del usuario paraguayo. El email es secundario.

**Reglas:**
- Botón flotante de WhatsApp Business visible en **todas** las páginas
- Las confirmaciones críticas (solicitud recibida, estado actualizado) van **primero** por WhatsApp
- OTP de login: WhatsApp por defecto, email como alternativa
- Los templates de mensajes deben sonar humanos, no corporativos

### 3. Conexión Inestable como Caso Base

Diseñar para 3G con caídas intermitentes, no para fibra óptica.

**Reglas:**
- Formularios guardan progreso localmente (`localStorage`) — no perder datos al perder señal
- Imágenes: skeleton placeholders mientras cargan, no espacios en blanco
- Acciones críticas (enviar formulario) con feedback inmediato optimista + confirmación real
- Catálogo de animales disponible offline vía Service Worker (PWA)
- Indicadores de estado de red para acciones que requieren conexión

### 4. Confianza antes que Conversión

Los usuarios paraguayos desconfían de organizaciones digitales que no conocen. La confianza se gana antes de pedirle que rellene un formulario largo.

**Orden de información en el homepage:**
1. Fotos reales del refugio y animales (no stock photos)
2. Número de animales adoptados (social proof)
3. Equipo real con nombres y fotos
4. Dirección física y horarios (anclaje en lo real)
5. CTA de adopción

**Reglas:**
- Nunca stock photos — siempre fotos reales del refugio
- Testimonios de adoptantes con nombre y foto real (con permiso)
- Información de contacto visible en header y footer
- Mostrar número de registro del refugio si existe

### 5. Lenguaje Humano y Cálido

El refugio cuida animales — el tono debe reflejar esa calidez. No burocrático, no clínico.

**Ejemplos de tono:**

| ❌ No | ✅ Sí |
|-------|-------|
| "Solicitud enviada con éxito" | "¡Tu solicitud llegó! Te confirmamos por WhatsApp en minutos." |
| "Complete todos los campos requeridos" | "Faltó completar algunos datos — los marcamos en rojo" |
| "Error 400: Bad Request" | "Algo salió mal al enviar. ¿Podés intentar de nuevo?" |
| "Animal ID: 0042 — Canino" | "Luna, 2 años — Perrita mestiza que adora los mimos" |
| "Proceso de adopción iniciado" | "¡Estás un paso más cerca de conocer a Max!" |

**Palabras a usar:** mimos, amiguito, familia, hogar, amor, cuidado
**Palabras a evitar:** mascota (usar "animal de compañía" o el nombre del animal), procesado, usuario

---

## Sistema de Diseño

### Paleta de Colores

```css
/* Primarios */
--color-primary:      #E8622A;  /* Naranja cálido — energía, esperanza */
--color-primary-dark: #C44D1A;
--color-primary-light:#F5935A;

/* Secundarios */
--color-secondary:    #2A7E62;  /* Verde — naturaleza, bienestar */
--color-secondary-dark: #1A5E47;

/* Neutros */
--color-bg:           #FAFAF8;  /* Blanco cálido — no frío */
--color-surface:      #FFFFFF;
--color-border:       #E5E5E0;
--color-text-primary: #1A1A18;
--color-text-secondary: #6B6B63;
--color-text-muted:   #9B9B92;

/* Estados */
--color-success:      #2A7E62;
--color-warning:      #E8922A;
--color-error:        #D93025;
--color-urgent:       #D93025;  /* Rojo para animales urgentes */
--color-available:    #2A7E62;  /* Verde para disponibles */
--color-pending:      #E8922A;  /* Naranja para pendientes */
```

### Tipografía

```css
/* Fuente principal */
font-family: 'Inter', system-ui, -apple-system, sans-serif;

/* Escala de tamaños (mobile-first) */
--text-xs:   12px / 16px
--text-sm:   14px / 20px
--text-base: 16px / 24px  /* Mínimo para cuerpo de texto */
--text-lg:   18px / 28px
--text-xl:   20px / 30px
--text-2xl:  24px / 32px
--text-3xl:  30px / 38px  /* Títulos de sección */
--text-4xl:  36px / 44px  /* Headline homepage */

/* Pesos */
--font-regular: 400
--font-medium:  500
--font-semibold: 600
--font-bold:    700
```

### Espaciado

Sistema de 4px base (Tailwind por defecto):
- `space-1` = 4px, `space-2` = 8px, `space-4` = 16px, `space-6` = 24px, `space-8` = 32px

Padding de página en móvil: `px-4` (16px)
Padding de página en tablet: `px-6` (24px)
Ancho máximo de contenido: `max-w-6xl` (1152px)

---

## Componentes Clave

### Card de Animal (Catálogo)

```
┌─────────────────────────┐
│  [Foto 4:3, lazy-load]  │
│  ● DISPONIBLE  ⚠️ URGENTE│  ← Badge superpuesto
├─────────────────────────┤
│  Luna                   │  ← Nombre grande
│  Perrita · 2 años · Med │  ← Especie, edad, tamaño
│  ❤️ 👶 🐕              │  ← Buena con: adultos, niños, perros
│                         │
│  [Conocer a Luna →]     │  ← CTA primario, full-width en móvil
└─────────────────────────┘
```

**Interacciones:**
- Tap en foto → Ampliar galería (swipe para pasar)
- Tap en ❤️ (favorito) → Guardar en lista (sin login para verla, login para persistir)
- Tap en card → Abrir perfil completo

### Formulario Multi-paso (Adopción)

**Principio:** Un concepto por paso, barra de progreso visible.

```
[━━━━━━━━░░░░░░░] Paso 2 de 5

  ¿Cómo es tu hogar?

  ○ Casa con jardín
  ○ Apartamento
  ○ Campo / zona rural

  ¿Tu jardín está cercado?
  ○ Sí, completamente  ○ Parcialmente  ○ No tengo jardín

  [← Anterior]          [Siguiente →]
```

**Reglas:**
- Guardar estado en `localStorage` entre pasos
- Validación en tiempo real (no solo al submit)
- Mensajes de error debajo del campo, en rojo suave
- El paso activo nunca tiene más de 5-6 preguntas
- "Anterior" siempre disponible y guarda los datos del paso actual

### Panel Admin (Tablet-Friendly)

```
┌──────────────────────────────────────────┐
│ Solicitudes Pendientes (8)               │
├──────────────────────────────────────────┤
│ 🟡 Lorena García — Luna (Perrita)        │
│    Recibida hace 2 horas                 │
│    [Ver detalle] [Aprobar] [Rechazar]    │
├──────────────────────────────────────────┤
│ 🟡 Carlos Martínez — Tobby (Perro)      │
│    Recibida hace 5 horas                 │
│    [Ver detalle] [Aprobar] [Rechazar]    │
└──────────────────────────────────────────┘
```

**Reglas:**
- Botones de acción rápida directamente en la lista (no solo en detalle)
- Botones grandes (mínimo 48px altura) para uso con dedos en tablet
- Color coding: 🟡 pendiente, 🟢 aprobada, 🔴 rechazada

---

## Patrones de Accesibilidad

### Mínimos No Negociables

- Contraste de texto: mínimo 4.5:1 (WCAG AA) — 7:1 para texto pequeño
- Todos los inputs con label visible (no solo placeholder)
- Imágenes con alt text descriptivo para lectores de pantalla
- Navegación por teclado funcional en formularios y modals
- `role` y `aria-*` en componentes interactivos custom (sliders, modals)
- `lang="es-PY"` en el HTML raíz

### Skip Links

```html
<a href="#main-content" class="sr-only focus:not-sr-only">
  Saltar al contenido principal
</a>
```

### Formularios

```html
<!-- Siempre asociar label con input -->
<label for="phone">Número de WhatsApp</label>
<input id="phone" name="phone" type="tel" inputMode="tel"
  aria-describedby="phone-hint phone-error"
  aria-invalid={hasError} />
<span id="phone-hint">Ej: 0981 123 456</span>
<span id="phone-error" role="alert">{error}</span>
```

---

## Performance como UX

| Métrica | Target | Por qué importa para UX |
|---------|--------|------------------------|
| LCP | <2.5s | Primera foto de animal visible |
| INP | <200ms | Filtros del catálogo responden rápido |
| CLS | <0.1 | Las cards no "saltan" al cargar fotos |
| TTFB | <800ms | Percepción de carga inmediata |
| Bundle JS | <100KB inicial | Carga rápida en 4G Paraguay |

**Técnicas:**
- Foto del animal con `priority` en la hero de cada perfil
- `sizes` attribute en todas las imágenes del catálogo
- Skeleton loaders para cards durante fetch
- Prefetch al hover sobre links de navegación frecuente

---

## Flujos Críticos — Tiempo Objetivo

| Flujo | Objetivo | Medición |
|-------|---------|---------|
| Ver catálogo y encontrar un animal | <60 segundos | Tiempo hasta primer click en perfil |
| Completar formulario de adopción | <8 minutos | Desde step 1 hasta submit |
| Donar (Tigo Money) | <3 minutos | Desde página de donación hasta confirmación |
| Reportar animal perdido | <5 minutos | Formulario + foto + ubicación |
| Admin: actualizar estado de solicitud | <30 segundos | Login hasta click en "Aprobar" |
